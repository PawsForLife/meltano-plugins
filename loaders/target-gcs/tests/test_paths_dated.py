"""Tests for DatedPath: partition path from extraction date, one handle, rotation at limit, close, current_key.

Black-box: assert on keys passed to open, partition path in key, record count per file, and close behaviour only.
"""

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
    """Build DatedPath with given config and injectables. Uses hive_partitioned=True so key template uses partition_date."""
    cfg = config or {}
    default = {"bucket_name": "test-bucket", "hive_partitioned": True}
    merged = {**default, **cfg}
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


# --- Partition path from extraction date ---


def test_dated_path_partition_path_from_extraction_date_in_key():
    """WHAT: Key used for open/write contains partition path from extraction date (year=.../month=.../day=...) and stream and timestamp.
    WHY: Dated partition path must be correct and stable for the run."""
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
        assert "year=2024/month=03/day=11" in key
        assert key.startswith("my_stream/")
        assert "12345" in key
        assert key.endswith(".jsonl")


# --- One handle per run ---


def test_dated_path_one_handle_per_run_when_no_chunking_uses_single_key():
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


def test_dated_path_rotation_at_limit_produces_keys_with_chunk_index_and_distributes_writes():
    """WHAT: With max_records_per_file=2, processing more records opens multiple keys with chunk index (-0, -1) and distributes writes per limit.
    WHY: Chunking within the dated path must match base/Simple behaviour."""
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
                "key_naming_convention": "{stream}/{partition_date}/{timestamp}-{chunk_index}.{format}",
            },
            time_fn=lambda: next(timestamps),
            date_fn=lambda: datetime(2024, 3, 11),
        )
        for i in range(5):
            subject.process_record({"id": i}, {})
        assert mock_open.call_count >= 2
        keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
        assert any("-0." in k or "-0.jsonl" in k for k in keys)
        assert any("-1." in k or "-1.jsonl" in k for k in keys)
        assert mock_handles[0].write.call_count == 2
        assert mock_handles[1].write.call_count == 2


# --- Close behaviour ---


def test_dated_path_close_flushes_and_closes_handle():
    """WHAT: After processing records, close() flushes and closes the handle (observable via mock).
    WHY: Lifecycle must call flush_and_close_handle on close."""
    mock_handle = MagicMock()
    with patch("target_gcs.paths.dated.smart_open.open", return_value=mock_handle):
        subject = build_dated_sink(
            time_fn=lambda: 1.0,
            date_fn=lambda: datetime(2024, 1, 1),
        )
        subject.process_record({"id": 1}, {})
        subject.close()
        mock_handle.flush.assert_called_once()
        mock_handle.close.assert_called_once()


# --- Current key property ---


def test_dated_path_current_key_empty_before_first_write():
    """WHAT: Before any process_record, current_key is empty (or as specified by base contract).
    WHY: Property contract for GCSSink.key_name delegation."""
    subject = build_dated_sink()
    assert subject.current_key == ""


def test_dated_path_current_key_equals_key_passed_to_open_after_one_record():
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
