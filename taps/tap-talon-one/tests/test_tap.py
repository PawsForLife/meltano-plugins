"""End-to-end checks for the campaigns stream."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
import requests
from singer_sdk.exceptions import ConfigValidationError

from tap_talon_one import streams
from tap_talon_one.streams import ExportEffectsStream, TalonOnePaginator
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
        "effects_window_minutes": 60,
    }


def test_campaigns_sync_retries_and_preserves_paging(
    requests_mock, capsys, monkeypatch
) -> None:
    """Emit nested records after a Retry-After response and two stable pages."""
    url = "https://example.talon.one/v1/applications/42/campaigns"
    requests_mock.get(
        "https://example.talon.one/v1/applications/42/events/no_total",
        json={"data": [], "hasMore": False},
    )
    requests_mock.get(
        "https://example.talon.one/v1/applications/42/export_effects",
        text="",
    )
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

    messages = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    records = [message["record"] for message in messages if message["type"] == "RECORD"]
    assert records == [
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


def test_discovery_uses_static_schema_and_id_key() -> None:
    """Discover every static schema without making a source request."""
    campaigns, events, effects = TalonOneTap(config=config()).discover_streams()

    assert campaigns.primary_keys == events.primary_keys == ("id",)
    assert "object" in campaigns.schema["properties"]["referralSettings"]["type"]
    assert events.replication_key == "created"
    assert "object" in events.schema["properties"]["attributes"]["type"]
    assert effects.name == "export_effects"
    assert effects.primary_keys == ()
    assert effects.replication_method == "FULL_TABLE"
    assert effects.replication_key is None
    assert effects.schema["additionalProperties"] is True
    assert effects.path.endswith("/v1/applications/42/export_effects")


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
    requests_mock.get(
        "https://example.talon.one/v1/applications/42/campaigns",
        json={"data": [], "hasMore": False},
    )
    requests_mock.get(
        "https://example.talon.one/v1/applications/42/export_effects",
        text="",
    )
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


def test_effects_export_parses_csv_over_frozen_window(
    requests_mock, capsys, monkeypatch
) -> None:
    """Download the effects CSV once over a run-frozen window and emit row records."""
    monkeypatch.setattr(
        streams, "_utcnow", lambda: datetime(2026, 7, 23, 0, 0, 0, tzinfo=UTC)
    )
    requests_mock.get(
        "https://example.talon.one/v1/applications/42/campaigns",
        json={"data": [], "hasMore": False},
    )
    requests_mock.get(
        "https://example.talon.one/v1/applications/42/events/no_total",
        json={"data": [], "hasMore": False},
    )
    csv_body = (
        "\ufeffcampaignId,ruleName,value\r\n7,Spring Sale,10.50\r\n7,Spring Sale,3\r\n"
    ).encode()
    requests_mock.get(
        "https://example.talon.one/v1/applications/42/export_effects",
        content=csv_body,
        headers={"Content-Type": "application/csv"},
    )

    TalonOneTap(config=config()).sync_all()

    effects_requests = [
        request
        for request in requests_mock.request_history
        if request.path.endswith("/export_effects")
    ]
    assert len(effects_requests) == 1
    assert effects_requests[0].headers["Accept"] == "application/csv"
    assert effects_requests[0].qs["createdafter"] == ["2026-07-22t23:00:00z"]
    assert effects_requests[0].qs["createdbefore"] == ["2026-07-23t00:00:00z"]
    assert effects_requests[0].qs["dateformat"] == ["iso8601"]

    messages = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    records = [
        message["record"]
        for message in messages
        if message["type"] == "RECORD" and message["stream"] == "export_effects"
    ]
    assert records == [
        {"campaignId": "7", "ruleName": "Spring Sale", "value": "10.50"},
        {"campaignId": "7", "ruleName": "Spring Sale", "value": "3"},
    ]


def test_effects_window_is_frozen_across_calls(monkeypatch) -> None:
    """Freeze the window at the first call so later wall-clock ticks are ignored."""
    ticks = iter(
        [
            datetime(2026, 7, 23, 0, 0, 0, tzinfo=UTC),
            datetime(2026, 7, 23, 6, 0, 0, tzinfo=UTC),
        ]
    )
    monkeypatch.setattr(streams, "_utcnow", lambda: next(ticks))
    effects = ExportEffectsStream(TalonOneTap(config=config()))

    first = effects.get_url_params(None, None)
    second = effects.get_url_params(None, None)

    assert first == second
    assert first == {
        "createdAfter": "2026-07-22T23:00:00Z",
        "createdBefore": "2026-07-23T00:00:00Z",
        "dateFormat": "ISO8601",
    }
    assert next(ticks) == datetime(2026, 7, 23, 6, 0, 0, tzinfo=UTC)
