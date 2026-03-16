"""Tests for BasePathPattern: key prefix normalization, filename_for_current_file, full_key, rotation.

Black-box: assert on returned strings and observable state only; no call counts or log assertions.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

from target_gcs.paths.base import BasePathPattern
from tests.fixtures.recording_gcs_client import RecordingGCSClient


class _MinimalPattern(BasePathPattern):
    """Minimal concrete subclass so BasePathPattern can be instantiated in tests."""

    def process_record(self, record: dict, context: dict) -> None:
        pass

    def close(self) -> None:
        pass


# --- apply_key_prefix_and_normalize ---


def test_apply_key_prefix_and_normalize_no_prefix_returns_normalized_base(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: With no key_prefix, base is returned normalized (no leading slash, no double slashes).
    WHY: GCS keys must be valid; normalization is shared behaviour."""
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    result = subject.apply_key_prefix_and_normalize("stream/part/file.jsonl")
    assert result == "stream/part/file.jsonl"


def test_apply_key_prefix_and_normalize_strips_leading_slash_from_base(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Base with leading slash is normalized so result has no leading slash.
    WHY: GCS object keys must not start with /."""
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    result = subject.apply_key_prefix_and_normalize("/stream/file.jsonl")
    assert result == "stream/file.jsonl"
    assert not result.startswith("/")


def test_apply_key_prefix_and_normalize_collapses_double_slashes(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Internal double slashes in base are collapsed to single slash.
    WHY: Valid key shape; consistent with GCSSink behaviour."""
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    result = subject.apply_key_prefix_and_normalize("stream//part//file.jsonl")
    assert result == "stream/part/file.jsonl"
    assert "//" not in result


def test_apply_key_prefix_and_normalize_with_prefix_prepends_and_normalizes(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: When key_prefix is set, result is prefix + / + base, normalized.
    WHY: User prefix must be applied; output must still have no leading slash or //."""
    config = {"bucket_name": "test-bucket", "key_prefix": "my/prefix"}
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    result = subject.apply_key_prefix_and_normalize("stream/file.jsonl")
    assert result == "my/prefix/stream/file.jsonl"


def test_apply_key_prefix_and_normalize_with_prefix_and_slash_in_base_normalizes(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Prefix + base with leading slash or // still yields normalized key.
    WHY: Full path must be normalized regardless of prefix."""
    config = {"bucket_name": "test-bucket", "key_prefix": "p"}
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    result = subject.apply_key_prefix_and_normalize("/a//b.jsonl")
    assert result == "p/a/b.jsonl"
    assert not result.startswith("/")
    assert "//" not in result


# --- current_key ---


def test_minimal_pattern_has_current_key_property(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Base exposes current_key returning _key_name so callers can delegate.
    WHY: GCSSink will delegate key_name to path pattern's current key."""
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    assert subject.current_key == ""
    subject._key_name = "some/key.jsonl"
    assert subject.current_key == "some/key.jsonl"


# --- write_record_as_jsonl ---


def test_write_record_as_jsonl_writes_one_jsonl_line_to_handle(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: write_record_as_jsonl writes the record as one JSONL line (orjson, newline) to _current_handle.
    WHY: Shared serialization must match GCSSink and support Decimal via _json_default."""
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject._current_handle = io.BytesIO()
    record: dict[str, Any] = {"id": 1, "name": "a"}
    subject.write_record_as_jsonl(record)
    raw = subject._current_handle.getvalue().decode("utf-8")
    assert raw.endswith("\n")
    assert raw.strip() == raw.rstrip("\n")
    import orjson

    assert orjson.loads(raw.strip()) == record


def test_write_record_as_jsonl_serializes_decimal_as_numeric(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Record containing Decimal is serialized as numeric (float) in JSONL output.
    WHY: orjson does not natively serialize Decimal; _json_default enables correct output."""
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject._current_handle = io.BytesIO()
    record: dict[str, Any] = {"value": Decimal("12.34")}
    subject.write_record_as_jsonl(record)
    raw = subject._current_handle.getvalue().decode("utf-8")
    import orjson

    loaded = orjson.loads(raw.strip())
    assert loaded["value"] == 12.34
    assert isinstance(loaded["value"], (int, float))


# --- flush_and_close_handle (black-box: assert observable state only) ---


def test_flush_and_close_handle_clears_current_handle(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: After flush_and_close_handle, _current_handle is None so next write uses a new handle.
    WHY: Subclasses rely on this for rotation and close; observable outcome is handle cleared."""
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject._current_handle = MagicMock()
    subject.flush_and_close_handle()
    assert subject._current_handle is None


def test_flush_and_close_handle_without_flush_does_not_raise(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: When _current_handle has no flush attribute, flush_and_close_handle still closes and clears.
    WHY: Handles without flush must not raise; behaviour mirrors GCSSink."""
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    mock_handle = MagicMock(spec=["close", "write"])
    del mock_handle.flush  # type: ignore[attr-defined]
    subject._current_handle = mock_handle
    subject.flush_and_close_handle()
    assert subject._current_handle is None


# --- maybe_rotate_if_at_limit ---


def test_maybe_rotate_if_at_limit_under_limit_does_not_close(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: When max_records_per_file is set and record count is below limit, handle stays open.
    WHY: Rotation must only occur at limit."""
    config = {"bucket_name": "test-bucket", "max_records_per_file": 5}
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject._current_handle = io.BytesIO()
    subject._time_fn = lambda: 1000.0
    for _ in range(3):
        subject.write_record_as_jsonl({"x": 1})
    subject.maybe_rotate_if_at_limit()
    assert subject._current_handle is not None


# --- filename_for_current_file ---


def test_filename_for_current_file_returns_timestamp_jsonl(
    sample_config: dict,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: With time_fn=lambda: 12345, filename_for_current_file returns '12345.jsonl'.
    WHY: Core filename contract uses FILENAME_TEMPLATE with timestamp only (no chunk_index)."""
    def time_fn() -> float:
        return 12345.0

    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    result = subject.filename_for_current_file()
    assert result == "12345.jsonl"


def test_filename_for_current_file_uses_injected_time_fn(
    sample_config: dict,
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: Deterministic time_fn yields predictable filename; asserts DI for deterministic tests.
    WHY: Tests must be deterministic; time_fn injection enables this."""
    def time_fn() -> float:
        return 99999.0

    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    result = subject.filename_for_current_file()
    assert result == "99999.jsonl"


# --- full_key ---


def test_full_key_joins_path_and_filename(
    sample_config: dict,
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: full_key('a/b', 'c.jsonl') returns normalized key (path + filename, prefix applied).
    WHY: Key composition must join path and filename correctly."""
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=sample_config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    result = subject.full_key("a/b", "c.jsonl")
    assert result == "a/b/c.jsonl"


def test_full_key_applies_key_prefix(
    fixed_time_fn: Callable[[], float],
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: With key_prefix='x/y', full_key result starts with prefix.
    WHY: User prefix must be applied to composed key."""
    config = {"bucket_name": "test-bucket", "key_prefix": "x/y"}
    subject = _MinimalPattern(
        stream_name="my_stream",
        config=config,
        time_fn=fixed_time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    result = subject.full_key("stream/part", "123.jsonl")
    assert result.startswith("x/y/")
    assert "123.jsonl" in result


# --- maybe_rotate (timestamp-only, no chunk_index) ---


def test_maybe_rotate_resets_records_no_chunk_index(
    fixed_date: datetime,
    recording_storage_client: RecordingGCSClient,
) -> None:
    """WHAT: After rotate at max_records_per_file, next filename_for_current_file has timestamp; no chunk_index in key.
    WHY: Chunking uses timestamp-only filenames; rotation resets record count; filename has no -0/-1 suffix."""
    config = {"bucket_name": "test-bucket", "max_records_per_file": 2}

    def time_fn() -> float:
        return 2001.0

    subject = _MinimalPattern(
        stream_name="my_stream",
        config=config,
        time_fn=time_fn,
        storage_client=recording_storage_client,
        extraction_date=fixed_date,
    )
    subject._records_written_in_current_file = 2
    subject._current_handle = MagicMock()
    subject.maybe_rotate_if_at_limit()
    assert subject._current_handle is None
    assert subject._records_written_in_current_file == 0
    fn = subject.filename_for_current_file()
    assert fn == "2001.jsonl"
    assert "chunk" not in fn and "-0" not in fn and "-1" not in fn
