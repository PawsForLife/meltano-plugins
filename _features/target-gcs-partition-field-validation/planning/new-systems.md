# New Systems — target-gcs-partition-field-validation

## Summary

No new services or external systems. New behaviour is a single validation step inside the existing target-gcs sink (and optionally a small helper used only by that sink).

## New Behaviour

### Partition field schema validation

- **Trigger**: When `partition_date_field` is set in config and a sink is created (schema already passed in).
- **Inputs**: Stream name, configured field name, stream schema (e.g. `self.schema`).
- **Output**: None on success; on failure raises an exception with a clear message (stream name, field name, reason: missing from schema, null-only type, or type not date-parseable).
- **Placement**: Run once per stream in the sink, in `__init__` after `super().__init__`, so `self.schema` is available.

## New Code Artefacts

### 1. Validation logic (internal)

- **Option A — Inline in GCSSink**: A small block in `GCSSink.__init__` that, when `partition_date_field` is set, checks `self.schema["properties"]` for the field and for a date-parseable type (and rejects null-only).
- **Option B — Helper**: A function (e.g. in `target_gcs/helpers/` or `target_gcs/sinks.py`) such as `validate_partition_date_field_schema(stream_name: str, field_name: str, schema: dict) -> None` that performs the checks and raises on failure. The sink calls it from `__init__`.

Recommendation: Helper (Option B) for testability and single responsibility; see selected-solution.md.

### 2. Tests

- **Sink tests**: Build sink with `partition_date_field` and various stream schemas; assert raised exception when field is missing, null-only, or non–date-parseable; assert no exception when field exists and is date-parseable (e.g. string, or string with format date/date-time).
- **Helper tests** (if Option B): Same cases against the helper function directly (missing field, null-only, integer/boolean, string, string with format date-time).

## Interfaces

- **Public**: No new public API. Config and Singer message contracts unchanged.
- **Internal**: Optional new function `validate_partition_date_field_schema(stream_name, field_name, schema)` with a defined exception type or `ValueError` and a consistent message format.

## Dependencies

- **Existing**: Stream schema (Singer/JSON Schema) and `self.config`; no new runtime dependencies.
- **Optional**: Reuse of `singer_sdk.helpers._typing` helpers (e.g. `get_datelike_property_type`, `is_date_or_datetime_type`) for “date-parseable” detection if we rely on string + date/date-time format; see selected-solution.md for allowed types.
