# Selected Solution — Schema-driven Hive Partitioning

Internal implementation: extend existing helpers and sink logic; no new external libraries.

## Config

- Add `hive_partitioned: bool` (default `false`) to target config. When true, partition path is driven by stream schema and record; when false, retain current non-hive behaviour (flat or chunked single key). Remove config-driven `partition_date_field` / `partition_date_format` (backward compatibility not required).

## Schema convention

- Stream schema may include `x-partition-fields: ["field1", "field2", ...]` (array of property names, order = path order). If absent when `hive_partitioned` is true, partition path = current date only (existing Hive date segment).

## Algorithms and interfaces

**1. Validation** (`partition_schema.py`)

- New function: `validate_partition_fields_schema(stream_name: str, schema: dict, partition_fields: list[str]) -> None`.
- For each `field` in `partition_fields`: assert `field` in `schema.get("properties", {})`; assert `field` in `schema.get("required", [])`; assert property type is not null-only (same logic as current validator: non_null types exist). On failure raise `ValueError` with stream name, field name, and reason.

**2. Path building** (`partition_path.py`)

- New function: `get_partition_path_from_schema_and_record(schema: dict, record: dict, fallback_date: datetime, *, partition_date_format: str = DEFAULT_PARTITION_DATE_FORMAT) -> str`.
- Read `partition_fields = schema.get("x-partition-fields")`. If missing or empty, return `fallback_date.strftime(partition_date_format)` (single Hive date segment).
- For each `field` in `partition_fields`: get `value = record.get(field)`. If value is date-parseable (use schema `format` for "date"/"date-time" if present; else try dateutil parse): append one segment `YEAR=.../MONTH=.../DAY=...` (reuse existing strftime with `partition_date_format`). Else: append one segment = string representation of value (literal folder); sanitize so path has no embedded slashes (e.g. replace or reject).
- Join segments with `/` and return.

**3. Date vs literal**

- Internal helper: given property schema and value, decide “date” vs “literal”. If `prop_schema.get("format")` in `("date", "date-time")` → date. Else if value is `datetime` or `date` → date. Else if value is str and dateutil.parser.parse(value) succeeds → date. Else → literal (str(value), sanitized for path).

## How it fits together

- **Target** (`target.py`): Add `hive_partitioned` to config_jsonschema; remove partition_date_field / partition_date_format from schema (and meltano.yml).
- **Sink** (`sinks.py`): If `config.get("hive_partitioned")`: at init, if schema has `x-partition-fields`, call `validate_partition_fields_schema(stream_name, schema, schema["x-partition-fields"])`. In record processing, call `get_partition_path_from_schema_and_record(self.schema, record, self.fallback, partition_date_format=...)` to get `partition_path`; pass to existing key/handle logic (same as current partition path change → close handle, clear state, new key on next write). Key template still uses `{partition_date}` (and `{hive}`) for the full path. When `hive_partitioned` is false, keep current behaviour (no record-driven partition).
- **Helpers** (`__init__.py`): Export `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema`; keep or deprecate `get_partition_path_from_record` / `validate_partition_date_field_schema` only if still used (e.g. for date-only fallback path internally).

## References

- Existing path format: `DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"` in sinks.py; same for date segments.
- Singer schema: stream schema is the dict passed to the sink (e.g. from SCHEMA message); x- keys are custom and valid in JSON Schema.
- Date parsing: continue using `dateutil.parser.parse` for string values; no API reference beyond current usage in `partition_path.py`.
