"""Tests for BasePathPattern: key prefix normalization and effective key template.

Black-box: assert on returned strings only; no call counts or log assertions.
"""

import io
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

from target_gcs.paths.base import (
    DEFAULT_KEY_NAMING_CONVENTION,
    DEFAULT_KEY_NAMING_CONVENTION_HIVE,
    BasePathPattern,
)


class _MinimalPattern(BasePathPattern):
    """Minimal concrete subclass so BasePathPattern can be instantiated in tests."""

    def process_record(self, record: dict, context: dict) -> None:
        pass

    def close(self) -> None:
        pass


def _build_pattern(
    config: dict[str, Any] | None = None,
    time_fn: Any = None,
    date_fn: Any = None,
) -> _MinimalPattern:
    """Build a minimal pattern with the given config (config file contents)."""
    cfg = config or {}
    default = {"bucket_name": "test-bucket"}
    merged = {**default, **cfg}
    return _MinimalPattern(
        target=None,
        stream_name="my_stream",
        schema={"properties": {}},
        key_properties=[],
        config=merged,
        time_fn=time_fn,
        date_fn=date_fn,
        storage_client=None,
    )


# --- apply_key_prefix_and_normalize ---


def test_apply_key_prefix_and_normalize_no_prefix_returns_normalized_base():
    """WHAT: With no key_prefix, base is returned normalized (no leading slash, no double slashes).
    WHY: GCS keys must be valid; normalization is shared behaviour."""
    subject = _build_pattern()
    result = subject.apply_key_prefix_and_normalize("stream/part/file.jsonl")
    assert result == "stream/part/file.jsonl"


def test_apply_key_prefix_and_normalize_strips_leading_slash_from_base():
    """WHAT: Base with leading slash is normalized so result has no leading slash.
    WHY: GCS object keys must not start with /."""
    subject = _build_pattern()
    result = subject.apply_key_prefix_and_normalize("/stream/file.jsonl")
    assert result == "stream/file.jsonl"
    assert not result.startswith("/")


def test_apply_key_prefix_and_normalize_collapses_double_slashes():
    """WHAT: Internal double slashes in base are collapsed to single slash.
    WHY: Valid key shape; consistent with GCSSink behaviour."""
    subject = _build_pattern()
    result = subject.apply_key_prefix_and_normalize("stream//part//file.jsonl")
    assert result == "stream/part/file.jsonl"
    assert "//" not in result


def test_apply_key_prefix_and_normalize_with_prefix_prepends_and_normalizes():
    """WHAT: When key_prefix is set, result is prefix + / + base, normalized.
    WHY: User prefix must be applied; output must still have no leading slash or //."""
    subject = _build_pattern({"key_prefix": "my/prefix"})
    result = subject.apply_key_prefix_and_normalize("stream/file.jsonl")
    assert result == "my/prefix/stream/file.jsonl"


def test_apply_key_prefix_and_normalize_with_prefix_and_slash_in_base_normalizes():
    """WHAT: Prefix + base with leading slash or // still yields normalized key.
    WHY: Full path must be normalized regardless of prefix."""
    subject = _build_pattern({"key_prefix": "p"})
    result = subject.apply_key_prefix_and_normalize("/a//b.jsonl")
    assert result == "p/a/b.jsonl"
    assert not result.startswith("/")
    assert "//" not in result


# --- get_effective_key_template ---


def test_get_effective_key_template_returns_user_template_when_set():
    """WHAT: get_effective_key_template returns key_naming_convention when set and non-empty.
    WHY: User override must take precedence over defaults."""
    subject = _build_pattern(
        {"key_naming_convention": "custom/{stream}/dt={partition_date}.jsonl"}
    )
    assert (
        subject.get_effective_key_template()
        == "custom/{stream}/dt={partition_date}.jsonl"
    )


def test_get_effective_key_template_returns_hive_default_when_hive_partitioned_and_no_user_template():
    """WHAT: When hive_partitioned is true and key_naming_convention omitted, returns DEFAULT_KEY_NAMING_CONVENTION_HIVE.
    WHY: Hive-style default must apply when Hive partitioning is enabled."""
    subject = _build_pattern({"hive_partitioned": True})
    assert subject.get_effective_key_template() == DEFAULT_KEY_NAMING_CONVENTION_HIVE


def test_get_effective_key_template_returns_non_partition_default_when_neither_set():
    """WHAT: When neither key_naming_convention nor hive_partitioned is set, returns DEFAULT_KEY_NAMING_CONVENTION.
    WHY: Non-partition default must apply when not using Hive partitioning."""
    subject = _build_pattern()
    assert subject.get_effective_key_template() == DEFAULT_KEY_NAMING_CONVENTION


def test_get_effective_key_template_empty_user_template_uses_default():
    """WHAT: When key_naming_convention is empty or whitespace-only, effective template uses default (hive or non-hive).
    WHY: Empty user value must not override; config semantics match GCSSink."""
    subject_non_hive = _build_pattern({"key_naming_convention": "   "})
    assert (
        subject_non_hive.get_effective_key_template() == DEFAULT_KEY_NAMING_CONVENTION
    )
    subject_hive = _build_pattern(
        {"key_naming_convention": "", "hive_partitioned": True}
    )
    assert (
        subject_hive.get_effective_key_template() == DEFAULT_KEY_NAMING_CONVENTION_HIVE
    )


# --- constants and instantiation ---


def test_constants_match_expected_values():
    """WHAT: DEFAULT_KEY_NAMING_CONVENTION and DEFAULT_KEY_NAMING_CONVENTION_HIVE have expected template strings.
    WHY: Base is single source of truth for key template defaults."""
    assert DEFAULT_KEY_NAMING_CONVENTION == "{stream}_{timestamp}.{format}"
    assert (
        DEFAULT_KEY_NAMING_CONVENTION_HIVE
        == "{stream}/{partition_date}/{timestamp}.{format}"
    )


def test_minimal_pattern_has_current_key_property():
    """WHAT: Base exposes current_key (or key_name) returning _key_name so callers can delegate.
    WHY: GCSSink will delegate key_name to path pattern's current key."""
    subject = _build_pattern()
    assert subject.current_key == ""
    subject._key_name = "some/key.jsonl"
    assert subject.current_key == "some/key.jsonl"


# --- write_record_as_jsonl ---


def test_write_record_as_jsonl_writes_one_jsonl_line_to_handle():
    """WHAT: write_record_as_jsonl writes the record as one JSONL line (orjson, newline) to _current_handle.
    WHY: Shared serialization must match GCSSink and support Decimal via _json_default."""
    subject = _build_pattern()
    subject._current_handle = io.BytesIO()
    record = {"id": 1, "name": "a"}
    subject.write_record_as_jsonl(record)
    raw = subject._current_handle.getvalue().decode("utf-8")
    assert raw.endswith("\n")
    assert raw.strip() == raw.rstrip("\n")
    import orjson

    assert orjson.loads(raw.strip()) == record


def test_write_record_as_jsonl_serializes_decimal_as_numeric():
    """WHAT: Record containing Decimal is serialized as numeric (float) in JSONL output.
    WHY: orjson does not natively serialize Decimal; _json_default enables correct output."""
    subject = _build_pattern()
    subject._current_handle = io.BytesIO()
    record = {"value": Decimal("12.34")}
    subject.write_record_as_jsonl(record)
    raw = subject._current_handle.getvalue().decode("utf-8")
    import orjson

    loaded = orjson.loads(raw.strip())
    assert loaded["value"] == 12.34
    assert isinstance(loaded["value"], (int, float))


# --- flush_and_close_handle ---


def test_flush_and_close_handle_flushes_closes_and_clears_handle():
    """WHAT: flush_and_close_handle flushes (if supported), closes the handle, and sets _current_handle to None.
    WHY: Subclasses rely on this for rotation and close; must be safe when handle has flush."""
    subject = _build_pattern()
    mock_handle = MagicMock()
    subject._current_handle = mock_handle
    subject.flush_and_close_handle()
    mock_handle.flush.assert_called_once()
    mock_handle.close.assert_called_once()
    assert subject._current_handle is None


def test_flush_and_close_handle_without_flush_does_not_raise():
    """WHAT: When _current_handle has no flush attribute, flush_and_close_handle still closes and clears.
    WHY: Handles without flush must not raise; behaviour mirrors GCSSink."""
    subject = _build_pattern()
    mock_handle = MagicMock(spec=["close", "write"])
    del mock_handle.flush
    subject._current_handle = mock_handle
    subject.flush_and_close_handle()
    mock_handle.close.assert_called_once()
    assert subject._current_handle is None


# --- maybe_rotate_if_at_limit (under limit) ---


def test_maybe_rotate_if_at_limit_under_limit_does_not_close_or_increment():
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


# --- maybe_rotate_if_at_limit (at limit) ---


def test_maybe_rotate_if_at_limit_at_limit_closes_and_increments_chunk_index():
    """WHAT: When record count reaches max_records_per_file, handle is closed, _chunk_index incremented, _records_written_in_current_file reset, _current_timestamp refreshed.
    WHY: Shared rotation behaviour for all patterns."""
    fixed_time = 2000.0
    subject = _build_pattern(
        {"max_records_per_file": 2},
        time_fn=lambda: fixed_time,
    )
    subject._records_written_in_current_file = 2
    mock_handle = MagicMock()
    subject._current_handle = mock_handle
    subject._chunk_index = 0
    subject._current_timestamp = None
    subject.maybe_rotate_if_at_limit()
    mock_handle.flush.assert_called_once()
    mock_handle.close.assert_called_once()
    assert subject._current_handle is None
    assert subject._chunk_index == 1
    assert subject._records_written_in_current_file == 0
    assert subject._current_timestamp == round(fixed_time)


# --- get_chunk_format_map ---


def test_get_chunk_format_map_returns_stream_date_timestamp_format():
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
    assert m["timestamp"] == 12346  # rounded
    assert m["format"] == "jsonl"


def test_get_chunk_format_map_includes_chunk_index_when_chunking_enabled():
    """WHAT: When max_records_per_file > 0, get_chunk_format_map includes chunk_index.
    WHY: Key template uses chunk_index for -0, -1 suffix when chunking."""
    subject = _build_pattern({"max_records_per_file": 10})
    subject._chunk_index = 2
    m = subject.get_chunk_format_map()
    assert "chunk_index" in m
    assert m["chunk_index"] == 2


def test_get_chunk_format_map_omits_chunk_index_when_chunking_disabled():
    """WHAT: When max_records_per_file is 0 or unset, get_chunk_format_map does not include chunk_index.
    WHY: Single-file mode does not use chunk index in key."""
    subject = _build_pattern()
    m = subject.get_chunk_format_map()
    assert "chunk_index" not in m


# --- chunk index in key ---


def test_chunk_index_in_key_template_produces_suffix_before_extension():
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
