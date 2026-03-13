# Task 04 — Config schema (target)

## Background

The target config must expose `hive_partitioned` (boolean, default false) and no longer expose `partition_date_field` or `partition_date_format`. This task updates the target's JSON schema only; no dependency on helper implementation tasks.

## This Task

- **File:** `loaders/target-gcs/target_gcs/target.py`
  - In `config_jsonschema`: add `th.Property("hive_partitioned", th.BooleanType, required=False, default=False, description="When true, enable Hive-style partitioning from stream schema (x-partition-fields) or current date.")`.
  - Remove `th.Property("partition_date_field", ...)` and `th.Property("partition_date_format", ...)`.

## Testing Needed

- **File:** `loaders/target-gcs/tests/test_sinks.py` (or existing config test location)
  - Assert config schema has "hive_partitioned" in properties; type boolean; not required or default false.
  - Assert "partition_date_field" and "partition_date_format" are not in config_jsonschema["properties"].
