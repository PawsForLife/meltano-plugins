# Architecture — Schema-driven Hive Partitioning

## Design Summary

Partitioning is driven by a boolean config flag and optional stream-level schema metadata. Path building and validation live in helpers; the sink orchestrates validation at init and path resolution per record, reusing existing key template and handle lifecycle.

## Component Responsibilities

| Component | Responsibility |
|-----------|-----------------|
| **GCSTarget** (`target_gcs/target.py`) | Config schema: add `hive_partitioned` (bool, default false); remove `partition_date_field` and `partition_date_format`. Sink creation unchanged. |
| **GCSSink** (`target_gcs/sinks.py`) | Use `hive_partitioned` (not `partition_date_field`) to choose partition vs flat/chunked. When `hive_partitioned`: at init, if schema has `x-partition-fields`, call `validate_partition_fields_schema`; per record, call `get_partition_path_from_schema_and_record` to get partition path; pass to existing `_build_key_for_record` and handle lifecycle (partition change → close handle, clear state). Key template still uses `{partition_date}` / `{hive}` for the full path. |
| **partition_path** (`target_gcs/helpers/partition_path.py`) | New: `get_partition_path_from_schema_and_record(schema, record, fallback_date, *, partition_date_format)`. Read `x-partition-fields`; if missing/empty return fallback_date formatted; else for each field append one segment (date → Hive date path, else literal); join with `/`. Reuse existing date-formatting and dateutil parse logic. Internal helper for “date vs literal” per field. |
| **partition_schema** (`target_gcs/helpers/partition_schema.py`) | New: `validate_partition_fields_schema(stream_name, schema, partition_fields)`. For each field: in properties, in required, non-nullable (type not only null). Raise `ValueError` with stream name and reason. |
| **helpers/__init__.py** | Export `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema`. Keep or deprecate old exports only if still used; sink will use new API. |

## Data Flow

1. **Config load**: Target loads config; `hive_partitioned` defaults to false.
2. **Sink init**: If `config.get("hive_partitioned")` and `schema.get("x-partition-fields")` is present, call `validate_partition_fields_schema(stream_name, schema, schema["x-partition-fields"])`. On failure, `ValueError` aborts.
3. **Record processing**: If `hive_partitioned`, partition_path = `get_partition_path_from_schema_and_record(self.schema, record, self.fallback, partition_date_format=...)`. Else (flat/chunked) use existing non-partition path logic.
4. **Key and handle**: Same as today: partition_path feeds `_build_key_for_record`; key template uses `{partition_date}`; on partition change, close handle and clear state; next write gets new key.

## Design Patterns

- **Dependency injection**: Sink already receives `date_fn` for fallback date; use it when building path from schema+record when `x-partition-fields` is missing or empty. No new DI for path builder (schema/record/fallback_date are explicit).
- **Validation at boundary**: Validate partition fields once at sink init when `hive_partitioned` and `x-partition-fields` present; do not re-validate per record (validation-over-testing rule).
- **Single responsibility**: Path builder returns a string; validator raises or returns None. Sink owns orchestration and key/handle lifecycle.
- **Existing patterns**: Follow `AI_CONTEXT_PATTERNS.md` (config via schema, time/date injectable, black-box tests). Reuse `DEFAULT_PARTITION_DATE_FORMAT` and dateutil parsing from `partition_path.py`.

## References

- Current partition path format: `DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"` in `target_gcs/sinks.py`.
- Singer schema: stream schema dict from SCHEMA message; `x-` keys are custom (e.g. `x-singer.decimal`); we define `x-partition-fields`.
- Key template tokens: `{stream}`, `{partition_date}`, `{hive}`, `{timestamp}`, `{format}`, `{chunk_index}` when chunking.
