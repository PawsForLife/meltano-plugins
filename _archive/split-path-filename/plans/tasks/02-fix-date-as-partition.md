# Task Plan: 02 — Fix date_as_partition Bug

## Overview

This task fixes a pre-existing bug in `date_as_partition` within `target_gcs/paths/_partitioned/string_functions.py`. The function calls `date_value.strftime(DEFAULT_PARTITION_DATE_FORMAT)` but does not return the result, causing `hive_path(record)` in PartitionedPath to receive `None` for date partition fields. DatedPath and PartitionedPath depend on correct date formatting for path construction.

**Scope:** Single function fix; no config or interface changes. Depends on task 01 (constants) only for `DEFAULT_PARTITION_DATE_FORMAT` import; that constant is unchanged.

---

## Files to Create/Modify

### Modify

| File | Change |
|------|--------|
| `loaders/target-gcs/target_gcs/paths/_partitioned/string_functions.py` | Add `return` before `date_value.strftime(DEFAULT_PARTITION_DATE_FORMAT)` so the formatted string is returned. Ensure both code paths (datetime/date and str) return the result. |

### Create

| File | Purpose |
|------|---------|
| `loaders/target-gcs/tests/unit/paths/_partitioned/test_string_functions.py` | Unit tests for `date_as_partition` and `string_as_partition`; primary focus on `date_as_partition` return value. |

**Note:** Per `.cursor/CONVENTIONS.md`, test path mirrors source: `target_gcs/paths/_partitioned/string_functions.py` → `tests/unit/paths/_partitioned/test_string_functions.py`. Create `_partitioned/` directory under `tests/unit/paths/` if missing.

---

## Test Strategy

**TDD:** Write failing tests first, then implement the fix.

### Test File

`loaders/target-gcs/tests/unit/paths/_partitioned/test_string_functions.py`

### Tests to Write (Order)

1. **`test_date_as_partition_returns_formatted_string_for_datetime`**  
   Given a `datetime` instance, assert `date_as_partition(field_name, field_value)` returns a non-empty string matching `DEFAULT_PARTITION_DATE_FORMAT` (e.g. `year=YYYY/month=MM/day=DD`). Use a fixed datetime for deterministic output.

2. **`test_date_as_partition_returns_formatted_string_for_date`**  
   Given a `date` instance, assert `date_as_partition(field_name, field_value)` returns a non-empty string in the same format.

3. **`test_date_as_partition_returns_formatted_string_for_parseable_string`**  
   Given a parseable date string (e.g. `"2024-03-15"`), assert `date_as_partition(field_name, field_value)` returns a non-empty string in the expected format.

4. **`test_date_as_partition_invalid_type_raises`** (optional)  
   Given an invalid type (e.g. `int`), assert the function raises (e.g. `ValueError` or `NameError`). Per task: "per existing behaviour, may raise". If current behaviour is implicit `NameError`, document or add explicit `ValueError` for clarity.

**Black-box style:** Assert on return value only; do not assert on call counts or internals.

**Fixtures:** Use `datetime(2024, 3, 15)` or `date(2024, 3, 15)` for deterministic assertions. Expected format: `year=2024/month=03/day=15`.

---

## Implementation Order

1. Create `loaders/target-gcs/tests/unit/paths/_partitioned/` directory and `__init__.py` if needed.
2. Create `test_string_functions.py` with the tests above.
3. Run `uv run pytest loaders/target-gcs/tests/unit/paths/_partitioned/test_string_functions.py -v` — tests fail (missing return).
4. Fix `date_as_partition` in `string_functions.py`:
   - Replace `date_value.strftime(DEFAULT_PARTITION_DATE_FORMAT)` with `return date_value.strftime(DEFAULT_PARTITION_DATE_FORMAT)`.
   - Ensure both branches (datetime/date and str) execute the return. Current structure: single `strftime` call after if/elif; one `return` suffices.
5. Re-run tests — all pass.
6. Run full test suite, ruff, mypy from `loaders/target-gcs/`.

---

## Validation Steps

1. **Tests:** `uv run pytest` from `loaders/target-gcs/` — all pass.
2. **Lint:** `uv run ruff check .` — no violations.
3. **Types:** `uv run mypy target_gcs` — no errors.
4. **Regression:** No existing tests fail; PartitionedPath and DatedPath tests (when present) continue to pass or are unaffected.

---

## Documentation Updates

- **None required** for this task. The fix is internal; no public API, config, or README changes.
- **Changelog:** Add entry under `loaders/target-gcs/CHANGELOG.md` (or date-based section): `### Fixed` — "date_as_partition now returns formatted date string instead of None".
