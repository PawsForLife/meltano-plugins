"""Tests for get_partition_path_from_record: partition path resolution from record date field."""

from datetime import datetime

import pytest

from target_gcs.helpers import get_partition_path_from_record

# Fixed fallback date for deterministic partition resolution tests (no datetime.today() in tests).
FALLBACK_DATE = datetime(2024, 3, 11)
DEFAULT_HIVE_FORMAT = "year=%Y/month=%m/day=%d"


def test_partition_path_valid_iso_date_in_field():
    """Valid ISO date in partition_date_field yields Hive-style path. WHAT: Parsed date is formatted with default Hive format. WHY: Core behaviour for partition path from date string."""
    result = get_partition_path_from_record(
        record={"created_at": "2024-03-11"},
        partition_date_field="created_at",
        partition_date_format=DEFAULT_HIVE_FORMAT,
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=11"


def test_partition_path_valid_iso_datetime_in_field():
    """Valid ISO datetime in field yields date-only partition path. WHAT: Datetime is parsed and date part used for path. WHY: Common API format must be supported."""
    result = get_partition_path_from_record(
        record={"created_at": "2024-03-11T12:00:00"},
        partition_date_field="created_at",
        partition_date_format=DEFAULT_HIVE_FORMAT,
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=11"


def test_partition_path_missing_field_uses_fallback():
    """Missing partition_date_field in record yields fallback_date formatted path. WHAT: Fallback when field absent. WHY: No crash; predictable path."""
    result = get_partition_path_from_record(
        record={"other": "value"},
        partition_date_field="created_at",
        partition_date_format=DEFAULT_HIVE_FORMAT,
        fallback_date=FALLBACK_DATE,
    )
    assert result == FALLBACK_DATE.strftime(DEFAULT_HIVE_FORMAT)


def test_partition_path_invalid_value_uses_fallback():
    """Non-date string in partition_date_field yields fallback path. WHAT: Unparseable value uses fallback. WHY: Robustness against bad data."""
    result = get_partition_path_from_record(
        record={"created_at": "not-a-date"},
        partition_date_field="created_at",
        partition_date_format=DEFAULT_HIVE_FORMAT,
        fallback_date=FALLBACK_DATE,
    )
    assert result == FALLBACK_DATE.strftime(DEFAULT_HIVE_FORMAT)


def test_partition_path_custom_format():
    """Custom partition_date_format is applied to parsed date. WHAT: Configurable format produces matching path. WHY: Flexibility for different Hive layouts."""
    custom_format = "day=%d/month=%m"
    result = get_partition_path_from_record(
        record={"created_at": "2024-03-11"},
        partition_date_field="created_at",
        partition_date_format=custom_format,
        fallback_date=FALLBACK_DATE,
    )
    assert result == "day=11/month=03"


@pytest.mark.xfail(
    reason="Requires Task 05 dateutil parsing; current code uses fromisoformat/strptime only."
)
def test_partition_path_slash_separated_date_yields_hive_path():
    """Slash-separated date string (dateutil-only) yields Hive path from parsed date. WHAT: Format 'YYYY/MM/DD' is parsed and path uses that date. WHY: After Task 05 dateutil will support this; current code falls back so we assert a different day (15) so test fails until then."""
    result = get_partition_path_from_record(
        record={"created_at": "2024/03/15"},
        partition_date_field="created_at",
        partition_date_format=DEFAULT_HIVE_FORMAT,
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=15"


@pytest.mark.xfail(
    reason="Requires Task 05 dateutil parsing; current code uses fromisoformat/strptime only."
)
def test_partition_path_rfc_style_datetime_yields_hive_path():
    """RFC-style datetime string (dateutil-only) yields Hive path from parsed date. WHAT: Format 'DD Mon YYYY HH:MM:SS' is parsed and path uses that date. WHY: Common in logs/APIs; dateutil will support it in Task 05; assert day 15 so test fails with current fallback."""
    result = get_partition_path_from_record(
        record={"created_at": "15 Mar 2024 12:00:00"},
        partition_date_field="created_at",
        partition_date_format=DEFAULT_HIVE_FORMAT,
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=15"


@pytest.mark.xfail(
    reason="Requires Task 05 dateutil parsing; current code uses fromisoformat/strptime only."
)
def test_partition_path_long_month_name_yields_hive_path():
    """Long month name date string (dateutil-only) yields Hive path from parsed date. WHAT: Format 'Month DD, YYYY' is parsed and path uses that date. WHY: Broader format support after Task 05; assert day 20 so test fails with current fallback."""
    result = get_partition_path_from_record(
        record={"created_at": "March 20, 2024"},
        partition_date_field="created_at",
        partition_date_format=DEFAULT_HIVE_FORMAT,
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=20"
