# Task 07 — Sink process_record dispatch

## Overview

This task wires the sink’s public `process_record` entry point to the correct code path based on the `hive_partitioned` config flag. When `hive_partitioned` is true, records are processed by the hive-partition record method (schema + record → partition path, handle lifecycle on partition change). When false, records use the existing non-partition path (single-file or chunked). No new behaviour is implemented here; only the dispatch condition and docstring are updated to use `hive_partitioned` instead of `partition_date_field`. Task 06 provides the hive-partition record method that uses `get_partition_path_from_schema_and_record`; task 05 ensures init and key template already key off `hive_partitioned`.

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Modify `process_record`: dispatch on `self.config.get("hive_partitioned")`; call hive-partition method when true, `_process_record_single_or_chunked` when false; update docstring to describe dispatch by `hive_partitioned`. |

No new files. No changes to config schema, helpers, or tests in this task (config in 04, init in 05, record-processing implementation in 06, sink/key tests in 08).

## Test Strategy

- **No new tests in this task.** The task description and master plan assign coverage to task 08: black-box tests that with `hive_partitioned: false` records go to the non-partition path, and with `hive_partitioned: true` records go through the hive partition path and keys contain expected segments.
- **TDD for this task:** Optional: add a minimal test that builds a sink with `hive_partitioned: true` and one with `hive_partitioned: false`, calls `process_record` with a record, and asserts the resulting key (or written path) matches expectations (non-partition vs partition path). If added, it belongs in task 08’s test file; this task only changes the dispatch condition.
- **Validation:** After implementation, run the full test suite; any existing tests that still reference `partition_date_field` in sink behaviour will have been updated in tasks 04/05/08, so no test should assume `partition_date_field` controls dispatch.

## Implementation Order

1. **Update `process_record` in `sinks.py`**
   - Replace the dispatch condition: use `self.config.get("hive_partitioned")` instead of `self.config.get("partition_date_field")`.
   - Keep the same two branches: when true, call the hive-partition record method (the method that uses `get_partition_path_from_schema_and_record` and handles partition change; after task 06 it may be named `_process_record_partition_by_field` or `_process_record_hive_partitioned`—call whichever method implements that behaviour). When false, call `_process_record_single_or_chunked(record, context)`.
   - Update the docstring: state that dispatch is by `hive_partitioned`; when true, the partition-by-field (hive) path is used; when false, the single-file or chunked path is used. Remove references to `partition_date_field`.

2. **No other changes**
   - Do not change `_process_record_partition_by_field` / `_process_record_hive_partitioned` or `_process_record_single_or_chunked` in this task; that is task 06.
   - Do not change init, config, or key template in this task; that is task 05 and 04.

## Validation Steps

1. **Code review:** Confirm `process_record` reads only `hive_partitioned` (not `partition_date_field`) and that both branches call the correct methods.
2. **Regression:** Run the project test suite (e.g. `pytest loaders/target-gcs/tests/` or project-defined test command). All tests pass (any tests still expecting `partition_date_field`-driven dispatch will have been updated in prior tasks).
3. **Docstring:** Confirm the docstring describes dispatch by `hive_partitioned` and no longer mentions `partition_date_field` for this method.

## Documentation Updates

- **Code docstring:** Update the `process_record` docstring in `sinks.py` to describe dispatch by `hive_partitioned` and the two code paths (hive partition vs single/chunked). No README or external docs change in this task; those are in task 09.

## Dependencies

- **Requires:** Task 05 (sink init and key template use `hive_partitioned`), Task 06 (hive-partition record method exists and uses `get_partition_path_from_schema_and_record`). Config schema (04) and helpers (01–03) must be in place so that `hive_partitioned` exists and the hive method can resolve paths.
- **Blocks:** Task 08 (sink and key tests) can assume `process_record` dispatches on `hive_partitioned` when writing black-box tests.
