"""Tests for DatedPath: partition path from extraction date, one handle, rotation at limit, close, current_key.

Black-box: assert on keys and content via RecordingGCSClient get_written_paths.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from target_gcs.paths import DatedPath
from tests.fixtures.recording_gcs_client import RecordingGCSClient

# --- Path from PATH_DATED constant ---


def test_path_from_path_dated_constant(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Key matches {stream}/{hive_path}/{timestamp}.jsonl shape from PATH_DATED.
    WHY: Validates path is built from PATH_DATED constant at init."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    subject = DatedPath(
        stream_name="my_stream",
        config=config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1, "name": "a"}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    key = paths[0][1]
    assert key.startswith("my_stream/")
    assert "year=2024/month=03/day=11" in key
    assert "12345" in key
    assert key.endswith(".jsonl")


def test_hive_path_is_extraction_date_formatted(
    fixed_time_fn: Callable[[], float],
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: hive_path segment equals year=YYYY/month=MM/day=DD from extraction date.
    WHY: Validates DatedPath semantics: partition path uses DEFAULT_PARTITION_DATE_FORMAT."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    extraction_date = datetime(2024, 6, 15)
    subject = DatedPath(
        stream_name="my_stream",
        config=config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=extraction_date,
    )
    subject.process_record({"id": 1}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    assert "year=2024/month=06/day=15" in paths[0][1]


def test_filename_is_timestamp_jsonl(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Filename segment is {timestamp}.jsonl (no chunk_index).
    WHY: Validates filename format uses timestamp-only chunking (FILENAME_TEMPLATE)."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}

    def time_fn() -> float:
        return 77777.0

    subject = DatedPath(
        stream_name="my_stream",
        config=config,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    key = paths[0][1]
    assert key.endswith("77777.jsonl")
    assert "-0" not in key and "-1" not in key


# --- One handle per run ---


def test_dated_path_one_handle_per_run_when_no_chunking_uses_single_key(
    fixed_time_fn: Callable[[], float],
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: With max_records_per_file unset/0, processing multiple records uses one key and one open call.
    WHY: No spurious rotation when partition is fixed for the run."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    extraction_date = datetime(2024, 1, 1)
    subject = DatedPath(
        stream_name="my_stream",
        config=config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=extraction_date,
    )
    for i in range(5):
        subject.process_record({"id": i}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    keys = [p[1] for p in paths]
    assert len(set(keys)) == 1
    assert "year=2024/month=01/day=01" in keys[0]


# --- Rotation at limit ---


def test_dated_path_rotation_at_limit_produces_distinct_keys(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: With max_records_per_file=2, processing more records opens multiple handles with distinct keys.
    WHY: Chunking within the dated path must match base/Simple behaviour; key shape uses timestamp (no chunk_index)."""
    config = {
        "bucket_name": "test-bucket",
        "hive_partitioned": True,
        "max_records_per_file": 2,
    }
    timestamps = iter([1000.0, 1001.0, 1002.0, 1003.0, 1004.0, 1005.0, 1006.0, 1007.0])

    def time_fn() -> float:
        return next(timestamps)

    subject = DatedPath(
        stream_name="my_stream",
        config=config,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    for i in range(5):
        subject.process_record({"id": i}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) >= 2
    keys = [p[1] for p in paths]
    assert len(set(keys)) >= 2, "rotation must produce distinct keys"


# --- Close behaviour (black-box) ---


def test_dated_path_close_allows_subsequent_write_to_open_new_handle(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: After process_record and close(), a subsequent process_record opens a new handle (new key).
    WHY: Lifecycle must release resources; observable outcome is that next write uses a new file."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    timestamps = iter([1.0, 2.0])

    def time_fn() -> float:
        return next(timestamps)

    subject = DatedPath(
        stream_name="my_stream",
        config=config,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1}, {})
    subject.close()
    subject.process_record({"id": 2}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 2
    keys = [p[1] for p in paths]
    assert keys[0] != keys[1]


# --- Current key property ---


def test_dated_path_current_key_empty_before_first_write(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Before any process_record, current_key is empty (or as specified by base contract).
    WHY: Property contract for GCSSink.key_name delegation."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    subject = DatedPath(
        stream_name="my_stream",
        config=config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    assert subject.current_key == ""


def test_dated_path_current_key_equals_key_passed_to_open_after_one_record(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: After processing one record, current_key equals the key used for the write (key passed to open).
    WHY: key_name delegation will work after task 06."""
    config = {"bucket_name": "test-bucket", "hive_partitioned": True}
    subject = DatedPath(
        stream_name="my_stream",
        config=config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    assert subject.current_key == paths[0][1]
