# 02 — Fix date_as_partition Bug

## Background

Pre-existing bug: `date_as_partition` in `_partitioned/string_functions.py` calls `date_value.strftime(...)` but does not return the result. DatedPath and PartitionedPath depend on correct date formatting. Depends on task 01 (constants) only for `DEFAULT_PARTITION_DATE_FORMAT` import; no change to that.

## This Task

**Files to modify:**
- `loaders/target-gcs/target_gcs/paths/_partitioned/string_functions.py`

**Files to create (if missing):**
- `loaders/target-gcs/tests/unit/paths/_partitioned/test_string_functions.py`

**Implementation steps:**
1. **TDD first:** Add `test_date_as_partition_returns_formatted_string` — given a date/datetime or parseable date string, assert `date_as_partition(field_name, field_value)` returns a non-empty string matching `DEFAULT_PARTITION_DATE_FORMAT` (e.g. `year=YYYY/month=MM/day=DD`).
2. Run test; it fails (missing return).
3. Fix `date_as_partition`: add `return date_value.strftime(DEFAULT_PARTITION_DATE_FORMAT)` (replace the bare call).
4. Ensure all code paths return (handle edge cases if `field_value` is neither datetime/date nor str — per existing behaviour, may raise; document or handle as appropriate).

**Acceptance criteria:**
- `date_as_partition` returns the formatted string.
- Test passes; black-box style (assert on return value, not internals).

## Testing Needed

- `test_date_as_partition_returns_formatted_string`: With `datetime` or `date` or parseable string, assert return is non-empty and matches Hive date format.
- `test_date_as_partition_uses_injected_format` (optional): If format is injectable; otherwise rely on constant.
