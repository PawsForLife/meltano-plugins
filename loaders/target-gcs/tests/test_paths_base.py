"""Tests for BasePathPattern: key prefix normalization and effective key template.

Black-box: assert on returned strings only; no call counts or log assertions.
"""

from typing import Any

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
        time_fn=None,
        date_fn=None,
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
