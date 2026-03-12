"""Unit tests for validate_partition_date_field_schema: partition-date-field schema validation."""

import pytest

from target_gcs.helpers import validate_partition_date_field_schema

STREAM_NAME = "test_stream"


def test_validate_partition_field_missing_from_schema_raises():
    """Field missing from schema raises ValueError so users get a clear config error."""
    schema = {"properties": {"a": {"type": "string"}}}
    field_name = "b"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "not in schema" in msg or "not in" in msg.lower()


def test_validate_partition_field_null_only_type_raises():
    """Null-only type raises ValueError so partition field must be date-parseable."""
    schema = {"properties": {"x": {"type": "null"}}}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "null-only" in msg or "cannot be parsed to a date" in msg


def test_validate_partition_field_null_only_array_type_raises():
    """Null-only array type raises ValueError; same as single null type."""
    schema = {"properties": {"x": {"type": ["null"]}}}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "null-only" in msg or "cannot be parsed to a date" in msg


def test_validate_partition_field_integer_type_raises():
    """Integer type raises ValueError; non-date-parseable type must be rejected."""
    schema = {"properties": {"x": {"type": "integer"}}}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "non" in msg and ("date" in msg or "parseable" in msg)


def test_validate_partition_field_boolean_type_raises():
    """Boolean type raises ValueError; non-date-parseable type must be rejected."""
    schema = {"properties": {"x": {"type": "boolean"}}}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "non" in msg and ("date" in msg or "parseable" in msg)


def test_validate_partition_field_string_type_succeeds():
    """String type is valid; strings are date-parseable. No exception."""
    schema = {"properties": {"x": {"type": "string"}}}
    field_name = "x"
    validate_partition_date_field_schema(STREAM_NAME, field_name, schema)


def test_validate_partition_field_string_format_date_time_succeeds():
    """String with format date-time is valid; common datetime schema. No exception."""
    schema = {"properties": {"x": {"type": "string", "format": "date-time"}}}
    field_name = "x"
    validate_partition_date_field_schema(STREAM_NAME, field_name, schema)


def test_validate_partition_field_nullable_string_succeeds():
    """Nullable string (string | null) is valid; optional date field. No exception."""
    schema = {"properties": {"x": {"type": ["string", "null"]}}}
    field_name = "x"
    validate_partition_date_field_schema(STREAM_NAME, field_name, schema)


def test_validate_partition_field_empty_properties_raises():
    """Empty or missing properties: field not in schema; raises ValueError."""
    for schema in ({}, {"properties": {}}):
        field_name = "any"
        with pytest.raises(ValueError) as exc_info:
            validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
        msg = str(exc_info.value)
        assert STREAM_NAME in msg
        assert field_name in msg
        assert "not in schema" in msg or "not in" in msg.lower()


def test_validate_partition_field_no_properties_key_raises():
    """Schema with no properties key: field not in schema; raises ValueError."""
    schema = {}
    field_name = "any"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "not in schema" in msg or "not in" in msg.lower()
