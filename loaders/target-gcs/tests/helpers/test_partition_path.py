"""Tests for get_partition_path_from_record: partition path resolution from record date field."""

from datetime import datetime

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
