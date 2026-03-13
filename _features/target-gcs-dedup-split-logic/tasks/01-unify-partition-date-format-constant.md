# Task 01: Unify partition date format constant

## Background

The plan identifies `DEFAULT_PARTITION_DATE_FORMAT` as duplicated in `sinks.py` and `helpers/partition_path.py`. A single source of truth is required in `partition_path.py`; sinks must import it instead of defining a local constant. This task has no dependencies on other tasks.

## This Task

- In `loaders/target-gcs/target_gcs/sinks.py`: remove the local definition of `DEFAULT_PARTITION_DATE_FORMAT` and add an import from `target_gcs.helpers.partition_path` (or from `.helpers` if the constant is re-exported there).
- In `loaders/target-gcs/target_gcs/helpers/partition_path.py`: no code change; it remains the sole owner of the constant.
- In `loaders/target-gcs/target_gcs/helpers/__init__.py`: add `DEFAULT_PARTITION_DATE_FORMAT` to exports only if other consumers need a single entry point; sinks may import from `partition_path` directly.
- Ensure all existing usages of `DEFAULT_PARTITION_DATE_FORMAT` in `sinks.py` (e.g. passed to `get_partition_path_from_schema_and_record` or equivalent) now use the imported constant.

**Acceptance criteria:** No local constant in `sinks.py`; all references resolve to the import; full target-gcs test suite passes.

## Testing Needed

- No new tests. Run the full target-gcs test suite (`uv run pytest` from `loaders/target-gcs/`) to confirm no behaviour change (regression gate).
