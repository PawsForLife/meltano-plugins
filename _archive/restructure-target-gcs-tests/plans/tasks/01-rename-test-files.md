# Task Plan: 01-rename-test-files

## Overview

This task renames four test files in `loaders/target-gcs/tests/` so their names map 1:1 to the source modules they exercise. It is the first step in the restructure feature: no test logic, assertions, or imports change. Completing it establishes the naming convention (`test_<module_path>.py`) before later tasks (merge, dedupe, CI updates).

## Files to Create/Modify

**Renames only** (no content change; optional: docstring/comment "core" → "target" in the renamed target file):

| Current path | New path |
|--------------|----------|
| `loaders/target-gcs/tests/test_core.py` | `loaders/target-gcs/tests/test_target.py` |
| `loaders/target-gcs/tests/test_simple_path.py` | `loaders/target-gcs/tests/test_paths_simple.py` |
| `loaders/target-gcs/tests/test_dated_path.py` | `loaders/target-gcs/tests/test_paths_dated.py` |
| `loaders/target-gcs/tests/test_partitioned_path.py` | `loaders/target-gcs/tests/test_paths_partitioned.py` |

**Unchanged:** `test_sinks.py`, `test_paths_base.py`, all files under `tests/helpers/`.

## Test Strategy

- After all renames: run the full test suite from `loaders/target-gcs` (e.g. `uv run pytest`) and confirm all tests pass.
- Run `uv run pytest --collect-only` and confirm the renamed modules appear and no references to the old file names remain in the collected tests.

## Implementation Order

1. Rename `test_core.py` → `test_target.py`.
2. Rename `test_simple_path.py` → `test_paths_simple.py`.
3. Rename `test_dated_path.py` → `test_paths_dated.py`.
4. Rename `test_partitioned_path.py` → `test_paths_partitioned.py`.
5. Optionally update docstrings or comments in `test_target.py` that refer to "core" to "target" for clarity.
6. Run validation steps below.

## Validation Steps

1. From `loaders/target-gcs`: `uv run pytest` — all tests must pass.
2. From `loaders/target-gcs`: `uv run pytest --collect-only` — verify collected items use the new file names (`test_target`, `test_paths_simple`, `test_paths_dated`, `test_paths_partitioned`) and that no old names appear.

## Documentation Updates

None for this task (renames only). AI context and CI path updates are covered in later tasks (e.g. 04-update-ci-and-script-paths, documentation.md).
