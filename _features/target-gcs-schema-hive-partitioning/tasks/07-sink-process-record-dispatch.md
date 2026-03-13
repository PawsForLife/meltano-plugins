# Task 07 — Sink process_record dispatch

## Background

`process_record` must dispatch to the hive-partitioned path when `hive_partitioned` is true, and to the existing non-partition path otherwise. Depends on task 06 (record processing method exists).

## This Task

- **File:** `loaders/target-gcs/target_gcs/sinks.py`
  - In `process_record`: when `self.config.get("hive_partitioned")` call the partition-by-field path (the method that uses `get_partition_path_from_schema_and_record`); else call `_process_record_single_or_chunked` (or the existing non-partition code path).

## Testing Needed

- Covered by task 08: black-box tests that with hive_partitioned false records go to non-partition path, and with hive_partitioned true records go through the hive partition path and keys contain expected segments.
