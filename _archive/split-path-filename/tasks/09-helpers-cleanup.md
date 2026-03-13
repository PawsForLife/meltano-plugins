# 09 — Helpers Cleanup

## Background

After PartitionedPath uses `hive_path(record)` for key building, `get_partition_path_from_schema_and_record` in `helpers/partition_path.py` may be unused. Verify and remove or deprecate. Ensure `DEFAULT_PARTITION_DATE_FORMAT` import path is consistent (constants vs helpers).

## This Task

**Files to modify:**
- `loaders/target-gcs/target_gcs/helpers/partition_path.py`
- Any modules that import from `helpers/partition_path`

**Implementation steps:**
1. Grep for `get_partition_path_from_schema_and_record` usages. If only used by removed PartitionedPath logic, remove the function.
2. If retained for other uses (e.g. validation, tests), keep and document. Otherwise remove.
3. Verify `DEFAULT_PARTITION_DATE_FORMAT` is defined in `constants.py` and imported from there by `_partitioned` and DatedPath. Remove duplicate definition from helpers if present.
4. Update `helpers/__init__.py` exports if function is removed.
5. Update `tests/unit/helpers/test_partition_path.py`: remove or adjust tests for removed function; keep tests for any retained helpers.

**Acceptance criteria:**
- No dead code; `get_partition_path_from_schema_and_record` removed if unused.
- `DEFAULT_PARTITION_DATE_FORMAT` has single source in `constants.py`.
- All tests pass.
