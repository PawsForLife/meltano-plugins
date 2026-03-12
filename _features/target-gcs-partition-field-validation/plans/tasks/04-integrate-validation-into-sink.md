# Task Plan: 04-integrate-validation-into-sink

## Overview

This task **wires the partition-date-field schema validation helper into the GCSSink** so that misconfiguration is caught at sink initialization. When `partition_date_field` is set in config, the sink calls `validate_partition_date_field_schema(stream_name, field_name, schema)` after `super().__init__` and after initializing `_current_partition_path`. No changes are made to `process_record`, `_build_key_for_record`, or other methods. This task depends on task 02 (helper implemented and exported from `target_gcs.helpers`) and task 03 (sink integration tests added); its completion makes those integration tests pass.

**Scope:** One production file change (`sinks.py`): add import and a single validation call in `GCSSink.__init__`. No new tests are written in this task (tests exist from task 03).

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | **Modify.** Add import for `validate_partition_date_field_schema` from `target_gcs.helpers`; in `GCSSink.__init__`, after the block that sets `_current_partition_path` when `partition_date_field` is set, add a conditional call to the helper and a short comment. |

**No other files** are created or modified. The helper module and its tests live in tasks 01–02; sink integration tests live in task 03.

---

## Test Strategy

- **No new tests in this task.** Task 03 adds sink integration tests in `tests/test_sinks.py` that construct the sink with `partition_date_field` and various schemas; those tests fail until this task adds the validation call.
- **TDD context:** The tests already exist (from task 03). This task implements the integration so those tests pass.
- **Run after implementation:**  
  `uv run pytest tests/helpers/test_partition_schema.py tests/test_sinks.py -v`  
  and full suite:  
  `uv run pytest`  
  from `loaders/target-gcs/`. All must pass (no regressions).

---

## Implementation Order

1. **Import:** In `loaders/target-gcs/target_gcs/sinks.py`, add `validate_partition_date_field_schema` to the existing import from `.helpers` (e.g. `from .helpers import _json_default, get_partition_path_from_record, validate_partition_date_field_schema`). If task 02 placed the helper in a submodule (e.g. `partition_schema`), import from the same location used by tests: `from target_gcs.helpers import validate_partition_date_field_schema` (or `from .helpers.partition_schema import ...` if exported only there). Use the export path established in task 02 so that `from target_gcs.helpers import validate_partition_date_field_schema` works.
2. **Call site:** In `GCSSink.__init__`, immediately after the block that sets `_current_partition_path` when `partition_date_field` is set (i.e. after `if self.config.get("partition_date_field"): self._current_partition_path = None`), add:
   - A short comment: e.g. "Validate partition_date_field against stream schema when set; raises ValueError if missing or not date-parseable."
   - Code: if `self.config.get("partition_date_field")`, call `validate_partition_date_field_schema(self.stream_name, self.config["partition_date_field"], self.schema)`.
3. **No other edits:** Do not change `process_record`, `_build_key_for_record`, `key_name`, or any other method. Do not add constructor parameters.
4. **Lint/typecheck:** From `loaders/target-gcs/`, run `uv run ruff check .`, `uv run ruff format --check`, `uv run mypy target_gcs` and fix any issues.

---

## Validation Steps

1. **Helper and sink tests:**  
   `uv run pytest tests/helpers/test_partition_schema.py tests/test_sinks.py -v`  
   — all tests pass.
2. **Full target-gcs suite:**  
   `uv run pytest`  
   from `loaders/target-gcs/` — no new failures (excluding explicitly xfail).
3. **Lint/format/typecheck:**  
   `uv run ruff check .`  
   `uv run ruff format --check`  
   `uv run mypy target_gcs`  
   — all pass.
4. **Acceptance:** Existing tests in `tests/test_sinks.py` and elsewhere continue to pass; no regression. Sink integration tests (task 03) now pass because the sink performs validation in `__init__` when `partition_date_field` is set.

---

## Documentation Updates

- **None required for this task.** Code comment at the call site is sufficient. Broader feature documentation and changelog are handled in task 05.
