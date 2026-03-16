"""Tests for SimplePath: key generation, one handle, rotation at limit, close, current_key.

Black-box: assert on keys and content via RecordingGCSClient get_written_paths/get_written_content.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from target_gcs.paths import SimplePath
from tests.fixtures.recording_gcs_client import RecordingGCSClient

# --- Key generation (single path) ---


def test_path_from_path_simple_constant(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: After processing one record, the key written matches {stream}/{date}/{timestamp}.jsonl.
    WHY: Path is built from PATH_SIMPLE at init; full key = path + filename from full_key()."""
    subject = SimplePath(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1, "name": "a"}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    bucket, key = paths[0]
    assert key == "my_stream/2024-03-11/12345.jsonl"


def test_filename_is_timestamp_jsonl(
    sample_config: dict,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: The filename segment (last path component) is {timestamp}.jsonl.
    WHY: filename_for_current_file uses FILENAME_TEMPLATE; full_key joins path and filename."""

    def time_fn() -> float:
        return 99999.0

    subject = SimplePath(
        stream_name="my_stream",
        config=sample_config,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    key = paths[0][1]
    assert key.endswith("/99999.jsonl")
    filename = key.split("/")[-1]
    assert filename == "99999.jsonl"


def test_uses_date_format_from_config(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: With date_format='%Y', path contains year only (e.g. my_stream/2024/12345.jsonl).
    WHY: Path built at init uses config date_format for the date token."""
    config = {"bucket_name": "test-bucket", "date_format": "%Y"}
    subject = SimplePath(
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
    assert paths[0][1] == "my_stream/2024/12345.jsonl"


# --- One handle (no chunking) ---


def test_simple_path_one_handle_when_no_chunking_uses_single_key(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: With max_records_per_file=0 (or unset), processing multiple records opens exactly one handle with one key.
    WHY: No spurious rotation when chunking is disabled."""
    subject = SimplePath(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    for i in range(5):
        subject.process_record({"id": i}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    keys = [p[1] for p in paths]
    assert len(set(keys)) == 1


# --- Rotation at limit ---


def test_rotation_at_limit_uses_timestamp_only(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: With max_records_per_file=2, processing 5 records opens multiple handles; keys differ by timestamp only.
    WHY: Chunking uses timestamp-only filenames (no chunk_index); path prefix is shared."""
    config = {"bucket_name": "test-bucket", "max_records_per_file": 2}
    timestamps = iter([1000.0, 1001.0, 1002.0, 1003.0, 1004.0, 1005.0, 1006.0, 1007.0])

    def time_fn() -> float:
        return next(timestamps)

    subject = SimplePath(
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
    path_prefix = "my_stream/2024-03-11"
    for key in keys:
        assert key.startswith(path_prefix), f"key {key} must share path prefix"
    filenames = [k.split("/")[-1] for k in keys]
    assert all(f.endswith(".jsonl") for f in filenames)
    assert all(f.replace(".jsonl", "").isdigit() for f in filenames), (
        "filenames must be {timestamp}.jsonl (no chunk_index)"
    )


# --- Close behaviour (black-box: after close, next write uses new handle) ---


def test_simple_path_close_allows_subsequent_write_to_open_new_handle(
    sample_config: dict,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: After processing records and close(), a subsequent process_record opens a new handle (new key).
    WHY: Lifecycle must release resources; observable outcome is that next write uses a new file."""
    timestamps = iter([1.0, 2.0])

    def time_fn() -> float:
        return next(timestamps)

    subject = SimplePath(
        stream_name="my_stream",
        config=sample_config,
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


def test_simple_path_current_key_empty_before_first_write(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Before any record is processed, current_key returns empty string.
    WHY: GCSSink can delegate key_name to pattern; empty until first write."""
    subject = SimplePath(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    assert subject.current_key == ""


def test_simple_path_current_key_equals_key_passed_to_open_after_one_record(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: After processing one record, current_key returns the same key that was passed to open.
    WHY: GCSSink can delegate key_name to pattern for tests and introspection."""
    subject = SimplePath(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) == 1
    assert subject.current_key == paths[0][1]


# --- Recording client integration ---


def test_simple_path_with_recording_client_stores_path_and_content(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: SimplePath with recording_storage_client writes through smart_open; path and content readable via get_written_paths and get_written_content.
    WHY: Validates recording client works end-to-end with path code; no smart_open patch."""
    subject = SimplePath(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject.process_record({"id": 1, "name": "a"}, {})
    subject.process_record({"id": 2, "name": "b"}, {})
    subject.close()
    paths = recording_storage_client.get_written_paths()
    assert len(paths) >= 1
    bucket, key = paths[0]
    assert bucket == "test-bucket"
    assert key == "my_stream/2024-03-11/12345.jsonl"
    content = recording_storage_client.get_written_content(bucket, key)
    assert content is not None
    assert b'"id":1,"name":"a"' in content
    assert b'"id":2,"name":"b"' in content
