# Implementation Plan — Architecture

## System Design and Structure

Validation is a **single responsibility** inside the target-gcs loader: a small helper function performs schema checks; the sink calls it once per stream during construction. No new services, no new processes, no change to Singer message flow.

## Component Breakdown and Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Validation helper** | `validate_partition_date_field_schema(stream_name, field_name, schema)` — Ensures the field exists in `schema["properties"]`, is not null-only, and has a date-parseable type. Raises `ValueError` with a clear message on failure. |
| **GCSSink** | After `super().__init__`, if `self.config.get("partition_date_field")` is set, calls the helper with `self.stream_name`, the configured field name, and `self.schema`. No change to record processing or key building. |
| **partition_path.py** | Unchanged. `get_partition_path_from_record` continues to resolve partition paths from record values; validation is schema-only and does not touch this module’s signature or behaviour. |

## Data Flow

1. Target receives SCHEMA message for a stream and creates a sink with that schema.
2. `GCSSink.__init__(target, stream_name, schema, key_properties, ...)` runs; `super().__init__` sets `self.schema`.
3. If `partition_date_field` is in config, sink calls `validate_partition_date_field_schema(stream_name, field_name, self.schema)`.
4. Helper reads `schema.get("properties") or {}`, checks field presence and property type; returns normally or raises `ValueError`.
5. Record processing proceeds as today; no validation at record time.

## Design Patterns and Principles

- **Single responsibility**: Helper encapsulates “is this schema valid for partition_date_field?”; sink remains responsible for writing and key naming.
- **Fail fast**: Validation at init avoids partial writes and unclear errors later.
- **Testability**: Pure function `(stream_name, field_name, schema) -> None` is easy to unit test without constructing a full sink.
- **Existing patterns**: Aligns with project use of Singer SDK schema on the sink and config-driven behaviour; see `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` and `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`.

## Placement of Validation Logic

- **Option chosen**: Dedicated helper (e.g. in `target_gcs/helpers/` or alongside partition_path) so that:
  - Logic is testable in isolation.
  - Sink `__init__` stays readable (one call when config has `partition_date_field`).
- **Not in partition_path.py**: `get_partition_path_from_record` operates on record values and fallback date; validation operates on schema only. Co-location in the same helper module is acceptable if the codebase prefers it; the plan uses a separate helper for clarity.
