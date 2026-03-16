"""Tests for SimplePath: key generation, one handle, rotation at limit, close, current_key.

Black-box: assert on keys passed to open, record count per file (via keys), and close behaviour only.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from ...conftest import build_simple_path
from ...test_helpers import key_from_open_call

if TYPE_CHECKING:
    from tests.fixtures.recording_gcs_client import RecordingGCSClient

# --- Key generation (single path) ---


def test_path_from_path_simple_constant() -> None:
    """WHAT: After processing one record, the key passed to open matches {stream}/{date}/{timestamp}.jsonl.
    WHY: Path is built from PATH_SIMPLE at init; full key = path + filename from full_key()."""
    fixed_ts = 12345.0
    fixed_dt = datetime(2024, 3, 11)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.simple.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = build_simple_path(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1, "name": "a"}, {})
        assert mock_open.call_count == 1
        key = key_from_open_call(mock_open.call_args[0])
        assert key == "my_stream/2024-03-11/12345.jsonl"


def test_filename_is_timestamp_jsonl() -> None:
    """WHAT: The filename segment (last path component) is {timestamp}.jsonl.
    WHY: filename_for_current_file uses FILENAME_TEMPLATE; full_key joins path and filename."""
    fixed_ts = 99999.0
    fixed_dt = datetime(2024, 1, 15)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.simple.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = build_simple_path(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1}, {})
        key = key_from_open_call(mock_open.call_args[0])
        assert key.endswith("/99999.jsonl")
        filename = key.split("/")[-1]
        assert filename == "99999.jsonl"


def test_uses_date_format_from_config() -> None:
    """WHAT: With date_format='%Y', path contains year only (e.g. my_stream/2024/12345.jsonl).
    WHY: Path built at init uses config date_format for the date token."""
    fixed_ts = 12345.0
    fixed_dt = datetime(2024, 3, 11)
    mock_handle = MagicMock()
    with patch(
        "target_gcs.paths.simple.smart_open.open", return_value=mock_handle
    ) as mock_open:
        subject = build_simple_path(
            config={"bucket_name": "test-bucket", "date_format": "%Y"},
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1}, {})
        key = key_from_open_call(mock_open.call_args[0])
        assert key == "my_stream/2024/12345.jsonl"


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
        subject = build_simple_path(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        for i in range(5):
            subject.process_record({"id": i}, {})
        assert mock_open.call_count == 1
        keys = [key_from_open_call(c[0]) for c in mock_open.call_args_list]
        assert len(set(keys)) == 1


# --- Rotation at limit ---


def test_rotation_at_limit_uses_timestamp_only() -> None:
    """WHAT: With max_records_per_file=2, processing 5 records opens multiple handles; keys differ by timestamp only.
    WHY: Chunking uses timestamp-only filenames (no chunk_index); path prefix is shared."""
    timestamps = iter([1000.0, 1001.0, 1002.0, 1003.0, 1004.0, 1005.0, 1006.0, 1007.0])
    mock_handles = [MagicMock(), MagicMock(), MagicMock()]
    with patch(
        "target_gcs.paths.simple.smart_open.open", side_effect=mock_handles
    ) as mock_open:
        subject = build_simple_path(
            config={"bucket_name": "test-bucket", "max_records_per_file": 2},
            time_fn=lambda: next(timestamps),
            date_fn=lambda: datetime(2024, 3, 11),
        )
        for i in range(5):
            subject.process_record({"id": i}, {})
        assert mock_open.call_count >= 2
        keys = [key_from_open_call(c[0]) for c in mock_open.call_args_list]
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


def test_simple_path_close_allows_subsequent_write_to_open_new_handle() -> None:
    """WHAT: After processing records and close(), a subsequent process_record opens a new handle (new key).
    WHY: Lifecycle must release resources; observable outcome is that next write uses a new file."""
    timestamps = iter([1.0, 2.0])
    fixed_dt = datetime(2024, 1, 1)
    mock_handles = [MagicMock(), MagicMock()]
    with patch(
        "target_gcs.paths.simple.smart_open.open", side_effect=mock_handles
    ) as mock_open:
        subject = build_simple_path(
            time_fn=lambda: next(timestamps),
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1}, {})
        key_before = key_from_open_call(mock_open.call_args[0])
        subject.close()
        subject.process_record({"id": 2}, {})
        keys = [key_from_open_call(c[0]) for c in mock_open.call_args_list]
    assert mock_open.call_count == 2
    assert keys[0] != keys[1]
    assert key_before == keys[0]


# --- Current key property ---


def test_simple_path_current_key_empty_before_first_write() -> None:
    """WHAT: Before any record is processed, current_key returns empty string.
    WHY: GCSSink can delegate key_name to pattern; empty until first write."""
    subject = build_simple_path()
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
        subject = build_simple_path(
            time_fn=lambda: fixed_ts,
            date_fn=lambda: fixed_dt,
        )
        subject.process_record({"id": 1}, {})
        opened_key = key_from_open_call(mock_open.call_args[0])
        assert subject.current_key == opened_key


# --- Recording client integration (no patch; real smart_open) ---


def test_simple_path_with_recording_client_stores_path_and_content(
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: SimplePath with recording_storage_client writes through real smart_open; path and content are readable via get_written_paths and get_written_content.
    WHY: Validates recording client works end-to-end with path code; no smart_open patch."""
    fixed_ts = 12345.0
    fixed_dt = datetime(2024, 3, 11)
    subject = build_simple_path(
        time_fn=lambda: fixed_ts,
        date_fn=lambda: fixed_dt,
        storage_client=recording_storage_client,
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
    assert b'{"id":1,"name":"a"}' in content or b'{"id":1,"name":"a"}' in content
    assert b'{"id":2,"name":"b"}' in content or b'{"id":2,"name":"b"}' in content
