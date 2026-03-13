"""Tests for PartitionedPath: init validation, partition path from record, handle lifecycle on partition change, rotation at limit, ParserError propagation, current_key.

Black-box: assert on key segments, handle close/open behaviour, and exception type only.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from dateutil.parser import ParserError as DateutilParserError

from target_gcs.paths.partitioned import PartitionedPath


def build_partitioned_sink(
    config: dict[str, Any] | None = None,
    *,
    time_fn: Any = None,
    date_fn: Any = None,
    storage_client: Any = None,
    stream_name: str = "my_stream",
    schema: dict[str, Any] | None = None,
    extraction_date: datetime | None = None,
) -> PartitionedPath:
    """Build PartitionedPath with given config and injectables. Default schema has non-empty x-partition-fields and matching properties/required."""
    cfg = config or {}
    default = {"bucket_name": "test-bucket", "hive_partitioned": True}
    merged = {**default, **cfg}
    default_schema = {
        "x-partition-fields": ["region", "dt"],
        "properties": {
            "region": {"type": "string"},
            "dt": {"type": "string"},
        },
        "required": ["region", "dt"],
    }
    return PartitionedPath(
        target=None,
        stream_name=stream_name,
        schema=schema if schema is not None else default_schema,
        key_properties=[],
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


# --- Validation at init ---


def test_partitioned_path_init_invalid_schema_raises():
    """WHAT: Building PartitionedPath with schema where a partition field is not in properties raises ValueError.
    WHY: Init validation rejects invalid x-partition-fields before any write."""
    schema = {
        "x-partition-fields": ["region", "missing_field"],
        "properties": {"region": {"type": "string"}},
        "required": ["region"],
    }
    with pytest.raises(ValueError) as exc_info:
        build_partitioned_sink(schema=schema)
    msg = str(exc_info.value)
    assert "my_stream" in msg
    assert "missing_field" in msg
    assert "not in schema" in msg or "not in" in msg.lower()


def test_partitioned_path_init_field_not_required_raises():
    """WHAT: Building PartitionedPath with partition field not in schema required raises ValueError.
    WHY: All partition fields must be required so every record has values."""
    schema = {
        "x-partition-fields": ["region", "dt"],
        "properties": {"region": {"type": "string"}, "dt": {"type": "string"}},
        "required": ["region"],
    }
    with pytest.raises(ValueError) as exc_info:
        build_partitioned_sink(schema=schema)
    msg = str(exc_info.value)
    assert "my_stream" in msg
    assert "dt" in msg
    assert "must be required" in msg


def test_partitioned_path_init_valid_schema_constructs():
    """WHAT: Building PartitionedPath with valid x-partition-fields and matching properties/required succeeds; sink has stream_name and config.
    WHY: Happy path init when schema is valid."""
    subject = build_partitioned_sink()
    assert subject.stream_name == "my_stream"
    assert subject.config.get("bucket_name") == "test-bucket"
    assert subject.config.get("hive_partitioned") is True


# --- Partition path from record ---


def test_partitioned_path_keys_contain_partition_segments_from_record():
    """WHAT: Processing records with different partition field values yields keys containing correct partition path segments (e.g. region=eu, dt=...).
    WHY: Record-driven partition path must appear correctly in keys."""
    fixed_ts = 11111.0
    fixed_dt = datetime(2024, 3, 11)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.partitioned.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = build_partitioned_sink(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1, "region": "eu", "dt": "2024-03-11"}, {})
    key = _key_from_open_call(mock_open.call_args)
    assert "region=eu" in key
    assert "dt=2024-03-11" in key
    assert "my_stream" in key
    assert "11111" in key
    assert key.endswith(".jsonl")


# --- Handle lifecycle on partition change ---


def test_partitioned_path_partition_change_closes_handle_and_opens_new_key():
    """WHAT: Processing record in partition A then in partition B closes the handle and opens a new key for B.
    WHY: Partition change must close current handle and write to new partition path."""
    timestamps = iter([4000.0, 4001.0])

    def time_fn() -> float:
        return next(timestamps)

    schema = {
        "x-partition-fields": ["region"],
        "properties": {"region": {"type": "string"}},
        "required": ["region"],
    }
    mock_handles = [MagicMock(), MagicMock()]
    with patch(
        "target_gcs.paths.partitioned.smart_open.open",
        side_effect=mock_handles,
    ) as mock_open:
        subject = build_partitioned_sink(
            schema=schema,
            time_fn=time_fn,
            date_fn=lambda: datetime(2024, 3, 11),
        )
        subject.process_record({"id": 1, "region": "eu"}, {})
        subject.process_record({"id": 2, "region": "us"}, {})
    assert mock_open.call_count == 2
    keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert "region=eu" in keys[0]
    assert "region=us" in keys[1]
    assert keys[0] != keys[1]


def test_partitioned_path_partition_return_creates_new_file():
    """WHAT: Processing A then B then A produces three distinct keys; third key is a new file for A, not reopen of first.
    WHY: When partition returns we create a new key, not reopen the old file."""
    timestamps = iter([4000.0, 4001.0, 4002.0])

    def time_fn() -> float:
        return next(timestamps)

    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": ["dt"],
    }
    with patch(
        "target_gcs.paths.partitioned.smart_open.open",
        side_effect=[MagicMock(), MagicMock(), MagicMock()],
    ) as mock_open:
        subject = build_partitioned_sink(
            schema=schema,
            time_fn=time_fn,
            date_fn=lambda: datetime(2024, 3, 11),
        )
        subject.process_record({"id": 1, "dt": "2024-03-10"}, {})
        subject.process_record({"id": 2, "dt": "2024-03-11"}, {})
        subject.process_record({"id": 3, "dt": "2024-03-10"}, {})
    assert mock_open.call_count == 3
    keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert len(keys) == len(set(keys)), "all three keys must be distinct"
    assert keys[2] != keys[0], "third key (A') must differ from first (A); no reopen"


# --- Rotation at limit within partition ---


def test_partitioned_path_rotation_at_limit_within_partition():
    """WHAT: With max_records_per_file=2 and same partition, multiple records yield keys with chunk index and correct open count.
    WHY: Chunking within a single partition must match base rotation behaviour."""
    # time_fn is used by get_chunk_format_map (per record) and by maybe_rotate_if_at_limit (on rotate); provide enough values.
    timestamps = iter([3000.0, 3000.0, 3001.0, 3001.0])

    def time_fn() -> float:
        return next(timestamps)

    schema = {
        "x-partition-fields": ["region"],
        "properties": {"region": {"type": "string"}},
        "required": ["region"],
    }
    mock_handles = [MagicMock(), MagicMock()]
    with patch(
        "target_gcs.paths.partitioned.smart_open.open",
        side_effect=mock_handles,
    ) as mock_open:
        subject = build_partitioned_sink(
            config={
                "bucket_name": "test-bucket",
                "hive_partitioned": True,
                "max_records_per_file": 2,
            },
            schema=schema,
            time_fn=time_fn,
            date_fn=lambda: datetime(2024, 3, 11),
        )
        for i in range(3):
            subject.process_record({"id": i, "region": "eu"}, {})
    assert mock_open.call_count == 2
    keys = [_key_from_open_call(c) for c in mock_open.call_args_list]
    assert keys[0] != keys[1]
    assert "region=eu" in keys[0] and "region=eu" in keys[1]


# --- ParserError propagation ---


def test_partitioned_path_parser_error_when_date_format_unparseable():
    """WHAT: Record with partition field that has format date-time and unparseable string value raises ParserError.
    WHY: Unparseable partition dates must surface to caller; do not swallow."""
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string", "format": "date-time"}},
        "required": ["dt"],
    }
    with patch(
        "target_gcs.paths.partitioned.smart_open.open",
        return_value=MagicMock(),
    ):
        subject = build_partitioned_sink(
            schema=schema,
            date_fn=lambda: datetime(2024, 3, 11),
        )
        with pytest.raises(DateutilParserError):
            subject.process_record({"id": 1, "dt": "not-a-date"}, {})


# --- Current key ---


def test_partitioned_path_current_key_empty_before_first_write():
    """WHAT: Before calling process_record, current_key is empty (or as specified by base contract).
    WHY: Property contract for GCSSink.key_name delegation after task 06."""
    subject = build_partitioned_sink()
    assert subject.current_key == ""


def test_partitioned_path_current_key_equals_key_after_write():
    """WHAT: After processing one record, current_key equals the key that was used for the write.
    WHY: key_name delegation will work after task 06."""
    fixed_ts = 55555.0
    fixed_dt = datetime(2024, 3, 11)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.partitioned.smart_open.open",
        return_value=mock_handle,
    ) as mock_open:
        subject = build_partitioned_sink(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1, "region": "eu", "dt": "2024-03-11"}, {})
    expected_key = _key_from_open_call(mock_open.call_args)
    assert subject.current_key == expected_key
