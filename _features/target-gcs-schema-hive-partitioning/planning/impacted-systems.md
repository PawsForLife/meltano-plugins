# Impacted Systems — Schema-driven Hive Partitioning

Existing project parts that this feature changes or extends.

## Config and target

- **`target_gcs/target.py`**
  - Add `hive_partitioned: bool` (default `false`) to `config_jsonschema`.
  - Remove or deprecate config-driven partition field names: `partition_date_field` and `partition_date_format` are replaced by schema-driven behaviour when `hive_partitioned` is true (single flag, no config partition field list).
  - Sink creation unchanged; sinks receive schema (and thus `x-partition-fields` when present).

## Sink and key building

- **`target_gcs/sinks.py`**
  - **Partition enablement**: Use `hive_partitioned` instead of presence of `partition_date_field` to decide partition-by-field vs flat/chunked path. When `hive_partitioned` is true, partition path comes from schema + record (see below); when false, retain current non-hive behaviour (single key or chunked, no record-driven partition).
  - **Key template**: When `hive_partitioned` is true, effective key template remains `{stream}/{partition_date}/{timestamp}.{format}` (or user override). `partition_date` (and `hive`) becomes the full multi-segment path (e.g. `region_a/year=2024/month=03/day=11`).
  - **Record processing**: Replace single-field `get_partition_path_from_record(record, partition_date_field, ...)` with a path builder that (a) reads `x-partition-fields` from stream schema, (b) for each field in order: if date-parseable → YEAR=.../MONTH=.../DAY=... segment, else → literal folder name, (c) concatenates segments. When `hive_partitioned` is true and `x-partition-fields` is absent, use current date for partition path (existing date-only behaviour).
  - **Init**: When `hive_partitioned` is true and schema has `x-partition-fields`, run validation that each listed field is required and non-nullable (see new-systems). No longer validate a single `partition_date_field` from config.

## Helpers

- **`target_gcs/helpers/partition_path.py`**
  - Extend or replace single-field `get_partition_path_from_record` with a function that builds a full partition path from (schema, record, fallback_date): resolve `x-partition-fields` from schema; for each field compute segment (date → Hive date path, else literal); return path string in field order. Existing single-field date logic can be reused for the date case (one field, one segment).

- **`target_gcs/helpers/partition_schema.py`**
  - Replace or extend `validate_partition_date_field_schema(stream_name, field_name, schema)` with validation for `x-partition-fields`: each field must exist in `schema["properties"]`, be in `schema["required"]`, and be non-nullable (type not only `"null"`). Optionally: for fields used as date, require date-parseable type (e.g. string or date/date-time format). Called from sink init when `hive_partitioned` is true and `x-partition-fields` is present.

- **`target_gcs/helpers/__init__.py`**
  - Export new partition-path builder and new/updated schema validator; keep or deprecate old function names as needed for call sites.

## Meltano and docs

- **`loaders/target-gcs/meltano.yml`**
  - Add setting `hive_partitioned` (bool, default false). Remove or keep `partition_date_field` / `partition_date_format` for backward compatibility per product decision (feature says no backward compatibility required; can remove).

- **`loaders/target-gcs/README.md`**
  - Document `hive_partitioned` and stream-level `x-partition-fields`; path order and semantics (date → YEAR/MONTH/DAY, non-date → literal folder); required/non-nullable rules.

## Tests

- **`loaders/target-gcs/tests/test_sinks.py`**
  - Config schema tests: assert `hive_partitioned` present and optional; adjust or remove tests for `partition_date_field` / `partition_date_format` if those are removed.
  - Sink init: when `hive_partitioned` true and `x-partition-fields` present, assert validation runs (and fails with clear error if a partition field is missing, optional, or nullable-only).
  - Key/build tests: drive behaviour via `hive_partitioned` + schema; assert output paths, not internal call counts (black-box).

- **`loaders/target-gcs/tests/helpers/test_partition_path.py`**
  - Add cases for multi-field path: (a) all date, (b) all enum (literal), (c) mixed order (enum then date, date then enum), (d) `x-partition-fields` missing when `hive_partitioned` true → current date path.
  - Keep or adapt existing single-field date tests as one-field path building.

- **`loaders/target-gcs/tests/helpers/test_partition_schema.py`**
  - Add tests for `x-partition-fields` validation: required, non-nullable; fail when field missing, optional, or null-only.

- **`loaders/target-gcs/tests/test_partition_key_generation.py`**
  - Update to use `hive_partitioned` and schema-driven partition fields; assert keys and paths for multiple streams and field orders.
