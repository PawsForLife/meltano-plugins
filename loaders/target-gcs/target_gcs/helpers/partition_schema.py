"""Partition schema validation for target-gcs (partition-date-field and partition-fields)."""

from __future__ import annotations


def validate_partition_fields_schema(
    stream_name: str,
    schema: dict,
    partition_fields: list[str],
) -> None:
    """Validate that every partition field exists in the stream schema, is required, and is non-nullable.

    For schema-driven Hive partitioning (x-partition-fields), each field must be in
    schema["properties"], in schema["required"], and have at least one non-null type.

    Args:
        stream_name: Name of the stream (for error messages).
        schema: Stream schema dict (Singer/JSON Schema).
        partition_fields: List of property names from x-partition-fields.

    Returns:
        None on success.

    Raises:
        ValueError: With message including stream_name, field name, and reason
            (e.g. "is not in schema", "must be required for the stream", "is null-only").
    """
    properties = schema.get("properties") or {}
    required = schema.get("required")

    if not isinstance(required, list):
        raise ValueError(f"Stream '{stream_name}': schema 'required' must be a list.")

    for field in partition_fields:
        if field not in properties:
            raise ValueError(
                f"Stream '{stream_name}': partition field '{field}' is not in schema."
            )
        if field not in required:
            raise ValueError(
                f"Stream '{stream_name}': partition field '{field}' must be required for the stream."
            )

        prop_schema = properties[field]
        raw_type = prop_schema.get("type")
        if raw_type is None:
            raise ValueError(
                f"Stream '{stream_name}': partition field '{field}' has no type (null-only or missing)."
            )

        types: list[str] = [raw_type] if isinstance(raw_type, str) else list(raw_type)
        non_null = [t for t in types if t != "null"]

        if not non_null:
            raise ValueError(
                f"Stream '{stream_name}': partition field '{field}' is null-only."
            )


def validate_partition_date_field_schema(
    stream_name: str,
    field_name: str,
    schema: dict,
) -> None:
    """Validate that partition_date_field exists in the stream schema and is date-parseable.

    Checks that the configured partition date field is present in schema["properties"],
    is not null-only, and has a type that can be parsed to a date (string, with or
    without date/date-time format; nullable string allowed).

    Args:
        stream_name: Name of the stream (for error messages).
        field_name: Config value of partition_date_field (property name to look up).
        schema: Stream schema dict (Singer/JSON Schema); typically self.schema from the sink.

    Returns:
        None on success.

    Raises:
        ValueError: With message including stream name, field name, and one of:
            "is not in schema", "must be required for the stream",
            "is null-only and cannot be parsed to a date",
            "has non–date-parseable type".
    """
    properties = schema.get("properties") or {}
    if field_name not in properties:
        raise ValueError(
            f"Stream '{stream_name}': partition_date_field '{field_name}' is not in schema."
        )

    required = schema.get("required")
    if not isinstance(required, list) or field_name not in required:
        raise ValueError(
            f"Stream '{stream_name}': partition_date_field '{field_name}' must be required for the stream."
        )

    prop_schema = properties[field_name]
    raw_type = prop_schema.get("type")
    if raw_type is None:
        raise ValueError(
            f"Stream '{stream_name}': partition_date_field '{field_name}' has non–date-parseable type."
        )

    types: list[str] = [raw_type] if isinstance(raw_type, str) else list(raw_type)
    non_null = [t for t in types if t != "null"]

    if not non_null:
        raise ValueError(
            f"Stream '{stream_name}': partition_date_field '{field_name}' is null-only and cannot be parsed to a date."
        )

    date_parseable = False
    for t in non_null:
        if t == "string":
            date_parseable = True
            break
        if t not in ("integer", "number", "boolean", "array", "object", "null"):
            # Allow other types that might be date-like if we extend later
            break

    if not date_parseable:
        raise ValueError(
            f"Stream '{stream_name}': partition_date_field '{field_name}' has non–date-parseable type."
        )
