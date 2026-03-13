# Interfaces — Schema-driven Hive Partitioning

## Public Interfaces

### 1. `get_partition_path_from_schema_and_record`

- **Module**: `target_gcs.helpers.partition_path`
- **Signature**:
  ```python
  def get_partition_path_from_schema_and_record(
      schema: dict,
      record: dict,
      fallback_date: datetime,
      *,
      partition_date_format: str = "year=%Y/month=%m/day=%d",
  ) -> str
  ```
- **Behaviour**: Reads `partition_fields = schema.get("x-partition-fields")`. If missing or empty, returns `fallback_date.strftime(partition_date_format)`. Otherwise, for each `field` in `partition_fields`: get `value = record.get(field)`; if value is date-parseable (schema `format` "date"/"date-time", or value is date/datetime, or string parseable by dateutil), append one segment `YEAR=.../MONTH=.../DAY=...` using `partition_date_format`; else append one segment = path-safe string of value (literal folder). Join segments with `/` and return.
- **Date vs literal**: If property has `format` in `("date", "date-time")` → date. Else if value is `datetime` or `date` → date. Else if value is str and dateutil.parser.parse(value) succeeds → date. Else → literal (str(value), sanitized: no embedded `/`).
- **Literal sanitization**: Replace `/` in literal values with a safe character (e.g. `_`) or reject; document in README. No new dependency.
- **Raises**: `ParserError` from dateutil when a string is parsed as date and fails (propagate to caller; same as current `get_partition_path_from_record`).

### 2. `validate_partition_fields_schema`

- **Module**: `target_gcs.helpers.partition_schema`
- **Signature**:
  ```python
  def validate_partition_fields_schema(
      stream_name: str,
      schema: dict,
      partition_fields: list[str],
  ) -> None
  ```
- **Behaviour**: For each `field` in `partition_fields`: assert `field` in `schema.get("properties", {})`; assert `field` in `schema.get("required", [])` (if `required` is not a list, treat as error); assert property type is not null-only (same as current validator: at least one non-null type). On first failure raise `ValueError` with message including `stream_name`, `field`, and reason (e.g. "is not in schema", "must be required for the stream", "is null-only").
- **Returns**: None on success.
- **Raises**: `ValueError` only.

### 3. Config schema (GCSTarget)

- **Add**: `th.Property("hive_partitioned", th.BooleanType, required=False, default=False, description="When true, enable Hive-style partitioning from stream schema (x-partition-fields) or current date.")`.
- **Remove**: `partition_date_field`, `partition_date_format` from `config_jsonschema` (and from meltano.yml).

### 4. GCSSink behaviour contract

- **Partition enablement**: Use `config.get("hive_partitioned")` (truthy) to decide partition-by-field vs flat/chunked. When true, partition path comes from `get_partition_path_from_schema_and_record`; when false, retain current non-hive behaviour (no record-driven partition).
- **Init**: When `hive_partitioned` is true and `schema.get("x-partition-fields")` is present (non-empty list), call `validate_partition_fields_schema(stream_name, schema, schema["x-partition-fields"])` before any record processing. Set `_current_partition_path` and related state when partition-by-field is on.
- **Record processing**: When `hive_partitioned`, resolve path with `get_partition_path_from_schema_and_record(self.schema, record, self.fallback, partition_date_format=...)`; pass to `_build_key_for_record(record, partition_path)`. Key template and handle lifecycle unchanged: partition change → close handle, clear state, next write gets new key.
- **Effective key template**: When `hive_partitioned` is true and user did not set `key_naming_convention`, use `DEFAULT_KEY_NAMING_CONVENTION_HIVE` (same as today when partition-by-field was on). When `hive_partitioned` is false, use `DEFAULT_KEY_NAMING_CONVENTION` or user override.

## Data Conventions

- **Stream schema**: Singer/JSON Schema dict; may include `x-partition-fields: list[str]` (array of property names, order = path order).
- **Partition path string**: Segments joined by `/`; each segment either `year=YYYY/month=MM/day=DD` (from one date field) or a single path-safe folder name (no `/`).

## Dependencies Between Interfaces

- Sink depends on `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema`; helpers do not depend on sink or target.
- Path builder uses optional `partition_date_format` (default matches `DEFAULT_PARTITION_DATE_FORMAT` in sinks); sink passes it from config when we add an optional config for it later, or use default for now.
- Validator is pure: schema + list of field names → None or ValueError.
