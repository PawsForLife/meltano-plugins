# Documentation — Schema-driven Hive Partitioning

## User-Facing

### README.md (`loaders/target-gcs/README.md`)

- **Config**: Document `hive_partitioned` (boolean, default false). When true, Hive-style partitioning is enabled; partition path is built from stream schema and record (see Schema extension), or from current date when the stream schema does not define partition fields.
- **Schema extension**: Document `x-partition-fields`: array of property names on the **stream** schema (top-level, alongside `properties` / `required`). Order of the array is the order of path segments. Example: `"x-partition-fields": ["region", "event_date"]` → paths like `region_value/year=2024/month=03/day=11/...`.
- **Field rules**: Each field in `x-partition-fields` must exist in `schema["properties"]`, be listed in `schema["required"]`, and be non-nullable (type not only `"null"`). Validation runs at sink initialization; invalid schema raises an error with a clear message.
- **Field semantics**: For each partition field, if the value is date-parseable (schema `format` "date"/"date-time", or value is date/datetime, or string parseable as date), the segment is Hive date form `year=YYYY/month=MM/day=DD`. Otherwise the value is used as a literal folder name (path-safe; e.g. slashes in values are replaced).
- **Removal**: Note that `partition_date_field` and `partition_date_format` are no longer supported; use `hive_partitioned` and `x-partition-fields` instead.

Keep README concise; do not duplicate full config schema (that stays in code/Meltano).

### Meltano (`loaders/target-gcs/meltano.yml`)

- Add setting for `hive_partitioned` (boolean, default false). Remove or omit `partition_date_field` and `partition_date_format` from the plugin definition.

## Code Documentation

### Docstrings (Google style)

- **get_partition_path_from_schema_and_record**: One-line summary; Args (schema, record, fallback_date, partition_date_format); Returns (path string); Raises (ParserError when date string unparseable). Note behaviour when x-partition-fields missing or empty (fallback date); date vs literal rule; literal sanitization.
- **validate_partition_fields_schema**: Summary; Args (stream_name, schema, partition_fields); Returns None; Raises ValueError with message including stream name and reason.
- **GCSSink**: Update class docstring to mention hive_partitioned and x-partition-fields; partition path from schema+record or current date when hive_partitioned is true.
- **GCSTarget.config_jsonschema**: Property description for hive_partitioned already specified in interfaces.md.

### Inline comments

- In partition_path: brief comment for date vs literal branch (e.g. "Schema format or dateutil parse → date segment; else literal segment.").
- In sinks: comment that effective key template uses hive default when hive_partitioned is true.

## AI Context Updates

### docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md

- **Config schema**: Update to list `hive_partitioned` (boolean, default false); remove `partition_date_field` and `partition_date_format`.
- **Partition-by-field behaviour**: Replace "When partition_date_field is set" with "When hive_partitioned is true". Describe path from schema (x-partition-fields) and record; fallback to current date when x-partition-fields absent; validation at init for required/non-nullable.
- **Public interfaces**: Replace or add:
  - `get_partition_path_from_schema_and_record(schema, record, fallback_date, *, partition_date_format=...)` in `target_gcs.helpers.partition_path`.
  - `validate_partition_fields_schema(stream_name, schema, partition_fields)` in `target_gcs.helpers.partition_schema`.
- **Partition-date-field validation**: Rename or replace with "Partition fields validation (sink init)": when hive_partitioned and x-partition-fields present, validate_partition_fields_schema is called; each field must be in properties, required, non-nullable.

Do not invent behaviour not in the plan; update to reflect implemented behaviour after implementation.

## Changelog

- **loaders/target-gcs/CHANGELOG.md**: Add entry for the feature: schema-driven Hive partitioning; new config `hive_partitioned`; stream schema `x-partition-fields`; removal of `partition_date_field` and `partition_date_format`. One short paragraph; link to README for usage.
