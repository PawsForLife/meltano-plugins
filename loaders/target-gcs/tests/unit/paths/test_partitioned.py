"""Tests for PartitionedPath: init validation, partition path from record, handle lifecycle on partition change, rotation at limit, ParserError propagation, current_key.

Black-box: assert on key segments via RecordingGCSClient get_written_paths, and exception type only.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

import pytest
from dateutil.parser import ParserError as DateutilParserError

from target_gcs.paths import PartitionedPath
from tests.fixtures.recording_gcs_client import RecordingGCSClient

# Default schema for tests that do not pass a custom schema (conftest merges config with hive_partitioned).
_DEFAULT_PARTITIONED_SCHEMA: dict[str, Any] = {
    "x-partition-fields": ["region", "dt"],
    "properties": {
        "region": {"type": "string"},
        "dt": {"type": "string"},
    },
    "required": ["region", "dt"],
}


# --- Validation at init ---


def test_partitioned_path_init_invalid_schema_raises(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Building PartitionedPath with schema where a partition field is not in properties raises ValueError.
    WHY: Init validation rejects invalid x-partition-fields before any write."""
    schema = {
        "x-partition-fields": ["region", "missing_field"],
        "properties": {"region": {"type": "string"}},
        "required": ["region"],
    }
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    partition_fields = schema.get("x-partition-fields") or []
    with pytest.raises(ValueError) as exc_info:
        PartitionedPath(
            stream_name="my_stream",
            schema=schema,
            config=config,
            partition_fields=partition_fields,
            time_fn=None,
            storage_client=recording_storage_client,
            extraction_date=fixed_date,
        )
    msg = str(exc_info.value)
    assert "my_stream" in msg
    assert "missing_field" in msg
    assert "not in schema" in msg or "not in" in msg.lower()


def test_partitioned_path_init_field_not_required_raises(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Building PartitionedPath with partition field not in schema required raises ValueError.
    WHY: All partition fields must be required so every record has values."""
    schema = {
        "x-partition-fields": ["region", "dt"],
        "properties": {"region": {"type": "string"}, "dt": {"type": "string"}},
        "required": ["region"],
    }
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    partition_fields = schema.get("x-partition-fields") or []
    with pytest.raises(ValueError) as exc_info:
        PartitionedPath(
            stream_name="my_stream",
            schema=schema,
            config=config,
            partition_fields=partition_fields,
            time_fn=None,
            storage_client=recording_storage_client,
            extraction_date=fixed_date,
        )
    msg = str(exc_info.value)
    assert "my_stream" in msg
    assert "dt" in msg
    assert "must be required" in msg


def test_partitioned_path_init_valid_schema_constructs(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Building PartitionedPath with valid x-partition-fields and matching properties/required succeeds; sink has stream_name and config.
    WHY: Happy path init when schema is valid."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    partition_fields = _DEFAULT_PARTITIONED_SCHEMA.get("x-partition-fields") or []
    subject = PartitionedPath(
        stream_name="my_stream",
        schema=_DEFAULT_PARTITIONED_SCHEMA,
        config=config,
        partition_fields=partition_fields,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    assert subject.stream_name == "my_stream"
    assert subject.config.get("bucket_name") == "test-bucket"
    assert subject.config.get("hive_partitioned") is True


# --- path_for_record ---


def test_path_for_record_uses_hive_path_of_record(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: path_for_record(record) returns path matching {stream}/{hive_path} where hive_path is from hive_path(record).
    WHY: Validates path composition per record; path must contain partition segments from record."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    partition_fields = _DEFAULT_PARTITIONED_SCHEMA.get("x-partition-fields") or []
    subject = PartitionedPath(
        stream_name="my_stream",
        schema=_DEFAULT_PARTITIONED_SCHEMA,
        config=config,
        partition_fields=partition_fields,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    record = {"id": 1, "region": "eu", "dt": "2024-03-11"}
    path = subject.path_for_record(record)
    assert "my_stream" in path
    assert "region=eu" in path
    assert "dt=2024-03-11" in path
    assert path == f"my_stream/{subject.hive_path(record)}"


# --- Partition path from record ---


def test_partitioned_path_keys_contain_partition_segments_from_record(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Processing records with different partition field values yields keys containing correct partition path segments (e.g. region=eu, dt=...).
    WHY: Record-driven partition path must appear correctly in keys."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    partition_fields = _DEFAULT_PARTITIONED_SCHEMA.get("x-partition-fields") or []

    def time_fn() -> float:
        return 11111.0

    subject = PartitionedPath(
        stream_name="my_stream",
        schema=_DEFAULT_PARTITIONED_SCHEMA,
        config=config,
        partition_fields=partition_fields,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1, "region": "eu", "dt": "2024-03-11"}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    key = paths[0][1]
    assert "region=eu" in key
    assert "dt=2024-03-11" in key
    assert "my_stream" in key
    assert "11111" in key
    assert key.endswith(".jsonl")


# --- Handle lifecycle on partition change ---


def test_partition_change_closes_handle_and_resets(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Processing record in partition A then partition B closes the handle and opens a new key for B; state resets.
    WHY: Partition change must close current handle, reset _current_partition_path and _records_written_in_current_file."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    timestamps = iter([4000.0, 4001.0])
    schema = {
        "x-partition-fields": ["region"],
        "properties": {"region": {"type": "string"}},
        "required": ["region"],
    }
    partition_fields = schema.get("x-partition-fields") or []

    def time_fn() -> float:
        return next(timestamps)

    subject = PartitionedPath(
        stream_name="my_stream",
        schema=schema,
        config=config,
        partition_fields=partition_fields,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1, "region": "eu"}, {})
    subject.process_record({"id": 2, "region": "us"}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 2
    keys = [p[1] for p in paths]
    assert "region=eu" in keys[0]
    assert "region=us" in keys[1]
    assert keys[0] != keys[1]


def test_partitioned_path_partition_change_closes_handle_and_opens_new_key(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Processing record in partition A then in partition B closes the handle and opens a new key for B.
    WHY: Partition change must close current handle and write to new partition path."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    timestamps = iter([4000.0, 4001.0])
    schema = {
        "x-partition-fields": ["region"],
        "properties": {"region": {"type": "string"}},
        "required": ["region"],
    }
    partition_fields = schema.get("x-partition-fields") or []

    def time_fn() -> float:
        return next(timestamps)

    subject = PartitionedPath(
        stream_name="my_stream",
        schema=schema,
        config=config,
        partition_fields=partition_fields,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1, "region": "eu"}, {})
    subject.process_record({"id": 2, "region": "us"}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 2
    keys = [p[1] for p in paths]
    assert "region=eu" in keys[0]
    assert "region=us" in keys[1]
    assert keys[0] != keys[1]


def test_partitioned_path_partition_return_creates_new_file(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Processing A then B then A produces three distinct keys; third key is a new file for A, not reopen of first.
    WHY: When partition returns we create a new key, not reopen the old file."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    timestamps = iter([4000.0, 4001.0, 4002.0])
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string"}},
        "required": ["dt"],
    }
    partition_fields = schema.get("x-partition-fields") or []

    def time_fn() -> float:
        return next(timestamps)

    subject = PartitionedPath(
        stream_name="my_stream",
        schema=schema,
        config=config,
        partition_fields=partition_fields,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1, "dt": "2024-03-10"}, {})
    subject.process_record({"id": 2, "dt": "2024-03-11"}, {})
    subject.process_record({"id": 3, "dt": "2024-03-10"}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 3
    keys = [p[1] for p in paths]
    assert len(keys) == len(set(keys))
    assert keys[2] != keys[0]


# --- Rotation at limit within partition ---


def test_chunking_within_partition(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: With max_records_per_file=2 and same partition, three records yield two distinct keys; both share partition path; filenames differ by timestamp.
    WHY: Timestamp-only chunking within partition; no chunk_index in keys."""
    config = {
        "bucket_name": "test-bucket",
        "hive_partitioned": True,
        "max_records_per_file": 2,
    }
    timestamps = iter([5000.0, 5000.0, 5001.0])
    schema = {
        "x-partition-fields": ["region"],
        "properties": {"region": {"type": "string"}},
        "required": ["region"],
    }
    partition_fields = schema.get("x-partition-fields") or []

    def time_fn() -> float:
        return next(timestamps)

    subject = PartitionedPath(
        stream_name="my_stream",
        schema=schema,
        config=config,
        partition_fields=partition_fields,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    for i in range(3):
        subject.process_record({"id": i, "region": "eu"}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 2
    keys = [p[1] for p in paths]
    assert keys[0] != keys[1]
    assert "region=eu" in keys[0] and "region=eu" in keys[1]
    assert "5000" in keys[0] and "5001" in keys[1]


def test_partitioned_path_rotation_at_limit_within_partition(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: With max_records_per_file=2 and same partition, multiple records yield keys differing by timestamp only; same partition path.
    WHY: Chunking within a single partition must match base rotation behaviour (timestamp-only; no chunk_index)."""
    config = {
        "bucket_name": "test-bucket",
        "hive_partitioned": True,
        "max_records_per_file": 2,
    }
    timestamps = iter([3000.0, 3000.0, 3001.0, 3001.0])
    schema = {
        "x-partition-fields": ["region"],
        "properties": {"region": {"type": "string"}},
        "required": ["region"],
    }
    partition_fields = schema.get("x-partition-fields") or []

    def time_fn() -> float:
        return next(timestamps)

    subject = PartitionedPath(
        stream_name="my_stream",
        schema=schema,
        config=config,
        partition_fields=partition_fields,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    for i in range(3):
        subject.process_record({"id": i, "region": "eu"}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 2
    keys = [p[1] for p in paths]
    assert keys[0] != keys[1]
    assert "region=eu" in keys[0] and "region=eu" in keys[1]


# --- ParserError propagation ---


def test_partitioned_path_parser_error_when_date_format_unparseable(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Record with partition field that has format date-time and unparseable string value raises ParserError.
    WHY: Unparseable partition dates must surface to caller; do not swallow."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    schema = {
        "x-partition-fields": ["dt"],
        "properties": {"dt": {"type": "string", "format": "date-time"}},
        "required": ["dt"],
    }
    partition_fields = schema.get("x-partition-fields") or []
    subject = PartitionedPath(
        stream_name="my_stream",
        schema=schema,
        config=config,
        partition_fields=partition_fields,
        time_fn=None,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    with pytest.raises(DateutilParserError):
        subject.process_record({"id": 1, "dt": "not-a-date"}, {})


# --- Current key ---


def test_partitioned_path_current_key_empty_before_first_write(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Before calling process_record, current_key is empty (or as specified by base contract).
    WHY: Property contract for GCSSink.key_name delegation after task 06."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    partition_fields = _DEFAULT_PARTITIONED_SCHEMA.get("x-partition-fields") or []
    subject = PartitionedPath(
        stream_name="my_stream",
        schema=_DEFAULT_PARTITIONED_SCHEMA,
        config=config,
        partition_fields=partition_fields,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    assert subject.current_key == ""


def test_partitioned_path_current_key_equals_key_after_write(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: After processing one record, current_key equals the key that was used for the write.
    WHY: key_name delegation will work after task 06."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    partition_fields = _DEFAULT_PARTITIONED_SCHEMA.get("x-partition-fields") or []
    subject = PartitionedPath(
        stream_name="my_stream",
        schema=_DEFAULT_PARTITIONED_SCHEMA,
        config=config,
        partition_fields=partition_fields,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1, "region": "eu", "dt": "2024-03-11"}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    assert subject.current_key == paths[0][1]
