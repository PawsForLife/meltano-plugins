"""Tests for BasePathPattern: key prefix normalization and effective key template.

Black-box: assert on returned strings and observable state only; no call counts or log assertions.
"""

from __future__ import annotations

import io
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

from target_gcs.paths.base import BasePathPattern

# Fallback templates for _MinimalPattern until task 04 removes key_template.
_DEFAULT_TEMPLATE = "{stream}_{timestamp}.{format}"
_DEFAULT_TEMPLATE_HIVE = "{stream}/{partition_date}/{timestamp}.{format}"


class _MinimalPattern(BasePathPattern):
    """Minimal concrete subclass so BasePathPattern can be instantiated in tests."""

    @property
    def key_template(self) -> str:
        conv = (self.config.get("key_naming_convention") or "").strip()
        if conv:
            return conv
        return (
            _DEFAULT_TEMPLATE_HIVE
            if self.config.get("hive_partitioned")
            else _DEFAULT_TEMPLATE
        )

    def process_record(self, record: dict, context: dict) -> None:
        pass

    def close(self) -> None:
        pass


def _build_pattern(
    config: dict[str, Any] | None = None,
    time_fn: Any = None,
    date_fn: Any = None,
) -> _MinimalPattern:
    """Build a minimal pattern with the given config."""
    cfg = config or {}
    merged = {**{"bucket_name": "test-bucket"}, **cfg}
    return _MinimalPattern(
        stream_name="my_stream",
        config=merged,
        time_fn=time_fn,
        date_fn=date_fn,
        storage_client=None,
    )


# --- apply_key_prefix_and_normalize ---


def test_apply_key_prefix_and_normalize_no_prefix_returns_normalized_base() -> None:
    """WHAT: With no key_prefix, base is returned normalized (no leading slash, no double slashes).
    WHY: GCS keys must be valid; normalization is shared behaviour."""
    subject = _build_pattern()
    result = subject.apply_key_prefix_and_normalize("stream/part/file.jsonl")
    assert result == "stream/part/file.jsonl"


def test_apply_key_prefix_and_normalize_strips_leading_slash_from_base() -> None:
    """WHAT: Base with leading slash is normalized so result has no leading slash.
    WHY: GCS object keys must not start with /."""
    subject = _build_pattern()
    result = subject.apply_key_prefix_and_normalize("/stream/file.jsonl")
    assert result == "stream/file.jsonl"
    assert not result.startswith("/")


def test_apply_key_prefix_and_normalize_collapses_double_slashes() -> None:
    """WHAT: Internal double slashes in base are collapsed to single slash.
    WHY: Valid key shape; consistent with GCSSink behaviour."""
    subject = _build_pattern()
    result = subject.apply_key_prefix_and_normalize("stream//part//file.jsonl")
    assert result == "stream/part/file.jsonl"
    assert "//" not in result


def test_apply_key_prefix_and_normalize_with_prefix_prepends_and_normalizes() -> None:
    """WHAT: When key_prefix is set, result is prefix + / + base, normalized.
    WHY: User prefix must be applied; output must still have no leading slash or //."""
    subject = _build_pattern({"key_prefix": "my/prefix"})
    result = subject.apply_key_prefix_and_normalize("stream/file.jsonl")
    assert result == "my/prefix/stream/file.jsonl"


def test_apply_key_prefix_and_normalize_with_prefix_and_slash_in_base_normalizes() -> (
    None
):
    """WHAT: Prefix + base with leading slash or // still yields normalized key.
    WHY: Full path must be normalized regardless of prefix."""
    subject = _build_pattern({"key_prefix": "p"})
    result = subject.apply_key_prefix_and_normalize("/a//b.jsonl")
    assert result == "p/a/b.jsonl"
    assert not result.startswith("/")
    assert "//" not in result


# --- current_key ---


def test_minimal_pattern_has_current_key_property() -> None:
    """WHAT: Base exposes current_key returning _key_name so callers can delegate.
    WHY: GCSSink will delegate key_name to path pattern's current key."""
    subject = _build_pattern()
    assert subject.current_key == ""
    subject._key_name = "some/key.jsonl"
    assert subject.current_key == "some/key.jsonl"


# --- write_record_as_jsonl ---


def test_write_record_as_jsonl_writes_one_jsonl_line_to_handle() -> None:
    """WHAT: write_record_as_jsonl writes the record as one JSONL line (orjson, newline) to _current_handle.
    WHY: Shared serialization must match GCSSink and support Decimal via _json_default."""
    subject = _build_pattern()
    subject._current_handle = io.BytesIO()
    record: dict[str, Any] = {"id": 1, "name": "a"}
    subject.write_record_as_jsonl(record)
    raw = subject._current_handle.getvalue().decode("utf-8")
    assert raw.endswith("\n")
    assert raw.strip() == raw.rstrip("\n")
    import orjson

    assert orjson.loads(raw.strip()) == record


def test_write_record_as_jsonl_serializes_decimal_as_numeric() -> None:
    """WHAT: Record containing Decimal is serialized as numeric (float) in JSONL output.
    WHY: orjson does not natively serialize Decimal; _json_default enables correct output."""
    subject = _build_pattern()
    subject._current_handle = io.BytesIO()
    record: dict[str, Any] = {"value": Decimal("12.34")}
    subject.write_record_as_jsonl(record)
    raw = subject._current_handle.getvalue().decode("utf-8")
    import orjson

    loaded = orjson.loads(raw.strip())
    assert loaded["value"] == 12.34
    assert isinstance(loaded["value"], (int, float))


# --- flush_and_close_handle (black-box: assert observable state only) ---


def test_flush_and_close_handle_clears_current_handle() -> None:
    """WHAT: After flush_and_close_handle, _current_handle is None so next write uses a new handle.
    WHY: Subclasses rely on this for rotation and close; observable outcome is handle cleared."""
    subject = _build_pattern()
    subject._current_handle = MagicMock()
    subject.flush_and_close_handle()
    assert subject._current_handle is None


def test_flush_and_close_handle_without_flush_does_not_raise() -> None:
    """WHAT: When _current_handle has no flush attribute, flush_and_close_handle still closes and clears.
    WHY: Handles without flush must not raise; behaviour mirrors GCSSink."""
    subject = _build_pattern()
    mock_handle = MagicMock(spec=["close", "write"])
    del mock_handle.flush  # type: ignore[attr-defined]
    subject._current_handle = mock_handle
    subject.flush_and_close_handle()
    assert subject._current_handle is None


# --- maybe_rotate_if_at_limit ---


def test_maybe_rotate_if_at_limit_under_limit_does_not_close_or_increment() -> None:
    """WHAT: When max_records_per_file is set and record count is below limit, handle stays open and chunk_index unchanged.
    WHY: Rotation must only occur at limit."""
    subject = _build_pattern({"max_records_per_file": 5})
    subject._current_handle = io.BytesIO()
    subject._time_fn = lambda: 1000.0
    for _ in range(3):
        subject.write_record_as_jsonl({"x": 1})
    subject.maybe_rotate_if_at_limit()
    assert subject._current_handle is not None
    assert subject._chunk_index == 0


def test_maybe_rotate_if_at_limit_at_limit_clears_handle_and_increments_chunk_index() -> (
    None
):
    """WHAT: When record count reaches max_records_per_file, handle is cleared, _chunk_index incremented, _records_written_in_current_file reset.
    WHY: Shared rotation behaviour for all patterns; assert observable state only."""
    fixed_time = 2000.0
    subject = _build_pattern(
        {"max_records_per_file": 2},
        time_fn=lambda: fixed_time,
    )
    subject._records_written_in_current_file = 2
    subject._current_handle = MagicMock()
    subject._chunk_index = 0
    subject._current_timestamp = None
    subject.maybe_rotate_if_at_limit()
    assert subject._current_handle is None
    assert subject._chunk_index == 1
    assert subject._records_written_in_current_file == 0
    assert subject._current_timestamp == round(fixed_time)


# --- get_chunk_format_map ---


def test_get_chunk_format_map_returns_stream_date_timestamp_format() -> None:
    """WHAT: get_chunk_format_map returns dict with stream, date, timestamp, format.
    WHY: Key building in subclasses uses this for template substitution."""
    from datetime import datetime

    fixed_dt = datetime(2024, 3, 11)
    subject = _build_pattern(
        {},
        time_fn=lambda: 12345.67,
        date_fn=lambda: fixed_dt,
    )
    subject._extraction_date = fixed_dt
    m = subject.get_chunk_format_map()
    assert m["stream"] == "my_stream"
    assert m["date"] == "2024-03-11"
    assert m["timestamp"] == 12346
    assert m["format"] == "jsonl"


def test_get_chunk_format_map_includes_chunk_index_when_chunking_enabled() -> None:
    """WHAT: When max_records_per_file > 0, get_chunk_format_map includes chunk_index.
    WHY: Key template uses chunk_index for -0, -1 suffix when chunking."""
    subject = _build_pattern({"max_records_per_file": 10})
    subject._chunk_index = 2
    m = subject.get_chunk_format_map()
    assert "chunk_index" in m
    assert m["chunk_index"] == 2


def test_get_chunk_format_map_omits_chunk_index_when_chunking_disabled() -> None:
    """WHAT: When max_records_per_file is 0 or unset, get_chunk_format_map does not include chunk_index.
    WHY: Single-file mode does not use chunk index in key."""
    subject = _build_pattern()
    m = subject.get_chunk_format_map()
    assert "chunk_index" not in m


# --- chunk index in key ---


def test_chunk_index_in_key_template_produces_suffix_before_extension() -> None:
    """WHAT: Key built from template and get_chunk_format_map contains -0, -1 before extension when chunking enabled.
    WHY: Validates the -{chunk_index} convention used by downstream patterns."""
    subject = _build_pattern({"max_records_per_file": 5})
    template = "{stream}_{timestamp}-{chunk_index}.{format}"
    subject._chunk_index = 0
    m = subject.get_chunk_format_map()
    m["timestamp"] = 1000
    key0 = template.format_map(m)
    assert "-0." in key0
    assert key0.endswith(".jsonl")
    subject._chunk_index = 1
    m1 = subject.get_chunk_format_map()
    m1["timestamp"] = 1000
    key1 = template.format_map(m1)
    assert "-1." in key1
    assert key1.endswith(".jsonl")
