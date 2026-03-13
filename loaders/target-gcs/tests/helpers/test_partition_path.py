"""Tests for partition path helpers: get_partition_path_from_record and get_partition_path_from_schema_and_record."""

import warnings
from datetime import datetime

import pytest
from dateutil.parser import ParserError, UnknownTimezoneWarning

from target_gcs.helpers import get_partition_path_from_record
from target_gcs.helpers.partition_path import get_partition_path_from_schema_and_record

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


def test_partition_path_unparseable_value_raises():
    """Unparseable string in partition_date_field raises; no silent fallback. WHAT: Unparseable value causes visible exception (ParserError or ValueError). WHY: No silent fallback per feature requirement."""
    with pytest.raises((ParserError, ValueError)):
        get_partition_path_from_record(
            record={"created_at": "not-a-date"},
            partition_date_field="created_at",
            partition_date_format=DEFAULT_HIVE_FORMAT,
            fallback_date=FALLBACK_DATE,
        )


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


def test_partition_path_slash_separated_date_yields_hive_path():
    """Slash-separated date string (dateutil-only) yields Hive path from parsed date. WHAT: Format 'YYYY/MM/DD' is parsed and path uses that date. WHY: After Task 05 dateutil will support this; current code falls back so we assert a different day (15) so test fails until then."""
    result = get_partition_path_from_record(
        record={"created_at": "2024/03/15"},
        partition_date_field="created_at",
        partition_date_format=DEFAULT_HIVE_FORMAT,
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=15"


def test_partition_path_rfc_style_datetime_yields_hive_path():
    """RFC-style datetime string (dateutil-only) yields Hive path from parsed date. WHAT: Format 'DD Mon YYYY HH:MM:SS' is parsed and path uses that date. WHY: Common in logs/APIs; dateutil will support it in Task 05; assert day 15 so test fails with current fallback."""
    result = get_partition_path_from_record(
        record={"created_at": "15 Mar 2024 12:00:00"},
        partition_date_field="created_at",
        partition_date_format=DEFAULT_HIVE_FORMAT,
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=15"


def test_partition_path_long_month_name_yields_hive_path():
    """Long month name date string (dateutil-only) yields Hive path from parsed date. WHAT: Format 'Month DD, YYYY' is parsed and path uses that date. WHY: Broader format support after Task 05; assert day 20 so test fails with current fallback."""
    result = get_partition_path_from_record(
        record={"created_at": "March 20, 2024"},
        partition_date_field="created_at",
        partition_date_format=DEFAULT_HIVE_FORMAT,
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=20"


# Timestamp string with timezone name that dateutil does not resolve (no tzinfos).
# Used to assert UnknownTimezoneWarning is surfaced when Task 05 implements handling.
_UNKNOWN_TZ_TRIGGER_STRING = "2024-03-11 12:00:00 FOO"


def test_partition_path_unknown_timezone_surfaces_visibility():
    """Unsupported timezone in partition date string yields visible warning or error; no silent fallback. WHAT: String that triggers dateutil UnknownTimezoneWarning results in that warning being recorded or an exception raised. WHY: Feature requires unsupported timezone to be visible, not silently ignored."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        get_partition_path_from_record(
            record={"created_at": _UNKNOWN_TZ_TRIGGER_STRING},
            partition_date_field="created_at",
            partition_date_format=DEFAULT_HIVE_FORMAT,
            fallback_date=FALLBACK_DATE,
        )
    unknown_tz_warnings = [w for w in caught if w.category is UnknownTimezoneWarning]
    assert len(unknown_tz_warnings) >= 1, (
        "UnknownTimezoneWarning must be surfaced for unsupported timezone"
    )


# --- get_partition_path_from_schema_and_record ---


def test_get_partition_path_from_schema_and_record_importable_from_helpers():
    """Public API: get_partition_path_from_schema_and_record is importable from target_gcs.helpers and returns a non-empty path. WHAT: Import from helpers and call with empty schema/record and fallback_date; result is fallback path. WHY: Ensures the symbol is exported and callable from the public API."""
    from target_gcs.helpers import get_partition_path_from_schema_and_record

    result = get_partition_path_from_schema_and_record(
        schema={},
        record={},
        fallback_date=FALLBACK_DATE,
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_schema_and_record_no_x_partition_fields_uses_fallback():
    """No x-partition-fields in schema yields fallback_date formatted path. WHAT: When schema has no key or empty schema, path is fallback_date.strftime(partition_date_format). WHY: Ensures predictable path when partitioning is not schema-driven."""
    result = get_partition_path_from_schema_and_record(
        schema={},
        record={"any": "value"},
        fallback_date=FALLBACK_DATE,
    )
    assert result == FALLBACK_DATE.strftime(DEFAULT_HIVE_FORMAT)


def test_schema_and_record_empty_x_partition_fields_uses_fallback():
    """Empty x-partition-fields list yields same as no key (fallback path). WHAT: schema with x-partition-fields: [] returns fallback_date formatted. WHY: Empty list is treated as "no partition fields" per plan."""
    result = get_partition_path_from_schema_and_record(
        schema={"x-partition-fields": []},
        record={"region": "eu"},
        fallback_date=FALLBACK_DATE,
    )
    assert result == FALLBACK_DATE.strftime(DEFAULT_HIVE_FORMAT)


def test_schema_and_record_single_date_field_datetime():
    """Single date field with datetime value yields one Hive date segment. WHAT: x-partition-fields [dt], properties dt format date-time, record dt=datetime → year=2024/month=03/day=11. WHY: Core date-segment behaviour from native datetime."""
    schema = {
        "properties": {"dt": {"type": "string", "format": "date-time"}},
        "x-partition-fields": ["dt"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"dt": datetime(2024, 3, 11)},
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=11"


def test_schema_and_record_single_date_field_string_iso():
    """Single date field with ISO date string yields same Hive segment. WHAT: record dt='2024-03-11', format 'date' → year=2024/month=03/day=11. WHY: String dates must be parsed and formatted like datetime."""
    schema = {
        "properties": {"dt": {"type": "string", "format": "date"}},
        "x-partition-fields": ["dt"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"dt": "2024-03-11"},
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=11"


def test_schema_and_record_single_literal_field():
    """Single literal (non-date) field yields one path segment. WHAT: x-partition-fields [region], record region='eu', no date format → 'eu'. WHY: Literal partition keys (e.g. region) produce path-safe folder names."""
    schema = {
        "properties": {"region": {"type": "string"}},
        "x-partition-fields": ["region"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"region": "eu"},
        fallback_date=FALLBACK_DATE,
    )
    assert result == "eu"


def test_schema_and_record_enum_then_date_order():
    """Two fields (enum then date) produce path in array order. WHAT: region then dt → 'eu/year=2024/month=03/day=11'. WHY: Path order must follow x-partition-fields array order."""
    schema = {
        "properties": {
            "region": {"type": "string"},
            "dt": {"type": "string", "format": "date-time"},
        },
        "x-partition-fields": ["region", "dt"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"region": "eu", "dt": datetime(2024, 3, 11)},
        fallback_date=FALLBACK_DATE,
    )
    assert result == "eu/year=2024/month=03/day=11"


def test_schema_and_record_date_then_enum_order():
    """Two fields (date then enum) produce path in array order. WHAT: dt then region → 'year=2024/month=03/day=11/eu'. WHY: Path order must follow x-partition-fields array order."""
    schema = {
        "properties": {
            "dt": {"type": "string", "format": "date-time"},
            "region": {"type": "string"},
        },
        "x-partition-fields": ["dt", "region"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"region": "eu", "dt": datetime(2024, 3, 11)},
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=11/eu"


def test_schema_and_record_literal_with_slash_sanitized():
    """Literal value containing slash is path-sanitized (e.g. slash → underscore). WHAT: record region='a/b' yields segment 'a_b'. WHY: Embedded slashes would break path structure."""
    schema = {
        "properties": {"region": {"type": "string"}},
        "x-partition-fields": ["region"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"region": "a/b"},
        fallback_date=FALLBACK_DATE,
    )
    assert result == "a_b"


def test_schema_and_record_unparseable_date_raises_parser_error():
    """Unparseable date string when schema suggests date raises ParserError. WHAT: record dt='not-a-date', format date/date-time → ParserError from dateutil. WHY: No silent fallback; caller must handle invalid data."""
    schema = {
        "properties": {"dt": {"type": "string", "format": "date"}},
        "x-partition-fields": ["dt"],
    }
    with pytest.raises(ParserError):
        get_partition_path_from_schema_and_record(
            schema=schema,
            record={"dt": "not-a-date"},
            fallback_date=FALLBACK_DATE,
        )


def test_schema_and_record_no_format_datetime_still_date_segment():
    """No format + datetime yields Hive date segment. WHAT: Partition field has no format in schema; value is native datetime; path is still a Hive date segment. WHY: Native datetime/date are always treated as date segments regardless of schema format."""
    schema = {
        "properties": {"dt": {"type": "string"}},
        "x-partition-fields": ["dt"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"dt": datetime(2024, 3, 11)},
        fallback_date=FALLBACK_DATE,
    )
    assert result == "year=2024/month=03/day=11"


@pytest.mark.xfail(
    reason="Implementation in task 03: string date inference removed; will pass after partition_path.py updated."
)
def test_schema_and_record_no_format_parseable_string_literal_segment():
    """No format + dateutil-parseable string yields path-safe literal. WHAT: Partition field has no format; value is string '2024/03/11'; path is literal segment with slashes replaced. WHY: We must not infer date from string content when schema does not declare date/date-time format."""
    schema = {
        "properties": {"dt": {"type": "string"}},
        "x-partition-fields": ["dt"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"dt": "2024/03/11"},
        fallback_date=FALLBACK_DATE,
    )
    assert result == "2024_03_11"
