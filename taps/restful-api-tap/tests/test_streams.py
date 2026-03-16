"""Tests stream.py features."""

from typing import Any

import requests

from restful_api_tap.tap import RestfulApiTap


def config(extras: dict | None = None) -> dict:
    """Utility function giving a basic config file structure for tap tests.

    Args:
        extras: items to add to the basic config file contents.

    Returns:
        A complete config file structure (dict) for the tap.

    """
    contents = {
        "api_url": "https://example.com",
        "streams": [
            {
                "name": "stream_name",
                "path": "/path_test",
                "primary_keys": ["key1", "key2"],
                "replication_key": "key3",
                "records_path": "$.records[*]",
            }
        ],
    }
    if extras:
        for k, v in extras.items():
            contents[k] = v
    return contents


def json_resp(extras: dict | None = None) -> dict:
    """Utility function returning a common response for mocked API calls.

    Args:
        extras: items to be added to the contents of the json response.

    Returns:
        A json object that mocks the results of an API call.

    """
    contents = {
        "records": [
            {
                "key1": "this",
                "key2": "that",
                "key3": "foo",
                "field1": "I",
            },
            {"key1": "foo", "key2": "bar", "key3": "spam", "field2": 8},
        ],
    }
    if extras:
        for k, v in extras.items():
            contents[k] = v
    return contents


def url_path(path: str = "/path_test") -> str:
    """Utility function returning a common url for mocked API calls.

    Args:
        path: a path to add to the end of the base url.

    Returns:
        A full url.

    """
    return "https://example.com" + path


def setup_api(
    requests_mock: Any,
    url_path: str = url_path(),
    json_extras: dict | None = None,
    headers_extras: dict | None = None,
    matcher: Any | None = None,
) -> requests.Response:
    """Utility function for mocking API calls.

    Args:
        requests_mock: mock object for requests.
        url_path: url to mack for mocking.
        json_extras: extra items to add to the response's results.
        headers_extras: extra items to add to the API call's header.
        matcher: a function that checks a request's input for the appropriate
            configuration.

    Returns:
        A mocked requests.Response object.

    """
    headers_resp = {}
    if headers_extras:
        for k, v in headers_extras.items():
            headers_resp[k] = v

    requests_mock.get(
        url_path,
        headers=headers_resp,
        json=json_resp(json_extras),
        additional_matcher=matcher,
    )
    return requests.Session().get(url_path)


# Nested record used to verify post_process flatten vs no-flatten behaviour.
_NESTED_RECORD = {"user": {"name": "a", "id": 1}}
_NESTED_RESPONSE = {"records": [_NESTED_RECORD]}


def test_sync_returns_flattened_records_when_flatten_records_true(requests_mock):
    """Sync returns records with flattened keys when stream has flatten_records=True.

    Ensures post_process applies flatten_json when the flag is true so that
    current flatten behaviour is preserved. get_records() yields raw records;
    we run post_process to match sync behaviour.
    """
    setup_api(requests_mock, url_path(), json_extras=_NESTED_RESPONSE)
    tap = RestfulApiTap(config=config(), parse_env_config=True)
    stream = tap.discover_streams()[0]
    stream.flatten_records = True
    records = []
    for row in stream.get_records({}):
        processed = stream.post_process(row, {})
        if processed is not None:
            records.append(processed)
    assert len(records) == 1
    record = records[0]
    assert "user_name" in record and record["user_name"] == "a"
    assert "user_id" in record and record["user_id"] == 1
    assert "user" not in record


def test_sync_returns_nested_records_when_flatten_records_false(requests_mock):
    """Sync returns records with nested structure when stream has flatten_records=False.

    Ensures post_process returns row unchanged when the flag is false so that
    no-flatten path is accepted.
    """
    setup_api(requests_mock, url_path(), json_extras=_NESTED_RESPONSE)
    tap = RestfulApiTap(config=config(), parse_env_config=True)
    stream = tap.discover_streams()[0]
    stream.flatten_records = False
    records = list(stream.get_records({}))
    assert len(records) == 1
    record = records[0]
    assert "user" in record and isinstance(record["user"], dict)
    assert record["user"]["name"] == "a"
    assert record["user"]["id"] == 1
    assert "user_name" not in record
    assert "user_id" not in record


def test_flatten_records_stream_override_top_level_false_stream_true(requests_mock):
    """Stream-level flatten_records=True overrides top-level False (discovery wiring).

    Config file has top-level flatten_records false and this stream flatten_records
    true. Asserts the stream emits flattened records and has flattened inferred
    schema, so discovery correctly resolves and passes flatten_records into
    get_schema and DynamicStream (black-box: record shape and schema properties only).
    """
    cfg = config()
    cfg["flatten_records"] = False
    cfg["streams"][0]["flatten_records"] = True
    setup_api(requests_mock, url_path(), json_extras=_NESTED_RESPONSE)
    tap = RestfulApiTap(config=cfg, parse_env_config=True)
    streams = tap.discover_streams()
    stream = streams[0]
    records = []
    for row in stream.get_records({}):
        processed = stream.post_process(row, {})
        if processed is not None:
            records.append(processed)
    assert len(records) == 1
    record = records[0]
    assert "user_name" in record and record["user_name"] == "a"
    assert "user_id" in record and record["user_id"] == 1
    assert "user" not in record
    schema = stream.schema
    assert "properties" in schema
    assert "user_id" in schema["properties"]
    assert "user_name" in schema["properties"]
    assert "user" not in schema["properties"]


def test_flatten_records_stream_override_top_level_true_stream_false(requests_mock):
    """Stream-level flatten_records=False overrides top-level True (discovery wiring).

    Config file has top-level flatten_records true and this stream flatten_records
    false. Asserts the stream emits nested records and has nested inferred schema,
    so discovery correctly resolves and passes flatten_records into get_schema and
    DynamicStream (black-box: record shape and schema properties only).
    """
    cfg = config()
    cfg["flatten_records"] = True
    cfg["streams"][0]["flatten_records"] = False
    setup_api(requests_mock, url_path(), json_extras=_NESTED_RESPONSE)
    tap = RestfulApiTap(config=cfg, parse_env_config=True)
    streams = tap.discover_streams()
    stream = streams[0]
    records = []
    for row in stream.get_records({}):
        processed = stream.post_process(row, {})
        if processed is not None:
            records.append(processed)
    assert len(records) == 1
    record = records[0]
    assert "user" in record and isinstance(record["user"], dict)
    assert record["user"]["name"] == "a"
    assert record["user"]["id"] == 1
    assert "user_name" not in record
    assert "user_id" not in record
    schema = stream.schema
    assert "properties" in schema
    assert "user" in schema["properties"]
    assert "properties" in schema["properties"]["user"]
    assert "id" in schema["properties"]["user"]["properties"]
    assert "name" in schema["properties"]["user"]["properties"]


def test_pagination_style_default(requests_mock):
    """Stream returns all records across pages when pagination uses next_page token."""

    def first_matcher(request):
        return "page" not in request.url

    def second_matcher(request):
        return "page=next_page_token" in request.url

    requests_mock.get(
        url_path(),
        additional_matcher=first_matcher,
        json=json_resp({"next_page": "next_page_token"}),
    )
    requests_mock.get(url_path(), additional_matcher=second_matcher, json=json_resp())

    stream0 = RestfulApiTap(config=config(), parse_env_config=True).discover_streams()[
        0
    ]
    records_gen = stream0.get_records({})
    records = []
    for record in records_gen:
        records.append(record)

    assert records == [
        json_resp()["records"][0],
        json_resp()["records"][1],
        json_resp()["records"][0],
        json_resp()["records"][1],
    ]
