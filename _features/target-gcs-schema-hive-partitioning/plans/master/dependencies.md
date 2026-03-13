# Dependencies — Schema-driven Hive Partitioning

## External Dependencies

- **No new packages.** Reuse existing:
  - `dateutil` (python-dateutil): already used in `target_gcs.helpers.partition_path` for parsing date strings. Used in new path builder for date detection and parsing.
  - `singer_sdk`, `google.cloud.storage`, `smart_open`, `orjson`, etc.: unchanged.

## Internal Dependencies

| Consumer | Depends On |
|----------|------------|
| `target_gcs.sinks.GCSSink` | `target_gcs.helpers.get_partition_path_from_schema_and_record`, `validate_partition_fields_schema`, `DEFAULT_PARTITION_DATE_FORMAT` (sinks or helpers) |
| `target_gcs.helpers.partition_path` | `dateutil.parser`; optional: same constant as sinks for default format (avoid circular import: define default in partition_path or pass from sinks) |
| `target_gcs.helpers.partition_schema` | None (stdlib only) |
| `target_gcs.target.GCSTarget` | `GCSSink`; config schema only |

## System Requirements

- Unchanged: Python ≥3.12,<4.0 for target-gcs; uv for install; pytest, ruff, mypy for dev.

## Environment

- No new env vars. GCS auth remains Application Default Credentials (`GOOGLE_APPLICATION_CREDENTIALS` or default).

## Configuration (Config File)

- **Added**: `hive_partitioned` (boolean, optional, default false). When true, partition path is derived from stream schema (`x-partition-fields`) and record, or current date when schema has no x-partition-fields.
- **Removed**: `partition_date_field`, `partition_date_format` from config schema and from meltano.yml. State file and Catalog usage unchanged (target does not drive Catalog; streams and schema come from tap/Catalog).

## Meltano

- **meltano.yml**: Add setting for `hive_partitioned` (boolean, default false). Remove settings for `partition_date_field` and `partition_date_format` if present. No change to pip_url or namespace.

## Order of Implementation (Dependency Graph)

1. partition_schema: validate_partition_fields_schema (no internal deps).
2. partition_path: get_partition_path_from_schema_and_record (uses dateutil; no dependency on schema validator or sink).
3. helpers/__init__.py: export new functions.
4. target.py: config schema change (no runtime dep on new helpers).
5. sinks.py: import new helpers; use hive_partitioned and new path/validation (depends on 1–4).

Tests for (1) and (2) can be written and run in parallel with implementation; sink tests depend on (5).
