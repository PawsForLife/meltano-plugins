"""Black-box tests for stream-level is_sorted config.

Asserts that discovered streams expose stream.is_sorted according to config
(is_sorted true, false, omitted, and per-stream in multi-stream). No assertions
on logs, call counts, or internal functions.
"""

from typing import Any

from restful_api_tap.tap import RestfulApiTap
from tests.test_streams import config, setup_api, url_path


def test_is_sorted_true(requests_mock: Any) -> None:
    """Config with is_sorted true yields a stream with stream.is_sorted True.

    Ensures the tap passes stream-level is_sorted: true through to the
    discovered DynamicStream so the SDK can treat the stream as resumable
    when replication_key is set.
    """
    cfg = config(
        extras={
            "streams": [
                {
                    "name": "sorted_stream",
                    "path": "/path_test",
                    "records_path": "$.records[*]",
                    "primary_keys": ["key1"],
                    "is_sorted": True,
                }
            ]
        }
    )
    setup_api(requests_mock, url_path("/path_test"))
    tap = RestfulApiTap(config=cfg, parse_env_config=True)
    streams = tap.discover_streams()
    assert len(streams) >= 1
    assert streams[0].is_sorted is True


def test_is_sorted_omitted(requests_mock: Any) -> None:
    """Config with is_sorted omitted yields stream.is_sorted False (default).

    Ensures backward compatibility: when is_sorted is not set, the stream
    defaults to is_sorted False so existing behaviour is unchanged.
    """
    cfg = config(
        extras={
            "streams": [
                {
                    "name": "unsorted_stream",
                    "path": "/path_test",
                    "records_path": "$.records[*]",
                    "primary_keys": ["key1"],
                }
            ]
        }
    )
    setup_api(requests_mock, url_path("/path_test"))
    tap = RestfulApiTap(config=cfg, parse_env_config=True)
    streams = tap.discover_streams()
    assert len(streams) >= 1
    assert streams[0].is_sorted is False


def test_is_sorted_false(requests_mock: Any) -> None:
    """Config with is_sorted false yields stream.is_sorted False.

    Ensures explicit false is honoured so streams that are not ordered by
    replication key are not treated as resumable.
    """
    cfg = config(
        extras={
            "streams": [
                {
                    "name": "explicit_unsorted",
                    "path": "/path_test",
                    "records_path": "$.records[*]",
                    "primary_keys": ["key1"],
                    "is_sorted": False,
                }
            ]
        }
    )
    setup_api(requests_mock, url_path("/path_test"))
    tap = RestfulApiTap(config=cfg, parse_env_config=True)
    streams = tap.discover_streams()
    assert len(streams) >= 1
    assert streams[0].is_sorted is False


def test_is_sorted_multiple_streams(requests_mock: Any) -> None:
    """Multiple streams: first is_sorted true, second false; each stream independent.

    Ensures per-stream is_sorted is applied correctly so one stream can be
    resumable and another not within the same tap config.
    """
    cfg = config(
        extras={
            "streams": [
                {
                    "name": "stream_a",
                    "path": "/path_a",
                    "records_path": "$.records[*]",
                    "primary_keys": ["key1"],
                    "is_sorted": True,
                },
                {
                    "name": "stream_b",
                    "path": "/path_b",
                    "records_path": "$.records[*]",
                    "primary_keys": ["key1"],
                    "is_sorted": False,
                },
            ]
        }
    )
    setup_api(requests_mock, url_path("/path_a"))
    setup_api(requests_mock, url_path("/path_b"))
    tap = RestfulApiTap(config=cfg, parse_env_config=True)
    streams = tap.discover_streams()
    assert len(streams) >= 2
    assert streams[0].is_sorted is True
    assert streams[1].is_sorted is False
