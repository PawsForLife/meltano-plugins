# Task Plan: 09 — Helpers Cleanup

## Overview

This task removes dead code and standardizes imports after PartitionedPath (task 07) migrates to `hive_path(record)` for key building. `get_partition_path_from_schema_and_record` in `helpers/partition_path.py` becomes unused and is removed. `DEFAULT_PARTITION_DATE_FORMAT` is confirmed as a single source in `constants.py`; any imports from `helpers.partition_path` are switched to `constants`.

**Scope:** `helpers/partition_path.py`, `helpers/__init__.py`, `tests/unit/helpers/test_partition_path.py`, and import paths for `DEFAULT_PARTITION_DATE_FORMAT`.

**Dependencies:** Tasks 01–08 must be complete. Task 07 removes `get_partition_path_from_schema_and_record` usage from PartitionedPath; task 06 migrates DatedPath to import `DEFAULT_PARTITION_DATE_FORMAT` from constants.

---

## Files to Create/Modify

### 1. `loaders/target-gcs/target_gcs/helpers/partition_path.py`

**Action:** Delete the file.

**Rationale:** After task 07, `get_partition_path_from_schema_and_record` is the only symbol in this module and is unused. PartitionedPath uses `hive_path(record)` from `_partitioned`; DatedPath uses extraction date directly. No other module depends on this function.

### 2. `loaders/target-gcs/target_gcs/helpers/__init__.py`

**Changes:**
- Remove `from .partition_path import get_partition_path_from_schema_and_record`.
- Remove `"get_partition_path_from_schema_and_record"` from `__all__`.

**Retain:** `_json_default`, `validate_partition_date_field_schema`, `validate_partition_fields_schema`.

### 3. `loaders/target-gcs/target_gcs/paths/dated.py`

**Changes (if not already done in task 06):**
- Replace `from target_gcs.helpers.partition_path import DEFAULT_PARTITION_DATE_FORMAT` with `from target_gcs.constants import DEFAULT_PARTITION_DATE_FORMAT`.

**Verification:** Task 06 plan specifies importing from `target_gcs.constants`. If task 06 already updated this, no change needed; otherwise apply the fix.

### 4. `loaders/target-gcs/target_gcs/paths/partitioned.py`

**Changes (if not already done in task 07):**
- Remove `from target_gcs.helpers.partition_path import DEFAULT_PARTITION_DATE_FORMAT` (PartitionedPath no longer uses it after migration to `path_for_record` + `hive_path`).
- Remove `from target_gcs.helpers import get_partition_path_from_schema_and_record`.

**Verification:** Task 07 removes all usage of `get_partition_path_from_schema_and_record` and `DEFAULT_PARTITION_DATE_FORMAT` from PartitionedPath. If task 07 left any stray imports, remove them here.

### 5. `loaders/target-gcs/tests/unit/helpers/test_partition_path.py`

**Action:** Delete the file.

**Rationale:** All tests target `get_partition_path_from_schema_and_record`, which is removed. No retained helpers in `partition_path.py` to test.

---

## Test Strategy

**TDD note:** This task is cleanup/removal. No new tests are written. Existing tests for the removed function are deleted.

**Pre-implementation verification:**
1. Grep for `get_partition_path_from_schema_and_record` — confirm only definition, export, and test file reference it.
2. Grep for `DEFAULT_PARTITION_DATE_FORMAT` — confirm single definition in `constants.py`; consumers (`_partitioned/string_functions.py`, `dated.py`) import from constants.

**Post-implementation:**
- Run full test suite; no tests should reference the removed function.
- `test_partition_schema.py` and `test_json_parsing.py` remain; they test other helpers.

---

## Implementation Order

1. **Verify usage** — Grep `get_partition_path_from_schema_and_record` and `DEFAULT_PARTITION_DATE_FORMAT` to confirm removal scope and import consistency.
2. **Update helpers/__init__.py** — Remove `get_partition_path_from_schema_and_record` import and `__all__` entry.
3. **Fix import paths** — Ensure `dated.py` and `partitioned.py` import `DEFAULT_PARTITION_DATE_FORMAT` from `constants` only (or remove unused imports).
4. **Delete partition_path.py** — Remove the module file.
5. **Delete test_partition_path.py** — Remove the test file.
6. **Run tests** — `uv run pytest` from `loaders/target-gcs/`; all pass.
7. **Run linters** — `uv run ruff check .` and `uv run mypy target_gcs`; no errors.

---

## Validation Steps

1. **Grep verification:** `get_partition_path_from_schema_and_record` has no references in source or tests.
2. **Import consistency:** `DEFAULT_PARTITION_DATE_FORMAT` is defined only in `constants.py`; `_partitioned/string_functions.py` and `dated.py` import from `target_gcs.constants`.
3. **Test suite:** `uv run pytest` from `loaders/target-gcs/` — all pass.
4. **Lint/type:** `uv run ruff check .` and `uv run mypy target_gcs` — no violations.
5. **Public API:** `from target_gcs.helpers import get_partition_path_from_schema_and_record` raises `ImportError`.

---

## Documentation Updates

| Document | Change |
|----------|--------|
| `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` | Remove references to `get_partition_path_from_schema_and_record`; update "Constant" section to state `DEFAULT_PARTITION_DATE_FORMAT` is in `target_gcs.constants`; remove "Partition resolution" guidance that mentions reusing `get_partition_path_from_schema_and_record`. |
| `loaders/target-gcs/CHANGELOG.md` | Add entry: removed `get_partition_path_from_schema_and_record` and `helpers/partition_path.py`; `DEFAULT_PARTITION_DATE_FORMAT` single source in `constants.py`. |

---

## Acceptance Criteria

- [ ] `get_partition_path_from_schema_and_record` removed; no dead code.
- [ ] `helpers/partition_path.py` deleted.
- [ ] `DEFAULT_PARTITION_DATE_FORMAT` has single source in `constants.py`; all consumers import from there.
- [ ] `helpers/__init__.py` no longer exports `get_partition_path_from_schema_and_record`.
- [ ] `tests/unit/helpers/test_partition_path.py` deleted.
- [ ] All tests pass; ruff and mypy pass.
- [ ] AI context and CHANGELOG updated.
