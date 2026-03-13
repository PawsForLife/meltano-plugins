# Task Plan: 06 — Sink record processing

## Overview

This task updates the **record-processing path** inside the sink when Hive partitioning is enabled. The method that today uses `get_partition_path_from_record(record, partition_date_field, format, fallback)` is changed to use `get_partition_path_from_schema_and_record(schema, record, fallback, partition_date_format=...)`, so the partition path is derived from stream schema (`x-partition-fields`) and the record. Config no longer supplies `partition_date_format`; the code uses `DEFAULT_PARTITION_DATE_FORMAT` only. Handle lifecycle (compare path to `_current_partition_path`, close and clear on change, build key with `_build_key_for_record`, write record) stays the same. Optionally the method is renamed to `_process_record_hive_partitioned` for clarity.

**Scope:** `loaders/target-gcs/target_gcs/sinks.py` only. No new test files; tests that cover partition key behaviour are added/updated in task 08. This task keeps behaviour consistent so those tests can pass after 06 and 07.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Modify: (1) Import `get_partition_path_from_schema_and_record` from `.helpers`; remove `get_partition_path_from_record` from imports if no longer used. (2) In the method that processes records when partition-by-field is on (`_process_record_partition_by_field`): obtain `partition_path` via `get_partition_path_from_schema_and_record(self.schema, record, self.fallback, partition_date_format=DEFAULT_PARTITION_DATE_FORMAT)`. (3) Remove use of `self.config.get("partition_date_format")`; use `DEFAULT_PARTITION_DATE_FORMAT` only. (4) Keep existing logic: compare `partition_path` to `_current_partition_path`; on change call `_close_handle_and_clear_state()`, set `_current_partition_path = partition_path`, reset chunk/record counters; build key with `_build_key_for_record(record, partition_path)`; open handle if needed; write record; re-raise `ParserError` from path builder. (5) Rename method to `_process_record_hive_partitioned` and update docstring to refer to `hive_partitioned` and schema-driven path. |

**No new files.** No changes to helpers, target, or tests in this task (tests in 08).

---

## Test Strategy

- **No new tests in this task.** Task 08 adds/updates sink and partition-key tests (hive_partitioned true/false, x-partition-fields, key/path assertions, partition change closing handle).
- **Regression:** After implementation, run the full target-gcs test suite. Any existing tests that call the partition-by-field path may still use `partition_date_field` in config until task 05/07/08 update dispatch and test configs; if task 05 and 07 are done in order, by the time 06 is run the sink will already be using `hive_partitioned` and calling this method from `process_record`. If 06 is executed before 07, `process_record` may still branch on `partition_date_field` (task 07 changes that). So: run tests after 06; fix only regressions caused by this task (e.g. import errors or wrong signature). Full behaviour tests are in 08.
- **Black-box:** When tests run, they must not assert on call counts or log lines; task 08 will assert on keys/paths and observable behaviour.

---

## Implementation Order

1. **Imports in `sinks.py`**
   - Add `get_partition_path_from_schema_and_record` to the import from `.helpers`.
   - Remove `get_partition_path_from_record` from the import list if it is not used elsewhere in the file (after the next step it will only be used in this method, which we are changing).

2. **Rename and update the partition record method**
   - Rename `_process_record_partition_by_field` to `_process_record_hive_partitioned`.
   - Update the docstring to state that the method runs when `hive_partitioned` is true and that the partition path comes from `get_partition_path_from_schema_and_record` (schema + record).

3. **Replace path resolution**
   - Remove: `partition_date_format = self.config.get("partition_date_format") or DEFAULT_PARTITION_DATE_FORMAT` and the call `get_partition_path_from_record(record, self.config["partition_date_field"], partition_date_format, self.fallback)`.
   - Add: `partition_path = get_partition_path_from_schema_and_record(self.schema, record, self.fallback, partition_date_format=DEFAULT_PARTITION_DATE_FORMAT)`.
   - Keep the existing `try`/`except ParserError: raise` so unparseable dates still fail the run.

4. **Leave the rest of the method unchanged**
   - Comparison to `_current_partition_path`, `_close_handle_and_clear_state()`, assignment to `_current_partition_path`, chunk index and record count reset, rotation check, `_build_key_for_record(record, partition_path)`, handle open, write, and record count increment.

5. **Call site (rename only)**
   - In `process_record`, update the call from `_process_record_partition_by_field(record, context)` to `_process_record_hive_partitioned(record, context)`. Do **not** change the condition (e.g. `if self.config.get("partition_date_field")` or `if self.config.get("hive_partitioned")`); that is task 07. This step only keeps the call site using the new method name after the rename.

6. **Run tests and lint**
   - From `loaders/target-gcs/`: `uv run pytest` and `uv run ruff check target_gcs` / `uv run mypy target_gcs`. Fix any regressions (e.g. broken import or call).

---

## Validation Steps

- [ ] `sinks.py` imports `get_partition_path_from_schema_and_record`; `get_partition_path_from_record` removed from imports if unused.
- [ ] The hive partition record method is renamed to `_process_record_hive_partitioned` and uses `get_partition_path_from_schema_and_record(self.schema, record, self.fallback, partition_date_format=DEFAULT_PARTITION_DATE_FORMAT)` with no config for format.
- [ ] Handle lifecycle and write logic unchanged; `ParserError` still re-raised.
- [ ] `process_record` calls `_process_record_hive_partitioned` (not `_process_record_partition_by_field`). The dispatch condition is unchanged in this task (task 07 updates it to `hive_partitioned`).
- [ ] Full test suite in `loaders/target-gcs` passes; ruff and mypy pass.
- [ ] No new test files; no changes to helpers or target in this task.

---

## Documentation Updates

- **None** for this task. README and Meltano docs are updated in task 09. In-code docstring for `_process_record_hive_partitioned` is updated as part of the implementation (describe hive_partitioned and schema-driven path).

---

## Dependencies and Notes

- **Depends on:** Tasks 02 (path builder `get_partition_path_from_schema_and_record`), 03 (helper exports), 05 (sink init and key template use `hive_partitioned`; sink calls this method when `hive_partitioned` is true). Task 04 (config schema) is assumed so that config no longer has `partition_date_format`.
- **Blocks:** Task 07 (dispatch in `process_record` to use `hive_partitioned` and call `_process_record_hive_partitioned`) and task 08 (sink/key tests) depend on this method producing the path from schema and record.
- **Constant:** Use `DEFAULT_PARTITION_DATE_FORMAT` from the same module (already defined in `sinks.py`). Do not read `partition_date_format` from config.
- **Call site:** When renaming to `_process_record_hive_partitioned`, update the single call in `process_record` to use the new name; the dispatch condition (e.g. `hive_partitioned`) is updated in task 07.
