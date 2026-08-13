"""End-to-end checks for the tap's streams."""

from __future__ import annotations

import json

import pytest
import requests
from singer_sdk.exceptions import ConfigValidationError

from tap_talon_one.streams import TalonOnePaginator
from tap_talon_one.tap import TalonOneTap


def config() -> dict[str, object]:
    """Return non-production test configuration."""
    return {
        "api_url": "https://example.talon.one",
        "management_key": "secret",
        "application_id": 42,
        "page_size": 2,
        "start_date": "2026-07-01T00:00:00Z",
        "lookback_minutes": 5,
    }


def mock_all_stream_endpoints(requests_mock) -> None:
    """Register empty responses for every stream so sync_all can run.

    Register these first; a test's own matcher for the same URL takes
    precedence because requests_mock evaluates matchers newest-first.
    """
    base = "https://example.talon.one/v1/applications/42"
    requests_mock.get(base, json={"id": 42})
    requests_mock.get(f"{base}/events/no_total", json={"data": [], "hasMore": False})
    for suffix in ("campaigns", "cart_item_filters", "event_types"):
        requests_mock.get(f"{base}/{suffix}", json={"data": [], "hasMore": False})


def emitted_records(capsys, stream: str) -> list[dict[str, object]]:
    """Return RECORD payloads for one stream from captured Singer output."""
    messages = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    return [
        message["record"]
        for message in messages
        if message["type"] == "RECORD" and message["stream"] == stream
    ]


def test_campaigns_sync_retries_and_preserves_paging(
    requests_mock, capsys, monkeypatch
) -> None:
    """Emit nested records after a Retry-After response and two stable pages."""
    url = "https://example.talon.one/v1/applications/42/campaigns"
    mock_all_stream_endpoints(requests_mock)
    requests_mock.get(
        url,
        [
            {"status_code": 429, "headers": {"Retry-After": "7"}},
            {
                "json": {
                    "data": [
                        {
                            "id": 1,
                            "name": "One",
                            "referralSettings": {"nested": True},
                        },
                        {"id": 2, "name": "Two"},
                    ],
                    "hasMore": True,
                }
            },
            {"json": {"data": [{"id": 3, "name": "Three"}], "hasMore": False}},
        ],
    )
    waits: list[float] = []
    monkeypatch.setattr("time.sleep", waits.append)

    TalonOneTap(config=config()).sync_all()

    requests_seen = [
        request
        for request in requests_mock.request_history
        if request.path.endswith("/campaigns")
    ]
    assert len(requests_seen) == 3
    assert requests_seen[0].headers["Authorization"] == "ManagementKey-v1 secret"
    assert [request.qs["skip"] for request in requests_seen] == [["0"], ["0"], ["2"]]
    assert all(request.qs["pagesize"] == ["2"] for request in requests_seen)
    assert all(request.qs["sort"] == ["id"] for request in requests_seen)
    assert waits == [7.0]

    assert emitted_records(capsys, "campaigns") == [
        {"id": 1, "name": "One", "referralSettings": {"nested": True}},
        {"id": 2, "name": "Two"},
        {"id": 3, "name": "Three"},
    ]


def test_paginator_stops_on_empty_data() -> None:
    """Avoid another request after an empty response page."""
    response = requests.Response()
    response._content = b'{"data": [], "hasMore": true}'
    paginator = TalonOnePaginator(start_value=0, page_size=2)

    assert paginator.has_more(response) is False


def test_paginator_rejects_invalid_data() -> None:
    """Fail before paginating an invalid Talon.One envelope."""
    response = requests.Response()
    response._content = b'{"data": "not-a-list"}'
    paginator = TalonOnePaginator(start_value=0, page_size=2)

    with pytest.raises(ValueError, match="data must be a list"):
        paginator.has_more(response)


def test_config_rejects_plaintext_api_url() -> None:
    """Never send a management key over plaintext HTTP."""
    plaintext_config = config() | {"api_url": "http://example.talon.one"}

    with pytest.raises(ConfigValidationError):
        TalonOneTap(config=plaintext_config)


@pytest.mark.parametrize(
    ("override", "invalid_value"),
    [("start_date", "not-a-date"), ("lookback_minutes", -1)],
)
def test_config_rejects_invalid_incremental_settings(
    override: str, invalid_value: object
) -> None:
    """Reject unsafe incremental boundaries before making requests."""
    with pytest.raises(ConfigValidationError):
        TalonOneTap(config=config() | {override: invalid_value})


def test_discovery_uses_static_schemas_and_keys() -> None:
    """Discover every static schema without making a source request."""
    streams = {
        stream.name: stream
        for stream in TalonOneTap(config=config()).discover_streams()
    }

    assert set(streams) == {
        "application",
        "campaigns",
        "cart_item_filters",
        "events",
        "event_types",
    }
    assert streams["event_types"].primary_keys == ("name",)
    for name in sorted(set(streams) - {"event_types"}):
        assert streams[name].primary_keys == ("id",)
    for name in sorted(set(streams) - {"events"}):
        assert streams[name].replication_method == "FULL_TABLE"
    assert streams["events"].replication_key == "created"
    assert (
        "object"
        in streams["campaigns"].schema["properties"]["referralSettings"]["type"]
    )
    assert "object" in streams["events"].schema["properties"]["attributes"]["type"]
    assert (
        "object"
        in streams["application"].schema["properties"]["attributesSettings"]["type"]
    )


@pytest.mark.parametrize(
    ("state", "start_date", "expected_created_after"),
    [
        (None, "2026-07-01T00:00:00Z", "2026-07-01T00:00:00+00:00"),
        (
            {
                "bookmarks": {
                    "events": {
                        "replication_key": "created",
                        "replication_key_value": "2026-07-10T10:00:00Z",
                    }
                }
            },
            None,
            "2026-07-10T09:55:00+00:00",
        ),
        (
            {
                "bookmarks": {
                    "events": {
                        "replication_key": "created",
                        "replication_key_value": "2026-07-10T10:00:00Z",
                    }
                }
            },
            "2026-07-11T00:00:00Z",
            "2026-07-10T09:55:00+00:00",
        ),
    ],
)
def test_events_sync_uses_stable_incremental_window_and_max_bookmark(
    requests_mock, capsys, state, start_date, expected_created_after
) -> None:
    """Reuse one boundary across pages and advance state to the newest event."""
    mock_all_stream_endpoints(requests_mock)
    requests_mock.get(
        "https://example.talon.one/v1/applications/42/events/no_total",
        [
            {
                "json": {
                    "data": [
                        {
                            "id": 1,
                            "created": "2026-07-10T10:01:00Z",
                            "attributes": {"source": {"nested": True}},
                        },
                        {"id": 2, "created": "2026-07-10T10:02:00Z"},
                    ],
                    "hasMore": True,
                }
            },
            {
                "json": {
                    "data": [],
                    "hasMore": True,
                }
            },
        ],
    )

    tap_config = config()
    if start_date is None:
        tap_config.pop("start_date")
    else:
        tap_config["start_date"] = start_date

    TalonOneTap(config=tap_config, state=state).sync_all()

    event_requests = [
        request
        for request in requests_mock.request_history
        if request.path.endswith("/events/no_total")
    ]
    assert [request.qs["skip"] for request in event_requests] == [["0"], ["2"]]
    assert [request.qs["createdafter"] for request in event_requests] == [
        [expected_created_after.lower()],
        [expected_created_after.lower()],
    ]
    assert all(request.qs["sort"] == ["created"] for request in event_requests)

    messages = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    records = [
        message["record"]
        for message in messages
        if message["type"] == "RECORD" and message["stream"] == "events"
    ]
    assert records[0]["attributes"] == {"source": {"nested": True}}
    assert messages[-1]["value"]["bookmarks"]["events"]["replication_key_value"] == (
        "2026-07-10T10:02:00Z"
    )


def test_application_syncs_single_object_without_paging(requests_mock, capsys) -> None:
    """Emit the Application singleton from one unpaginated, parameterless request."""
    mock_all_stream_endpoints(requests_mock)
    requests_mock.get(
        "https://example.talon.one/v1/applications/42",
        json={"id": 42, "name": "Dev", "loyaltyPrograms": [{"id": 9}]},
    )

    TalonOneTap(config=config()).sync_all()

    requests_seen = [
        request
        for request in requests_mock.request_history
        if request.path == "/v1/applications/42"
    ]
    assert len(requests_seen) == 1
    assert requests_seen[0].qs == {}
    assert requests_seen[0].headers["Authorization"] == "ManagementKey-v1 secret"

    assert emitted_records(capsys, "application") == [
        {"id": 42, "name": "Dev", "loyaltyPrograms": [{"id": 9}]}
    ]


def test_event_types_wraps_string_rows_and_omits_sort(requests_mock, capsys) -> None:
    """Wrap plain string event types as records and page without a sort parameter."""
    mock_all_stream_endpoints(requests_mock)
    requests_mock.get(
        "https://example.talon.one/v1/applications/42/event_types",
        [
            {"json": {"data": ["session_created", "purchase"], "totalResultSize": 3}},
            {"json": {"data": ["refund"], "totalResultSize": 3}},
        ],
    )

    TalonOneTap(config=config()).sync_all()

    requests_seen = [
        request
        for request in requests_mock.request_history
        if request.path == "/v1/applications/42/event_types"
    ]
    assert [request.qs["skip"] for request in requests_seen] == [["0"], ["2"]]
    assert all("sort" not in request.qs for request in requests_seen)

    assert emitted_records(capsys, "event_types") == [
        {"name": "session_created"},
        {"name": "purchase"},
        {"name": "refund"},
    ]


def test_cart_item_filters_cap_page_size_and_omit_sort(requests_mock, capsys) -> None:
    """Cap requests and paginator advancement at the endpoint's pageSize limit."""
    mock_all_stream_endpoints(requests_mock)
    first_page = [{"id": index} for index in range(50)]
    requests_mock.get(
        "https://example.talon.one/v1/applications/42/cart_item_filters",
        [
            {"json": {"data": first_page, "hasMore": True}},
            {"json": {"data": [{"id": 50}], "hasMore": False}},
        ],
    )

    TalonOneTap(config=config() | {"page_size": 1000}).sync_all()

    requests_seen = [
        request
        for request in requests_mock.request_history
        if request.path == "/v1/applications/42/cart_item_filters"
    ]
    assert [request.qs["skip"] for request in requests_seen] == [["0"], ["50"]]
    assert all(request.qs["pagesize"] == ["50"] for request in requests_seen)
    assert all("sort" not in request.qs for request in requests_seen)

    assert len(emitted_records(capsys, "cart_item_filters")) == 51
