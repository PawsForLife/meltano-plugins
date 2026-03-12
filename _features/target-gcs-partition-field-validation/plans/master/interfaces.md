# Implementation Plan — Interfaces

## Public Interfaces

No new public API. Config schema and Singer message contracts are unchanged. The target and sink constructors remain as documented in `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`.

## New Internal Interface: Validation Helper

### Function

**Name**: `validate_partition_date_field_schema`

**Location**: `target_gcs/helpers/partition_path.py` or a new module under `target_gcs/helpers/` (e.g. `partition_schema.py`). Export from `target_gcs.helpers` so the sink can import it.

**Signature**:

```python
def validate_partition_date_field_schema(
    stream_name: str,
    field_name: str,
    schema: dict,
) -> None:
```

**Contract**:

- **Inputs**:
  - `stream_name`: Name of the stream (for error messages).
  - `field_name`: Config value of `partition_date_field` (property name to look up).
  - `schema`: Stream schema dict (Singer/JSON Schema); typically `self.schema` from the sink.
- **Success**: Returns `None`. No side effects.
- **Failure**: Raises `ValueError` with a message that includes:
  - Stream name (e.g. `Stream 'stream_name'`),
  - Field name (e.g. `partition_date_field 'field_name'`),
  - Reason: one of “is not in schema”, “is null-only and cannot be parsed to a date”, “has non–date-parseable type”.

**Behaviour**:

1. Resolve `properties = schema.get("properties") or {}`.
2. If `field_name not in properties` → raise `ValueError(..., "is not in schema")`.
3. Get property schema `prop_schema = properties[field_name]`.
4. Resolve `type` (string or array of types). If the only type is `"null"` (e.g. `type: "null"` or `type: ["null"]`) → raise `ValueError(..., "is null-only and cannot be parsed to a date")`.
5. If the set of types (excluding null) does not include a date-parseable type (see below) → raise `ValueError(..., "has non–date-parseable type")`.
6. Otherwise return.

**Date-parseable types**:

- Allow: `string` (with or without `format` in `{"date", "date-time"}`).
- Allow: nullable string (e.g. `["string", "null"]`).
- Reject: `integer`, `number`, `boolean`, `array`, `object`, and null-only.

Implementation may use `singer_sdk.helpers._typing.get_datelike_property_type` / `is_date_or_datetime_type` if available to detect date-like format; plain `string` without format is still allowed (dateutil parses many string formats).

## GCSSink Integration

**Call site**: In `GCSSink.__init__`, after `super().__init__(...)` and after initializing attributes (e.g. `_current_partition_path` when `partition_date_field` is set):

```python
partition_field = self.config.get("partition_date_field")
if partition_field:
    validate_partition_date_field_schema(
        self.stream_name,
        partition_field,
        self.schema,
    )
```

No change to method signatures of `GCSSink`; no new constructor parameters for validation.

## Data Models

No new Pydantic or dataclass models. Schema is the existing `dict` from the Singer SDK (JSON Schema). Validation uses this dict only for reads.

## Dependencies Between Interfaces

- Helper depends only on the structure of `schema` (e.g. `properties`, and per-property `type`/`format`). It does not depend on the target or sink classes.
- Sink depends on the helper’s signature and exception contract; tests may depend on the exact message format for assertion (or assert only exception type and that message contains stream name, field name, and a reason substring).
