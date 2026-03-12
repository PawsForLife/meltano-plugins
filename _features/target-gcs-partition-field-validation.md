# Background

target-gcs supports a `partition_date_field` config: when set, the loader uses that record property to build partition paths (e.g. Hive-style) for GCS keys. Currently there is no validation that:

1. The configured field exists in the stream schema.
2. The schema type for that field is compatible with date parsing (not null-only, and not types that cannot be parsed to a date).

Without this, misconfiguration (e.g. typo in field name or a field that is null/integer) can cause runtime errors or silent fallbacks. Validation at sink initialization (after SCHEMA is received) gives clear, early feedback.

# This Task

- When `partition_date_field` is specified in config, validate before processing records:
  1. **Schema presence**: The field exists in the stream schema (`schema.properties`).
  2. **Date-parseable type**: The schema does not allow only null, and the type is one that can be parsed to a date (e.g. string, date-time; reject or constrain types that cannot be parsed to a date, and disallow null-only).

- Implement validation in the target-gcs sink (e.g. GCSSink), using the stream schema available on the Sink (e.g. `self.schema` per Singer SDK). Run validation in `__init__` or at start of batch/stream so it runs once per stream after SCHEMA is received.

- If validation fails: raise a clear error (e.g. `ValueError`) with a message that states the stream name, the configured field name, and the reason (missing from schema, or type not date-parseable / null-only).

# Testing Needed

- Unit tests that a sink (or validation helper) raises when `partition_date_field` is set and:
  - The field is missing from the stream schema.
  - The schema marks the field as null-only or a type that cannot be parsed to a date (e.g. integer, boolean; clarify allowed types from JSON Schema / Singer).
- Unit tests that validation passes when the field exists and has a date-parseable type (e.g. string, or format date/date-time).
- Optionally: test that when `partition_date_field` is not set, no schema validation for that field runs (no regression).
- All tests must be black-box (assert outcome, not call counts); follow TDD and project lint/format.
