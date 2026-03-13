"""Tests for DatedPath: partition path from extraction date, one handle, rotation at limit, close, current_key.

Black-box: assert on keys passed to open, partition path in key, and close behaviour only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

from target_gcs.paths.dated import DatedPath


def build_dated_sink(
    config: dict[str, Any] | None = None,
    *,
    time_fn: Any = None,
    date_fn: Any = None,
    storage_client: Any = None,
    stream_name: str = "my_stream",
    extraction_date: datetime | None = None,
) -> DatedPath:
    """Build DatedPath with given config and injectables."""
    cfg = config or {}
    merged = {**{"bucket_name": "test-bucket", "hive_partitioned": True}, **cfg}
    return DatedPath(
        stream_name=stream_name,
        config=merged,
        time_fn=time_fn,
        date_fn=date_fn,
        storage_client=storage_client,
        extraction_date=extraction_date,
    )


def _key_from_open_call(call_args: tuple) -> str:
    """Extract GCS object key from smart_open.open first positional arg (gs://bucket/key)."""
    url: str = str(call_args[0][0])
    return url.split("/", 3)[-1]


# --- Path from PATH_DATED constant ---


def test_path_from_path_dated_constant() -> None:
    """WHAT: Key matches {stream}/{hive_path}/{timestamp}.jsonl shape from PATH_DATED.
    WHY: Validates path is built from PATH_DATED constant at init."""
    fixed_ts = 12345.0
    fixed_dt = datetime(2024, 3, 11)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.dated.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = build_dated_sink(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1, "name": "a"}, {})
        assert mock_open.call_count == 1
        key = _key_from_open_call(mock_open.call_args)
        assert key.startswith("my_stream/")
        assert "year=2024/month=03/day=11" in key
        assert "12345" in key
        assert key.endswith(".jsonl")


def test_hive_path_is_extraction_date_formatted() -> None:
    """WHAT: hive_path segment equals year=YYYY/month=MM/day=DD from extraction date.
    WHY: Validates DatedPath semantics: partition path uses DEFAULT_PARTITION_DATE_FORMAT."""
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.dated.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = build_dated_sink(
            time_fn=lambda: 99999.0,
            extraction_date=datetime(2024, 6, 15),
        )
        subject.process_record({"id": 1}, {})
        key = _key_from_open_call(mock_open.call_args)
        assert "year=2024/month=06/day=15" in key


def test_filename_is_timestamp_jsonl() -> None:
    """WHAT: Filename segment is {timestamp}.jsonl (no chunk_index).
    WHY: Validates filename format uses timestamp-only chunking (FILENAME_TEMPLATE)."""
    fixed_ts = 77777.0
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.dated.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = build_dated_sink(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: datetime(2024, 1, 1),
        )
        subject.process_record({"id": 1}, {})
        key = _key_from_open_call(mock_open.call_args)
        assert key.endswith("77777.jsonl")
        assert "-0" not in key and "-1" not in key


# --- One handle per run ---


def test_dated_path_one_handle_per_run_when_no_chunking_uses_single_key() -> None:
    """WHAT: With max_records_per_file unset/0, processing multiple records uses one key and one open call.
    WHY: No spurious rotation when partition is fixed for the run."""
    fixed_ts = 9999.0
    fixed_dt = datetime(2024, 1, 1)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.dated.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = build_dated_sink(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        for i in range(5):
            subject.process_record({"id": i}, {})
        assert mock_open.call_count == 1
        keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
        assert len(set(keys)) == 1
        assert "year=2024/month=01/day=01" in keys[0]


# --- Rotation at limit ---


def test_dated_path_rotation_at_limit_produces_distinct_keys() -> None:
    """WHAT: With max_records_per_file=2, processing more records opens multiple handles with distinct keys.
    WHY: Chunking within the dated path must match base/Simple behaviour; key shape uses timestamp (no chunk_index after task 03)."""
    timestamps = iter([1000.0, 1001.0, 1002.0, 1003.0, 1004.0, 1005.0, 1006.0, 1007.0])
    mock_handles = [MagicMock(), MagicMock(), MagicMock()]
    with patch(
        "target_gcs.paths.dated.smart_open.open", side_effect=mock_handles
    ) as mock_open:
        subject = build_dated_sink(
            config={
                "bucket_name": "test-bucket",
                "hive_partitioned": True,
                "max_records_per_file": 2,
            },
            time_fn=lambda: next(timestamps),
            date_fn=lambda: datetime(2024, 3, 11),
        )
        for i in range(5):
            subject.process_record({"id": i}, {})
        assert mock_open.call_count >= 2
        keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
        assert len(set(keys)) >= 2, "rotation must produce distinct keys"


# --- Close behaviour (black-box) ---


def test_dated_path_close_allows_subsequent_write_to_open_new_handle() -> None:
    """WHAT: After process_record and close(), a subsequent process_record opens a new handle (new key).
    WHY: Lifecycle must release resources; observable outcome is that next write uses a new file."""
    timestamps = iter([1.0, 2.0])
    mock_handles = [MagicMock(), MagicMock()]
    with patch(
        "target_gcs.paths.dated.smart_open.open", side_effect=mock_handles
    ) as mock_open:
        subject = build_dated_sink(
            time_fn=lambda: next(timestamps),
            date_fn=lambda: datetime(2024, 1, 1),
        )
        subject.process_record({"id": 1}, {})
        subject.close()
        subject.process_record({"id": 2}, {})
        keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert mock_open.call_count == 2
    assert keys[0] != keys[1]


# --- Current key property ---


def test_dated_path_current_key_empty_before_first_write() -> None:
    """WHAT: Before any process_record, current_key is empty (or as specified by base contract).
    WHY: Property contract for GCSSink.key_name delegation."""
    subject = build_dated_sink()
    assert subject.current_key == ""


def test_dated_path_current_key_equals_key_passed_to_open_after_one_record() -> None:
    """WHAT: After processing one record, current_key equals the key used for the write (key passed to open).
    WHY: key_name delegation will work after task 06."""
    fixed_ts = 5555.0
    fixed_dt = datetime(2024, 6, 15)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.dated.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = build_dated_sink(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1}, {})
        opened_key = _key_from_open_call(mock_open.call_args)
        assert subject.current_key == opened_key
