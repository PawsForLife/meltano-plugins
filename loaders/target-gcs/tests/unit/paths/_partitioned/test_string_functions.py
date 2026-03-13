"""Tests for string_functions: date_as_partition and string_as_partition.

Black-box: assert on return values only; no internals or call counts.
"""

from __future__ import annotations

import importlib.util
from datetime import date, datetime
from pathlib import Path

import pytest

# Load string_functions directly to avoid paths/__init__.py imports
# (path modules still reference removed constants until tasks 05-07)
_pkg_root = Path(__file__).resolve().parents[4]
_spec = importlib.util.spec_from_file_location(
    "string_functions",
    _pkg_root / "target_gcs" / "paths" / "_partitioned" / "string_functions.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

date_as_partition = _mod.date_as_partition
string_as_partition = _mod.string_as_partition


# --- date_as_partition ---


def test_date_as_partition_returns_formatted_string_for_datetime() -> None:
    """WHAT: date_as_partition returns non-empty string in Hive date format for datetime input.
    WHY: Partition path construction depends on correct formatted date; datetime is a common input."""
    result = date_as_partition("dt", datetime(2024, 3, 15))
    assert result == "year=2024/month=03/day=15"
    assert len(result) > 0


def test_date_as_partition_returns_formatted_string_for_date() -> None:
    """WHAT: date_as_partition returns non-empty string in Hive date format for date input.
    WHY: Partition path construction supports native date objects."""
    result = date_as_partition("dt", date(2024, 3, 15))
    assert result == "year=2024/month=03/day=15"
    assert len(result) > 0


def test_date_as_partition_returns_formatted_string_for_parseable_string() -> None:
    """WHAT: date_as_partition returns non-empty string in Hive date format for parseable date string.
    WHY: Records often contain date strings; dateutil parses them for partition path."""
    result = date_as_partition("dt", "2024-03-15")
    assert result == "year=2024/month=03/day=15"
    assert len(result) > 0


def test_date_as_partition_invalid_type_raises() -> None:
    """WHAT: date_as_partition raises when field_value is neither datetime/date nor str.
    WHY: Invalid types cannot be formatted; explicit failure is preferable to implicit NameError."""
    with pytest.raises((ValueError, TypeError, NameError)):
        date_as_partition("dt", 12345)


# --- string_as_partition ---


def test_string_as_partition_returns_key_equals_value() -> None:
    """WHAT: string_as_partition returns field_name=value with slashes replaced by underscores.
    WHY: Hive partition segments use key=value; slashes must be path-safe."""
    result = string_as_partition("region", "eu")
    assert result == "region=eu"


def test_string_as_partition_replaces_slash_with_underscore() -> None:
    """WHAT: string_as_partition sanitizes value by replacing / with _.
    WHY: Slashes in partition values would break path structure."""
    result = string_as_partition("path", "a/b/c")
    assert result == "path=a_b_c"
