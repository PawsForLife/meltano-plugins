# Selected Solution — target-gcs-partition-field-validation

## Choice: Internal validation

Validation is implemented inside target-gcs. No external library beyond the existing stack (singer_sdk, stream schema). The sink runs validation in `__init__` when `partition_date_field` is set, using the stream schema already on the sink.

## How validation fits

### Schema access

- The stream schema is available on the sink as **`self.schema`** after `super().__init__(...)` in `GCSSink.__init__`. The Singer SDK base `Sink` sets `self.schema = schema` and `self.original_schema = copy.deepcopy(schema)` in its `__init__`. The target creates the sink only when it has a schema (from the SCHEMA message), so at the point we run validation, `self.schema` is the stream’s JSON Schema dict.
- Use **`self.schema["properties"]`** to get the map of property names to property schemas. The configured field must exist there.

### JSON Schema structure (stream schema)

- Singer stream schemas are JSON Schema objects. Top-level **`properties`** is a dict: key = property name, value = property schema.
- A property schema may have:
  - **`type`**: string (e.g. `"string"`) or array (e.g. `["string", "null"]`).
  - **`format`** (optional): e.g. `"date-time"`, `"date"` (common for date-parseable fields).
- **Null-only**: If `type` is exactly `["null"]` or `"null"`, the field allows only null — reject for partition_date_field.
- **Nullable allowed**: `["string", "null"]` or `["date-time", "null"]` (if type were date-time) is acceptable: the field can be string (or date-like) or null; runtime already handles null via fallback in `get_partition_path_from_record`.

### Date-parseable types

- **Allow**: `string` (with or without `format`). Runtime uses `dateutil.parser.parse` for strings and accepts `datetime`/`date`; string is the primary type we can parse to a date. Optionally allow property with **`format`** in `{"date", "date-time"}` (Singer/schema convention for date-like strings).
- **Reject**: `integer`, `number`, `boolean`, `array`, `object`, and **null-only** (`type` is `"null"` or `["null"]`). These are not parsed to a date by the current logic (and integer/boolean would be misleading as partition keys).
- **Implementation**: Treat as date-parseable if the property’s type (or resolved type from `anyOf`/`oneOf` if we support it) includes `string`, or has a date-like format. We can reuse `singer_sdk.helpers._typing.get_datelike_property_type` or `is_date_or_datetime_type` where applicable: they return a date-like format when the property is string with format `date`/`date-time` (and handle `anyOf`). For plain `string` without format, we still allow it (dateutil parses many string formats). So: allow if (a) type includes `string`, or (b) property is date-like per SDK helpers.

### Null handling

- **Null-only**: If the property schema allows *only* null (e.g. `"type": "null"` or `"type": ["null"]` with no other type), validation **fails** with a clear message (e.g. “partition_date_field is null-only and cannot be parsed to a date”).
- **Nullable string** (e.g. `"type": ["string", "null"]`): **Allow**. Runtime already falls back to run date when the value is missing or null.

## Implementation outline

1. **Where**: In `GCSSink.__init__`, after `super().__init__(...)`, if `self.config.get("partition_date_field")` is set, call a validation function with `self.stream_name`, the configured field name, and `self.schema`.
2. **Helper** (recommended): `validate_partition_date_field_schema(stream_name: str, field_name: str, schema: dict) -> None`. Raises `ValueError` with message including stream name, field name, and reason (missing from schema; null-only; type not date-parseable). Implement by: (a) resolve `schema.get("properties") or {}`, (b) if field_name not in properties → raise “missing from schema”, (c) get property schema; if type is null-only → raise “null-only”, (d) if type is not string and not date-like (per rules above) → raise “type not date-parseable”.
3. **Error message**: e.g. `f"Stream '{stream_name}': partition_date_field '{field_name}' is not in schema"` / `"... is null-only"` / `"... has non–date-parseable type"`.
4. **Tests**: Unit tests for the helper (or for the sink built with `partition_date_field` and various schemas): missing field → error; null-only → error; integer/boolean → error; string or string+null or date-time format → no error.

## Summary

- **Internal** solution; validation in sink **`__init__`** using **`self.schema`**.
- **Schema**: `self.schema["properties"]`; property may have `type` (string or array) and optional `format`.
- **Date-parseable**: Allow `string` (with or without `format` date/date-time); allow nullable string; reject null-only and non-string/non–date-like types.
- **Null**: Reject null-only; allow nullable string so runtime fallback remains valid.
