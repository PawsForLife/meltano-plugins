# New Systems — Schema-driven Hive Partitioning

New modules, interfaces, and behaviour to add.

## Config

- **Setting**: `hive_partitioned: bool`, default `false`. When true, enable hive partitioning; partition path is derived from stream schema and record (or current date when schema has no `x-partition-fields`). No config-driven partition field names.

## Stream schema extension

- **Convention**: `x-partition-fields: ["field1", "field2", ...]` on the **stream** schema (top-level, alongside `properties` / `required`). Order of the array defines path order.
  - If present and `hive_partitioned` is true: use these fields (in order) to build the partition path.
  - If absent and `hive_partitioned` is true: use current date for partition path (single segment, existing YEAR=.../MONTH=.../DAY=... behaviour).
  - If `hive_partitioned` is false: ignore; no hive path.

## Partition field rules

- Each field in `x-partition-fields` must:
  - Exist in `schema["properties"]`.
  - Be listed in `schema["required"]`.
  - Be non-nullable (type not only `"null"`).
- Validation runs at sink init when `hive_partitioned` is true and `x-partition-fields` is present. On failure: raise `ValueError` with stream name and reason (e.g. field not in schema, not required, null-only).

## Field semantics (path segment)

- For each field in `x-partition-fields`, read value from record:
  - **Date-parseable**: Prefer schema format hint (`format: "date"` / `"date-time"`); fallback to parse attempt (e.g. dateutil). Use existing Hive date structure: `YEAR=.../MONTH=.../DAY=...` (single segment).
  - **Otherwise**: Treat as enum; use the value as a literal folder name (one segment). Ensure safe for path (e.g. no slashes; normalize or reject if needed).
- Path order = order of fields: e.g. `[my_enum, my_date]` → `my_enum_value/year=.../month=.../day=.../timestamp.jsonl`.

## New/updated interfaces

- **Partition path builder** (in `partition_path` or new module):  
  `get_partition_path_from_schema_and_record(schema: dict, record: dict, fallback_date: datetime) -> str`  
  - Reads `x-partition-fields` from schema; if missing, returns `fallback_date` formatted as Hive date path.
  - For each field: resolve segment (date → Hive date path, else literal); join with `/`.  
  - Single responsibility: path string from schema + record + fallback.

- **Schema validator**:  
  `validate_partition_fields_schema(stream_name: str, schema: dict, partition_fields: list[str]) -> None`  
  - Asserts each field in `partition_fields` is in `properties`, in `required`, and non-nullable. Raises `ValueError` with clear message on failure.

- **Date vs enum detection**: Internal helper (or inline) that, given a property schema and optional record value, decides “date” vs “literal”. Use schema `format` and/or parse attempt; default to literal if ambiguous.

## Integration points

- Sink `__init__`: When `config.get("hive_partitioned")` and schema has `x-partition-fields`, call `validate_partition_fields_schema(stream_name, schema, schema["x-partition-fields"])`.
- Sink `_process_record_*`: When `hive_partitioned`, call `get_partition_path_from_schema_and_record(self.schema, record, self.fallback)` to get partition path; rest of handle/key lifecycle unchanged (path change → close handle, clear state, next write gets new key).
