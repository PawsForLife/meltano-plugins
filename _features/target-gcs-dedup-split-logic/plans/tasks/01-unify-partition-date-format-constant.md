# Task Plan: 01-unify-partition-date-format-constant

## Overview

This task establishes a single source of truth for `DEFAULT_PARTITION_DATE_FORMAT` by removing the duplicate definition from `sinks.py` and having the sink import the constant from `target_gcs.helpers.partition_path`. It is the first step in the target-gcs-dedup-split-logic feature and has no dependencies on other tasks. Behaviour is unchanged; existing tests act as the regression gate.

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Remove the local constant `DEFAULT_PARTITION_DATE_FORMAT` (line 23). Add import of `DEFAULT_PARTITION_DATE_FORMAT` from `.helpers.partition_path`. All existing references (docstring ~line 238, call site ~line 249) already use the name and will resolve to the import. |
| `loaders/target-gcs/target_gcs/helpers/partition_path.py` | No change. Remains the sole owner of the constant. |
| `loaders/target-gcs/target_gcs/helpers/__init__.py` | No change. Sinks import from `partition_path` directly; no other consumers require a single entry point for this constant. |

## Test Strategy

- **No new tests.** This task is a refactor only; behaviour is preserved.
- **Regression gate:** Run the full target-gcs test suite from `loaders/target-gcs/`: `uv run pytest`. All tests must pass.

## Implementation Order

1. **Add import in `sinks.py`**
   Add `from .helpers.partition_path import DEFAULT_PARTITION_DATE_FORMAT` (sinks import from `partition_path` directly per master plan). Optionally move `get_partition_path_from_schema_and_record` to this same import so all partition_path symbols come from one place; otherwise leave the existing `from .helpers import (..., get_partition_path_from_schema_and_record, ...)` as-is.
2. **Remove local constant**
   Delete the line `DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"` and the comment above it (the one referring to "Default Hive-style partition path format") from `sinks.py`.
3. **Verify usages**
   Confirm `DEFAULT_PARTITION_DATE_FORMAT` is used only in the docstring of `_process_record_hive_partitioned` and in the `get_partition_path_from_schema_and_record(..., partition_date_format=DEFAULT_PARTITION_DATE_FORMAT)` call; both resolve to the imported constant.

## Validation Steps

1. From `loaders/target-gcs/`, run `uv run pytest`. All tests must pass.
2. From `loaders/target-gcs/`, run `uv run ruff check .` and `uv run ruff format --check` and `uv run mypy target_gcs`. Resolve any new issues.
3. Optionally, from repo root, run `./scripts/run_plugin_checks.sh` to confirm no regressions across the repo.

## Documentation Updates

None. No user-facing or AI-context docs require changes for this task. The constant’s meaning and location are already described in the master plan and in `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` (constant lives in `partition_path`).
