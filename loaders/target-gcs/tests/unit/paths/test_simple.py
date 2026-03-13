"""Tests for SimplePath: key generation, one handle, rotation at limit, close, current_key.

Black-box: assert on keys passed to open, record count per file (via keys), and close behaviour only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

from target_gcs.paths.simple import SimplePath


def _build_simple_path(
    config: dict[str, Any] | None = None,
    *,
    time_fn: Any = None,
    date_fn: Any = None,
    storage_client: Any = None,
    extraction_date: Any = None,
) -> SimplePath:
    """Build SimplePath with given config and injectables."""
    cfg = config or {}
    merged = {**{"bucket_name": "test-bucket"}, **cfg}
    return SimplePath(
        stream_name="my_stream",
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


# --- Key generation (single path) ---


def test_simple_path_key_generation_single_path_matches_stream_date_timestamp_format() -> (
    None
):
    """WHAT: After processing one record, the key passed to open matches stream, date (from date_fn), timestamp (from time_fn), and format.
    WHY: Single-path key shape must match current non-hive behaviour for compatibility."""
    fixed_ts = 12345.0
    fixed_dt = datetime(2024, 3, 11)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.simple.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = _build_simple_path(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1, "name": "a"}, {})
        assert mock_open.call_count == 1
        key = _key_from_open_call(mock_open.call_args)
        assert key.startswith("my_stream_")
        assert "12345" in key
        assert key.endswith(".jsonl")


# --- One handle (no chunking) ---


def test_simple_path_one_handle_when_no_chunking_uses_single_key() -> None:
    """WHAT: With max_records_per_file=0 (or unset), processing multiple records opens exactly one handle with one key.
    WHY: No spurious rotation when chunking is disabled."""
    fixed_ts = 9999.0
    fixed_dt = datetime(2024, 1, 1)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.simple.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = _build_simple_path(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        for i in range(5):
            subject.process_record({"id": i}, {})
        assert mock_open.call_count == 1
        keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
        assert len(set(keys)) == 1


# --- Rotation at limit ---


def test_simple_path_rotation_at_limit_produces_distinct_keys() -> None:
    """WHAT: With max_records_per_file=2, processing more than 2 records opens multiple handles with distinct keys.
    WHY: Rotation at limit must produce multiple files; key shape uses timestamp (no chunk_index after task 03)."""
    timestamps = iter([1000.0, 1001.0, 1002.0, 1003.0, 1004.0, 1005.0, 1006.0, 1007.0])
    mock_handles = [MagicMock(), MagicMock(), MagicMock()]
    with patch(
        "target_gcs.paths.simple.smart_open.open", side_effect=mock_handles
    ) as mock_open:
        subject = _build_simple_path(
            config={"bucket_name": "test-bucket", "max_records_per_file": 2},
            time_fn=lambda: next(timestamps),
            date_fn=lambda: datetime(2024, 3, 11),
        )
        for i in range(5):
            subject.process_record({"id": i}, {})
        assert mock_open.call_count >= 2
        keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
        assert len(set(keys)) >= 2, "rotation must produce distinct keys"


# --- Close behaviour (black-box: after close, next write uses new handle) ---


def test_simple_path_close_allows_subsequent_write_to_open_new_handle() -> None:
    """WHAT: After processing records and close(), a subsequent process_record opens a new handle (new key).
    WHY: Lifecycle must release resources; observable outcome is that next write uses a new file."""
    timestamps = iter([1.0, 2.0])
    fixed_dt = datetime(2024, 1, 1)
    mock_handles = [MagicMock(), MagicMock()]
    with patch(
        "target_gcs.paths.simple.smart_open.open", side_effect=mock_handles
    ) as mock_open:
        subject = _build_simple_path(
            time_fn=lambda: next(timestamps),
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1}, {})
        key_before = _key_from_open_call(mock_open.call_args)
        subject.close()
        subject.process_record({"id": 2}, {})
        keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert mock_open.call_count == 2
    assert keys[0] != keys[1]
    assert key_before == keys[0]


# --- Current key property ---


def test_simple_path_current_key_empty_before_first_write() -> None:
    """WHAT: Before any record is processed, current_key returns empty string.
    WHY: GCSSink can delegate key_name to pattern; empty until first write."""
    subject = _build_simple_path()
    assert subject.current_key == ""


def test_simple_path_current_key_equals_key_passed_to_open_after_one_record() -> None:
    """WHAT: After processing one record, current_key returns the same key that was passed to open.
    WHY: GCSSink can delegate key_name to pattern for tests and introspection."""
    fixed_ts = 5555.0
    fixed_dt = datetime(2024, 6, 15)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.simple.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = _build_simple_path(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1}, {})
        opened_key = _key_from_open_call(mock_open.call_args)
        assert subject.current_key == opened_key
