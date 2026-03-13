# Task Plan: 03 — Helper exports

## Overview

This task updates the helpers package public API so the sink (and any other callers) can import the new schema-driven partition functions from a single entry point. It adds exports for `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema` to `target_gcs.helpers` and documents that removal of the legacy exports is deferred until the sink is migrated (later tasks).

**Scope**: Only `loaders/target-gcs/target_gcs/helpers/__init__.py`. No new modules; implementations live in `partition_path.py` and `partition_schema.py` (tasks 01 and 02).

**Dependencies**: Tasks 01 (validator implementation) and 02 (path builder implementation) must be complete so the symbols exist before exporting.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/helpers/__init__.py` | Modify: add imports for `get_partition_path_from_schema_and_record` (from `.partition_path`) and `validate_partition_fields_schema` (from `.partition_schema`); add both names to `__all__`. Do **not** remove `get_partition_path_from_record` or `validate_partition_date_field_schema` in this task—the sink still uses them until tasks 05–07. Removal of legacy exports is done when the sink no longer references them (see implementation order). |

**No new files.** No changes to `partition_path.py`, `partition_schema.py`, or sink in this task.

---

## Test Strategy

- **No new test file.** Reuse existing helper test layout.
- **Import verification**: Add one test that asserts the new functions are importable from the public API and are callable. Options:
  - **Option A (recommended)**: In `tests/helpers/test_partition_schema.py`, add a test that imports `validate_partition_fields_schema` from `target_gcs.helpers` and calls it with valid args (stream_name, schema with required property, partition_fields list); assert no exception. In `tests/helpers/test_partition_path.py`, add a test that imports `get_partition_path_from_schema_and_record` from `target_gcs.helpers` and calls it with minimal schema/record/fallback_date; assert return type is str. This validates both exports and that they are the correct callables.
  - **Option B**: Single test in either file that does `from target_gcs.helpers import get_partition_path_from_schema_and_record, validate_partition_fields_schema` and asserts `callable(get_partition_path_from_schema_and_record)` and `callable(validate_partition_fields_schema)`.
- **Regression**: Existing tests that import `get_partition_path_from_record` and `validate_partition_date_field_schema` from `target_gcs.helpers` must continue to pass (legacy exports remain in this task).

---

## Implementation Order

1. **Update `helpers/__init__.py`**
   - Add: `from .partition_path import get_partition_path_from_schema_and_record` (alongside existing `get_partition_path_from_record`).
   - Add: `from .partition_schema import validate_partition_fields_schema` (alongside existing `validate_partition_date_field_schema`).
   - Extend `__all__` with `"get_partition_path_from_schema_and_record"` and `"validate_partition_fields_schema"` (order: keep existing order, append new names or group new names together for clarity).
2. **Add import tests (TDD: add test first, then confirm it passes after step 1)**
   - In `test_partition_schema.py`: add test that imports `validate_partition_fields_schema` from `target_gcs.helpers` and runs it with a valid schema/partition_fields; no exception.
   - In `test_partition_path.py`: add test that imports `get_partition_path_from_schema_and_record` from `target_gcs.helpers` and runs it with schema `{}`, any record, and a fixed fallback_date; assert result is a non-empty string (fallback path).
3. **Do not remove legacy exports** in this task. Sink still uses `get_partition_path_from_record` and `validate_partition_date_field_schema`. Removal is part of the sink migration (tasks 05–07) when those symbols are no longer used.

---

## Validation Steps

1. From `loaders/target-gcs/`: run `uv run pytest tests/helpers/ -v` — all tests pass, including the new import/usage tests.
2. Run full test suite: `uv run pytest` — no regressions.
3. Manual check: `python -c "from target_gcs.helpers import get_partition_path_from_schema_and_record, validate_partition_fields_schema; print('OK')"` succeeds from `loaders/target-gcs/` with venv active.
4. Lint/type-check: `uv run ruff check target_gcs/` and `uv run mypy target_gcs` pass.

---

## Documentation Updates

- **None required** for this task. Public API is reflected by `__all__` and docstrings on the functions (in tasks 01 and 02). README and Meltano docs are updated in task 09; no mention of `helpers/__init__.py` exports there.

---

## Notes

- **Backward compatibility**: Feature plan states no backward compatibility for the old partition config. Legacy helper exports are kept only until the sink is migrated; once tasks 05–07 remove sink usage of `get_partition_path_from_record` and `validate_partition_date_field_schema`, a follow-up change (or explicit step in one of those tasks) should remove them from `__init__.py` and `__all__` and update any remaining test imports to use the new API or direct module imports.
