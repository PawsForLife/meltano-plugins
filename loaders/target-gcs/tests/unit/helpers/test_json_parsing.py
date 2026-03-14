"""Tests for _json_default: Decimal serialization and non-serializable type handling."""

from decimal import Decimal

import pytest

from target_gcs.helpers import _json_default


def test_json_default_decimal_returns_float():
    """Decimal is converted to float for JSON serialization. WHAT: _json_default(Decimal) returns the float value. WHY: orjson does not natively serialize Decimal; helper enables JSONL output with numeric values."""
    result = _json_default(Decimal("12.34"))
    assert result == 12.34


def test_json_default_non_decimal_raises_type_error():
    """Non-Decimal non-JSON-serializable type raises TypeError. WHAT: _json_default(object()) raises TypeError. WHY: Only Decimal is coerced; other types must not be silently converted."""
    with pytest.raises(TypeError):
        _json_default(object())
