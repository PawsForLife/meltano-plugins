"""Unit tests for test_helpers.key_from_open_call.

WHAT: key_from_open_call extracts the GCS object key from the positional-args tuple
of a smart_open.open call (e.g. gs://bucket/path/to/key -> path/to/key).
WHY: Centralises key extraction so path and sink tests can share one implementation.
"""

from __future__ import annotations

import pytest

from tests.test_helpers import key_from_open_call


def test_key_from_open_call_multi_segment_returns_key_after_bucket() -> None:
    """WHAT: Standard gs://bucket/path/to/key URI returns path/to/key.
    WHY: Normal multi-segment keys must be extracted for assertions in path/sink tests."""
    positional_args: tuple[str, ...] = ("gs://bucket/path/to/key",)
    assert key_from_open_call(positional_args) == "path/to/key"


def test_key_from_open_call_single_segment_returns_key() -> None:
    """WHAT: Single-segment gs://bucket/key returns key.
    WHY: Single-segment keys are valid and must be handled."""
    positional_args: tuple[str, ...] = ("gs://bucket/key",)
    assert key_from_open_call(positional_args) == "key"


def test_key_from_open_call_trailing_slash_preserves_slash() -> None:
    """WHAT: gs://bucket/foo/ returns foo/ (trailing slash preserved).
    WHY: Behaviour matches existing split(\"/\", 3)[-1]; document edge case."""
    positional_args: tuple[str, ...] = ("gs://bucket/foo/",)
    assert key_from_open_call(positional_args) == "foo/"


def test_key_from_open_call_empty_tuple_raises_index_error() -> None:
    """WHAT: Empty positional-args tuple raises IndexError.
    WHY: Contract is positional-args tuple with at least one element (the URI)."""
    with pytest.raises(IndexError):
        key_from_open_call(())
