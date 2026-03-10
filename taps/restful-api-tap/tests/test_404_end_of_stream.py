"""Tests for 404-as-end-of-stream pagination behaviour.

When the initial request returns 404 the tap must raise a fatal error (stream cannot start).
When a next-page request returns 404 the tap must treat it as end-of-stream and return
only records from previous pages.
"""

import json
from pathlib import Path

import pytest
import requests_mock
from singer_sdk.exceptions import FatalAPIError

from restful_api_tap.tap import RestfulApiTap
from tests.test_streams import config, json_resp, url_path

_SCHEMA_PATH = Path(__file__).parent / "schema.json"
_STREAM_SCHEMA = (
    json.loads(_SCHEMA_PATH.read_text())
    if _SCHEMA_PATH.exists()
    else {"type": "object", "properties": {}}
)


def test_initial_request_404_raises_fatal_error(
    requests_mock: requests_mock.Mocker,
) -> None:
    """When the initial request returns 404, the tap raises a fatal error.

    This ensures sync fails when the stream cannot be started (e.g. wrong URL or
    missing resource), rather than silently returning no records.
    """
    # Provide schema in config file so discover_streams() does not call get_schema() (no extra GET).
    cfg = config()
    cfg["streams"][0]["schema"] = _STREAM_SCHEMA
    requests_mock.get(url_path(), status_code=404)
    tap = RestfulApiTap(config=cfg, parse_env_config=True)
    stream = tap.discover_streams()[0]

    with pytest.raises(FatalAPIError):
        list(stream.get_records({}))


def test_next_page_request_404_treated_as_end_of_stream(
    requests_mock: requests_mock.Mocker,
) -> None:
    """When the next-page request returns 404, the tap treats it as end-of-stream and returns first-page records.

    This allows APIs that return an invalid next_page URL on the last page to be
    synced without failing; we consume records already fetched and stop.
    """

    def first_request_matcher(request: object) -> bool:
        return "page" not in (getattr(request, "url", None) or "")

    def second_request_matcher(request: object) -> bool:
        return "page=next_page_token" in (getattr(request, "url", None) or "")

    requests_mock.get(
        url_path(),
        additional_matcher=first_request_matcher,
        status_code=200,
        json=json_resp({"next_page": "next_page_token"}),
    )
    requests_mock.get(
        url_path(),
        additional_matcher=second_request_matcher,
        status_code=404,
    )

    cfg = config()
    cfg["streams"][0]["schema"] = _STREAM_SCHEMA
    tap = RestfulApiTap(config=cfg, parse_env_config=True)
    stream = tap.discover_streams()[0]
    records = list(stream.get_records({}))

    expected_records = json_resp()["records"]
    assert records == expected_records
