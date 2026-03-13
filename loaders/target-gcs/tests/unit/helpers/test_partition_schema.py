"""Unit tests for partition schema validation (partition-date-field and partition-fields)."""

import pytest

from target_gcs.helpers import (
    validate_partition_date_field_schema,
    validate_partition_fields_schema,
)

STREAM_NAME = "test_stream"


def test_validate_partition_field_missing_from_schema_raises():
    """Field missing from schema raises ValueError so users get a clear config error."""
    schema = {"properties": {"a": {"type": "string"}}, "required": ["a"]}
    field_name = "b"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "not in schema" in msg or "not in" in msg.lower()


def test_validate_partition_field_not_required_raises():
    """Field in properties but not in schema required list raises ValueError."""
    schema = {"properties": {"x": {"type": "string"}}, "required": ["other"]}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "must be required" in msg


def test_validate_partition_field_missing_required_key_raises():
    """Schema with no required key raises ValueError so partition field must be required."""
    schema = {"properties": {"x": {"type": "string"}}}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert "required" in msg.lower()


def test_validate_partition_field_required_not_list_raises():
    """Schema with required not a list raises ValueError so partition field must be in required list."""
    schema = {"properties": {"x": {"type": "string"}}, "required": "x"}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert "required" in msg.lower()


def test_validate_partition_field_null_only_type_raises():
    """Null-only type raises ValueError so partition field must be date-parseable."""
    schema = {"properties": {"x": {"type": "null"}}, "required": ["x"]}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "null-only" in msg or "cannot be parsed to a date" in msg


def test_validate_partition_field_null_only_array_type_raises():
    """Null-only array type raises ValueError; same as single null type."""
    schema = {"properties": {"x": {"type": ["null"]}}, "required": ["x"]}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "null-only" in msg or "cannot be parsed to a date" in msg


def test_validate_partition_field_integer_type_raises():
    """Integer type raises ValueError; non-date-parseable type must be rejected."""
    schema = {"properties": {"x": {"type": "integer"}}, "required": ["x"]}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "non" in msg and ("date" in msg or "parseable" in msg)


def test_validate_partition_field_boolean_type_raises():
    """Boolean type raises ValueError; non-date-parseable type must be rejected."""
    schema = {"properties": {"x": {"type": "boolean"}}, "required": ["x"]}
    field_name = "x"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert field_name in msg
    assert "non" in msg and ("date" in msg or "parseable" in msg)


def test_validate_partition_field_string_type_succeeds():
    """String type is valid when field is required; strings are date-parseable. No exception."""
    schema = {"properties": {"x": {"type": "string"}}, "required": ["x"]}
    field_name = "x"
    validate_partition_date_field_schema(STREAM_NAME, field_name, schema)


def test_validate_partition_field_string_format_date_time_succeeds():
    """String with format date-time is valid when field is required; common datetime schema. No exception."""
    schema = {
        "properties": {"x": {"type": "string", "format": "date-time"}},
        "required": ["x"],
    }
    field_name = "x"
    validate_partition_date_field_schema(STREAM_NAME, field_name, schema)


def test_validate_partition_field_nullable_string_succeeds():
    """Nullable string (string | null) is valid when field is required. No exception."""
    schema = {"properties": {"x": {"type": ["string", "null"]}}, "required": ["x"]}
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
        assert "not in schema" in msg or "required" in msg.lower()


def test_validate_partition_field_no_properties_key_raises():
    """Schema with no properties key: field not in schema; raises ValueError."""
    schema = {}
    field_name = "any"
    with pytest.raises(ValueError) as exc_info:
        validate_partition_date_field_schema(STREAM_NAME, field_name, schema)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert "not in schema" in msg or "required" in msg.lower()


# --- validate_partition_fields_schema (x-partition-fields / schema-driven Hive) ---


def test_validate_partition_fields_schema_importable_from_helpers():
    """Public API: validate_partition_fields_schema is importable from target_gcs.helpers and callable with valid args. WHAT: Import from helpers and call with minimal valid schema/partition_fields. WHY: Ensures the symbol is exported and usable from the public API."""
    from target_gcs.helpers import validate_partition_fields_schema

    schema = {"properties": {"x": {"type": "string"}}, "required": ["x"]}
    validate_partition_fields_schema(STREAM_NAME, schema, ["x"])


def test_validate_partition_fields_schema_valid_passes():
    """All partition fields in properties, required, and non-nullable; no exception."""
    schema = {
        "properties": {
            "A": {"type": "string"},
            "B": {"type": "number"},
        },
        "required": ["A", "B"],
    }
    partition_fields = ["A", "B"]
    validate_partition_fields_schema(STREAM_NAME, schema, partition_fields)


def test_validate_partition_fields_schema_missing_field_in_properties_raises():
    """Partition field not in schema properties raises ValueError with stream name and 'not in schema'."""
    schema = {"properties": {"A": {"type": "string"}}, "required": ["A"]}
    partition_fields = ["A", "C"]
    with pytest.raises(ValueError) as exc_info:
        validate_partition_fields_schema(STREAM_NAME, schema, partition_fields)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert "C" in msg
    assert "not in schema" in msg or "not in" in msg.lower()


def test_validate_partition_fields_schema_field_not_required_raises():
    """Partition field in properties but not in required raises ValueError 'must be required'."""
    schema = {
        "properties": {"A": {"type": "string"}, "B": {"type": "string"}},
        "required": ["A"],
    }
    partition_fields = ["A", "B"]
    with pytest.raises(ValueError) as exc_info:
        validate_partition_fields_schema(STREAM_NAME, schema, partition_fields)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert "B" in msg
    assert "must be required" in msg


def test_validate_partition_fields_schema_required_not_list_raises():
    """Schema with required not a list raises ValueError so schema shape is valid."""
    schema = {"properties": {"a": {"type": "string"}}, "required": "a"}
    partition_fields = ["a"]
    with pytest.raises(ValueError) as exc_info:
        validate_partition_fields_schema(STREAM_NAME, schema, partition_fields)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert "required" in msg.lower()


def test_validate_partition_fields_schema_null_only_type_raises():
    """Property type 'null' only raises ValueError 'null-only'."""
    schema = {"properties": {"x": {"type": "null"}}, "required": ["x"]}
    partition_fields = ["x"]
    with pytest.raises(ValueError) as exc_info:
        validate_partition_fields_schema(STREAM_NAME, schema, partition_fields)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert "x" in msg
    assert "null-only" in msg


def test_validate_partition_fields_schema_null_only_array_type_raises():
    """Property type ['null'] raises ValueError 'null-only'; same as single null."""
    schema = {"properties": {"x": {"type": ["null"]}}, "required": ["x"]}
    partition_fields = ["x"]
    with pytest.raises(ValueError) as exc_info:
        validate_partition_fields_schema(STREAM_NAME, schema, partition_fields)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert "x" in msg
    assert "null-only" in msg


def test_validate_partition_fields_schema_mixed_optional_required_raises():
    """Required [A]; partition_fields [A, B]; B optional raises ValueError for B."""
    schema = {
        "properties": {"A": {"type": "string"}, "B": {"type": "string"}},
        "required": ["A"],
    }
    partition_fields = ["A", "B"]
    with pytest.raises(ValueError) as exc_info:
        validate_partition_fields_schema(STREAM_NAME, schema, partition_fields)
    msg = str(exc_info.value)
    assert STREAM_NAME in msg
    assert "B" in msg
    assert "must be required" in msg
