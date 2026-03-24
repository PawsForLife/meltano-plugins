"""Tests for JSONPath pagination when the API repeats the cursor token (end-of-data signal).

Some cursor-based APIs return the same last-record cursor on the next page when there
are no further rows. The Singer SDK treats identical consecutive tokens as an infinite
loop and raises; the optional duplicate-token paginator ends pagination instead.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
import requests
from singer_sdk.pagination import JSONPathPaginator

from restful_api_tap.pagination import DuplicateTokenStopsJSONPathPaginator
from restful_api_tap.tap import RestfulApiTap


def _tap_config_stop_on_duplicate(*, stop: bool) -> dict[str, Any]:
    """Minimal tap config: array body, cursor from last sequence_id, optional flag."""
    return {
        "api_url": "https://example.com",
        "pagination_next_page_param": "after",
        "next_page_token_path": "$[-1].sequence_id",
        "pagination_stop_on_duplicate_token": stop,
        "streams": [
            {
                "name": "sessions",
                "path": "/path_test",
                "primary_keys": ["uuid"],
                "replication_key": "sequence_id",
                "records_path": "$[*]",
            }
        ],
    }


def _url_path() -> str:
    return "https://example.com/path_test"


def _response_with_json(body: Any) -> requests.Response:
    """Build a minimal Response whose .json() returns body."""
    resp = MagicMock(spec=requests.Response)
    resp.json.return_value = body
    return resp


def test_duplicate_token_stops_paginator_sets_finished_when_token_repeats() -> None:
    """When the next extracted token equals the current token, pagination stops cleanly.

    WHY: Medallia/Stella-style APIs may echo the same sequence_id when no further
    pages exist; the tap must not crash with SDK loop detection.
    """
    paginator = DuplicateTokenStopsJSONPathPaginator("$[-1].sequence_id")
    page1 = _response_with_json(
        [{"uuid": "a", "sequence_id": 10}, {"uuid": "b", "sequence_id": 20}]
    )
    page2 = _response_with_json(
        [{"uuid": "c", "sequence_id": 15}, {"uuid": "d", "sequence_id": 20}]
    )

    paginator.advance(page1)
    assert paginator.current_value == 20
    assert not paginator.finished

    paginator.advance(page2)
    assert paginator.finished


def test_standard_jsonpath_paginator_raises_on_duplicate_token() -> None:
    """SDK JSONPathPaginator still raises on duplicate token (unchanged default).

    WHY: Ensures opt-in behavior only applies when the new paginator is selected.
    """
    paginator = JSONPathPaginator("$[-1].sequence_id")
    page1 = _response_with_json([{"sequence_id": 1}, {"sequence_id": 2}])
    page2 = _response_with_json([{"sequence_id": 2}])

    paginator.advance(page1)
    with pytest.raises(RuntimeError, match="Loop detected in pagination"):
        paginator.advance(page2)


def test_tap_yields_all_records_when_flag_stops_duplicate_cursor(
    requests_mock: Any,
) -> None:
    """End-to-end: duplicate last sequence_id on page 2 ends sync and keeps records.

    WHY: Mirrors Medallia coaching_sessions behaviour without live API calls.
    """
    page1 = [
        {"uuid": "a", "sequence_id": 100},
        {"uuid": "b", "sequence_id": 200},
    ]
    page2 = [{"uuid": "c", "sequence_id": 200}]

    def first_page(req: Any) -> bool:
        return "after=" not in req.url

    def second_page(req: Any) -> bool:
        return "after=200" in req.url

    requests_mock.get(_url_path(), additional_matcher=first_page, json=page1)
    requests_mock.get(_url_path(), additional_matcher=second_page, json=page2)

    tap = RestfulApiTap(
        config=_tap_config_stop_on_duplicate(stop=True), parse_env_config=True
    )
    stream = tap.discover_streams()[0]
    records = list(stream.get_records({}))
    assert records == page1 + page2


def test_tap_raises_without_flag_on_duplicate_cursor(requests_mock: Any) -> None:
    """Default tap still surfaces SDK loop error when the cursor repeats.

    WHY: Confirms the new behaviour is opt-in and defaults match the SDK.
    """
    page1 = [{"uuid": "a", "sequence_id": 10}, {"uuid": "b", "sequence_id": 20}]
    page2 = [{"uuid": "c", "sequence_id": 20}]

    def first_page(req: Any) -> bool:
        return "after=" not in req.url

    def second_page(req: Any) -> bool:
        return "after=20" in req.url

    requests_mock.get(_url_path(), additional_matcher=first_page, json=page1)
    requests_mock.get(_url_path(), additional_matcher=second_page, json=page2)

    tap = RestfulApiTap(
        config=_tap_config_stop_on_duplicate(stop=False), parse_env_config=True
    )
    stream = tap.discover_streams()[0]
    with pytest.raises(RuntimeError, match="Loop detected in pagination"):
        list(stream.get_records({}))
