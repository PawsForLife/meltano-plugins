# Task 06 — Sink record processing

## Background

When `hive_partitioned` is true, the partition path for each record must come from `get_partition_path_from_schema_and_record`. The sink compares this path to `_current_partition_path`; on change it closes the handle and clears state, then builds the key with `_build_key_for_record(record, partition_path)`. Depends on tasks 02 (path builder), 03 (exports), 05 (sink init).

## This Task

- **File:** `loaders/target-gcs/target_gcs/sinks.py`
  - In the method that processes records with partition-by-field (e.g. `_process_record_partition_by_field` or renamed `_process_record_hive_partitioned`): obtain partition_path via `get_partition_path_from_schema_and_record(self.schema, record, self.fallback, partition_date_format=DEFAULT_PARTITION_DATE_FORMAT)`. Use the constant from sinks or helpers (plan: config no longer has partition_date_format; use default in code).
  - Rest unchanged: compare partition_path to _current_partition_path; on change close handle and clear state; build key with _build_key_for_record(record, partition_path); write record.
  - Rename method to something like `_process_record_hive_partitioned` if desired for clarity.

## Testing Needed

- Covered by task 08 (sink and key generation tests). This task does not add new test files; ensure existing partition key tests that will be updated in 08 still pass after this change, or are updated in 08.
