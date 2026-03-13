"""Tests for partition path helper get_partition_path_from_schema_and_record."""

from datetime import datetime

import pytest
from dateutil.parser import ParserError

from target_gcs.helpers.partition_path import get_partition_path_from_schema_and_record

# Fixed extraction date for deterministic partition resolution tests (no datetime.today() in tests).
EXTRACTION_DATE = datetime(2024, 3, 11)
DEFAULT_HIVE_FORMAT = "year=%Y/month=%m/day=%d"


def test_get_partition_path_from_schema_and_record_importable_from_helpers():
    """Public API: get_partition_path_from_schema_and_record is importable from target_gcs.helpers and returns a non-empty path. WHAT: Import from helpers and call with empty schema/record and extraction_date; result is extraction date path. WHY: Ensures the symbol is exported and callable from the public API."""
    from target_gcs.helpers import get_partition_path_from_schema_and_record

    result = get_partition_path_from_schema_and_record(
        schema={},
        record={},
        extraction_date=EXTRACTION_DATE,
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_schema_and_record_no_x_partition_fields_uses_extraction_date():
    """No x-partition-fields in schema yields extraction_date formatted path. WHAT: When schema has no key or empty schema, path is extraction_date.strftime(partition_date_format). WHY: Ensures predictable path when partitioning is not schema-driven."""
    result = get_partition_path_from_schema_and_record(
        schema={},
        record={"any": "value"},
        extraction_date=EXTRACTION_DATE,
    )
    assert result == EXTRACTION_DATE.strftime(DEFAULT_HIVE_FORMAT)


def test_schema_and_record_empty_x_partition_fields_uses_extraction_date():
    """Empty x-partition-fields list yields same as no key (extraction date path). WHAT: schema with x-partition-fields: [] returns extraction_date formatted. WHY: Empty list is treated as "no partition fields" per plan."""
    result = get_partition_path_from_schema_and_record(
        schema={"x-partition-fields": []},
        record={"region": "eu"},
        extraction_date=EXTRACTION_DATE,
    )
    assert result == EXTRACTION_DATE.strftime(DEFAULT_HIVE_FORMAT)


def test_schema_and_record_single_date_field_datetime():
    """Single date field with datetime value yields one Hive date segment. WHAT: x-partition-fields [dt], properties dt format date-time, record dt=datetime → year=2024/month=03/day=11. WHY: Core date-segment behaviour from native datetime."""
    schema = {
        "properties": {"dt": {"type": "string", "format": "date-time"}},
        "x-partition-fields": ["dt"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"dt": datetime(2024, 3, 11)},
        extraction_date=EXTRACTION_DATE,
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
        extraction_date=EXTRACTION_DATE,
    )
    assert result == "year=2024/month=03/day=11"


def test_schema_and_record_single_literal_field():
    """Single literal (non-date) field yields one Hive key=value segment. WHAT: x-partition-fields [region], record region='eu', no date format → 'region=eu'. WHY: Literal partition keys use Hive-standard field_name=value segments."""
    schema = {
        "properties": {"region": {"type": "string"}},
        "x-partition-fields": ["region"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"region": "eu"},
        extraction_date=EXTRACTION_DATE,
    )
    assert result == "region=eu"


def test_schema_and_record_enum_then_date_order():
    """Two fields (enum then date) produce path in array order with key=value literal. WHAT: region then dt → 'region=eu/year=2024/month=03/day=11'. WHY: Path order follows x-partition-fields; literal segments are Hive key=value."""
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
        extraction_date=EXTRACTION_DATE,
    )
    assert result == "region=eu/year=2024/month=03/day=11"


def test_schema_and_record_date_then_enum_order():
    """Two fields (date then enum) produce path in array order with key=value literal. WHAT: dt then region → 'year=2024/month=03/day=11/region=eu'. WHY: Path order follows x-partition-fields; literal segments are Hive key=value."""
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
        extraction_date=EXTRACTION_DATE,
    )
    assert result == "year=2024/month=03/day=11/region=eu"


def test_schema_and_record_literal_with_slash_sanitized():
    """Literal value containing slash is path-sanitized; segment is Hive key=value. WHAT: record region='a/b' yields segment 'region=a_b'. WHY: Embedded slashes sanitized; literal segments use field_name=value."""
    schema = {
        "properties": {"region": {"type": "string"}},
        "x-partition-fields": ["region"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"region": "a/b"},
        extraction_date=EXTRACTION_DATE,
    )
    assert result == "region=a_b"


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
            extraction_date=EXTRACTION_DATE,
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
        extraction_date=EXTRACTION_DATE,
    )
    assert result == "year=2024/month=03/day=11"


def test_schema_and_record_no_format_parseable_string_literal_segment():
    """No format + dateutil-parseable string yields Hive key=value literal segment. WHAT: Partition field dt has no format; value '2024/03/11' → literal segment 'dt=2024_03_11'. WHY: No date inference when schema has no format; literal segments use field_name=value."""
    schema = {
        "properties": {"dt": {"type": "string"}},
        "x-partition-fields": ["dt"],
    }
    result = get_partition_path_from_schema_and_record(
        schema=schema,
        record={"dt": "2024/03/11"},
        extraction_date=EXTRACTION_DATE,
    )
    assert result == "dt=2024_03_11"
