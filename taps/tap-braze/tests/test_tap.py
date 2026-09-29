"""End-to-end checks for the tap's streams."""

from __future__ import annotations

import json

import pytest
import requests
from singer_sdk.exceptions import ConfigValidationError

from tap_braze.streams import BrazeListPaginator
from tap_braze.tap import BrazeTap

BASE = "https://rest.example.braze.com"


def config() -> dict[str, object]:
    """Return non-production test configuration."""
    return {"api_url": BASE, "api_key": "secret"}


def mock_all_stream_endpoints(requests_mock) -> None:
    """Register empty responses for every endpoint so sync_all can run.

    Register these first; a test's own matcher for the same URL takes
    precedence because requests_mock evaluates matchers newest-first.
    """
    requests_mock.get(f"{BASE}/campaigns/list", json={"campaigns": []})
    requests_mock.get(f"{BASE}/canvas/list", json={"canvases": []})
    requests_mock.get(f"{BASE}/campaigns/details", json={"message": "success"})
    requests_mock.get(f"{BASE}/canvas/details", json={"message": "success"})


def emitted_records(capsys, stream: str) -> list[dict[str, object]]:
    """Return RECORD payloads for one stream from captured Singer output."""
    messages = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    return [
        message["record"]
        for message in messages
        if message["type"] == "RECORD" and message["stream"] == stream
    ]


def requests_to(requests_mock, suffix: str) -> list[object]:
    """Return the captured requests whose path ends with ``suffix``."""
    return [
        request
        for request in requests_mock.request_history
        if request.path.endswith(suffix)
    ]


def test_discovery_uses_static_schemas_and_wires_parent_child() -> None:
    """Discover every static schema and the details parent-child links."""
    streams = {
        stream.name: stream for stream in BrazeTap(config=config()).discover_streams()
    }

    assert set(streams) == {
        "campaigns",
        "canvases",
        "campaign_details",
        "canvas_details",
    }
    for name in streams:
        assert streams[name].replication_method == "FULL_TABLE"
    assert streams["campaigns"].primary_keys == ("id",)
    assert streams["canvases"].primary_keys == ("id",)
    assert streams["campaign_details"].primary_keys == ("campaign_id",)
    assert streams["canvas_details"].primary_keys == ("canvas_id",)
    assert streams["campaign_details"].parent_stream_type.name == "campaigns"
    assert streams["canvas_details"].parent_stream_type.name == "canvases"
    assert (
        "object" in streams["campaign_details"].schema["properties"]["messages"]["type"]
    )
    assert "array" in streams["canvas_details"].schema["properties"]["steps"]["type"]


def test_config_rejects_plaintext_api_url() -> None:
    """Never send a bearer token over plaintext HTTP."""
    with pytest.raises(ConfigValidationError):
        BrazeTap(config=config() | {"api_url": "http://rest.example.braze.com"})


def test_config_requires_api_key() -> None:
    """Reject configuration missing the REST API key."""
    with pytest.raises(ConfigValidationError):
        BrazeTap(config={"api_url": BASE})


def test_paginator_stops_on_empty_data() -> None:
    """Avoid another request after an empty list page."""
    response = requests.Response()
    response._content = b'{"campaigns": []}'
    paginator = BrazeListPaginator(start_value=0, records_key="campaigns")

    assert paginator.has_more(response) is False


def test_paginator_rejects_invalid_data() -> None:
    """Fail before paginating an invalid Braze envelope."""
    response = requests.Response()
    response._content = b'{"campaigns": "not-a-list"}'
    paginator = BrazeListPaginator(start_value=0, records_key="campaigns")

    with pytest.raises(ValueError, match="campaigns must be a list"):
        paginator.has_more(response)


def test_campaigns_list_paginates_and_authenticates(requests_mock, capsys) -> None:
    """Page through campaigns with the bearer token until the empty page."""
    mock_all_stream_endpoints(requests_mock)
    requests_mock.get(
        f"{BASE}/campaigns/list",
        [
            {"json": {"campaigns": [{"id": "1", "name": "One"}, {"id": "2"}]}},
            {"json": {"campaigns": []}},
        ],
    )

    BrazeTap(config=config()).sync_all()

    list_requests = requests_to(requests_mock, "/campaigns/list")
    assert [request.qs["page"] for request in list_requests] == [["0"], ["1"]]
    assert all(
        request.headers["Authorization"] == "Bearer secret" for request in list_requests
    )
    assert emitted_records(capsys, "campaigns") == [
        {"id": "1", "name": "One"},
        {"id": "2"},
    ]


def test_campaign_details_fans_out_one_call_per_parent_id(
    requests_mock, capsys
) -> None:
    """Issue exactly one campaign_details call per campaign id from the list."""
    mock_all_stream_endpoints(requests_mock)
    requests_mock.get(
        f"{BASE}/campaigns/list",
        [
            {"json": {"campaigns": [{"id": "c1"}, {"id": "c2"}, {"id": "c3"}]}},
            {"json": {"campaigns": []}},
        ],
    )
    requests_mock.get(
        f"{BASE}/campaigns/details",
        json={
            "message": "success",
            "name": "Detailed",
            "channels": ["email"],
            "messages": {"mv1": {"channel": "email", "subject": "Hi"}},
        },
    )

    BrazeTap(config=config()).sync_all()

    detail_requests = requests_to(requests_mock, "/campaigns/details")
    assert sorted(request.qs["campaign_id"][0] for request in detail_requests) == [
        "c1",
        "c2",
        "c3",
    ]
    assert len(detail_requests) == 3

    records = emitted_records(capsys, "campaign_details")
    assert sorted(record["campaign_id"] for record in records) == ["c1", "c2", "c3"]
    for record in records:
        assert "message" not in record
        assert record["name"] == "Detailed"
        assert record["messages"] == {"mv1": {"channel": "email", "subject": "Hi"}}


def test_canvas_details_fans_out_one_call_per_parent_id(requests_mock, capsys) -> None:
    """Issue exactly one canvas_details call per canvas id from the list."""
    mock_all_stream_endpoints(requests_mock)
    requests_mock.get(
        f"{BASE}/canvas/list",
        [
            {"json": {"canvases": [{"id": "v1"}, {"id": "v2"}]}},
            {"json": {"canvases": []}},
        ],
    )
    requests_mock.get(
        f"{BASE}/canvas/details",
        json={"message": "success", "name": "Flow", "steps": [{"id": "s1"}]},
    )

    BrazeTap(config=config()).sync_all()

    detail_requests = requests_to(requests_mock, "/canvas/details")
    assert sorted(request.qs["canvas_id"][0] for request in detail_requests) == [
        "v1",
        "v2",
    ]

    records = emitted_records(capsys, "canvas_details")
    assert sorted(record["canvas_id"] for record in records) == ["v1", "v2"]
    for record in records:
        assert "message" not in record
        assert record["steps"] == [{"id": "s1"}]


def test_details_retries_on_rate_limit(requests_mock, monkeypatch) -> None:
    """Honour a Retry-After response before the details call succeeds."""
    mock_all_stream_endpoints(requests_mock)
    requests_mock.get(
        f"{BASE}/campaigns/list",
        [
            {"json": {"campaigns": [{"id": "c1"}]}},
            {"json": {"campaigns": []}},
        ],
    )
    requests_mock.get(
        f"{BASE}/campaigns/details",
        [
            {"status_code": 429, "headers": {"Retry-After": "9"}},
            {"json": {"message": "success", "name": "Detailed"}},
        ],
    )
    waits: list[float] = []
    monkeypatch.setattr("time.sleep", waits.append)

    BrazeTap(config=config()).sync_all()

    assert waits == [9.0]
