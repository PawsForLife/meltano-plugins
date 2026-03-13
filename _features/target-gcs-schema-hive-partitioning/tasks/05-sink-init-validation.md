# Task 05 — Sink init and validation

## Background

The sink must use `hive_partitioned` instead of `partition_date_field` and, when `hive_partitioned` is true and the stream schema has `x-partition-fields`, call `validate_partition_fields_schema` at init. Depends on tasks 01 (validator), 03 (exports), 04 (config).

## This Task

- **File:** `loaders/target-gcs/target_gcs/sinks.py`
  - Replace all use of `partition_date_field` with `hive_partitioned`. Where the sink checks `if self.config.get("partition_date_field")`, use `if self.config.get("hive_partitioned")`.
  - In `__init__`: when `self.config.get("hive_partitioned")` and `self.schema.get("x-partition-fields")` is a non-empty list, call `validate_partition_fields_schema(self.stream_name, self.schema, self.schema["x-partition-fields"])`.
  - Set `_current_partition_path` when `hive_partitioned` is true (same pattern as before).
  - Remove references to `partition_date_field` and `partition_date_format` from init and from `_get_effective_key_template`. For effective key template: when `hive_partitioned` use hive default template; else use non-partition default or user override.
  - Import `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema` from `.helpers`; remove or keep `get_partition_path_from_record` and `validate_partition_date_field_schema` only if still used (plan: they will not be once path is from schema+record when hive_partitioned).

## Testing Needed

- **File:** `loaders/target-gcs/tests/test_sinks.py`
  - **Sink init with hive_partitioned and invalid x-partition-fields:** Build sink with config hive_partitioned true, schema with x-partition-fields ["missing"] but "missing" not in properties. Expect ValueError when sink is created (or on first use if validation is lazy; plan says init).
  - **Sink init with hive_partitioned and valid x-partition-fields:** Schema has x-partition-fields ["a"]; a in properties and required, non-null. No exception.
