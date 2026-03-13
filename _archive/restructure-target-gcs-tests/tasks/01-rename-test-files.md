# Task 01: Rename test files to match source modules

## Background

The target-gcs test layout must follow the rule: one test file per source module, with names that map 1:1 to the module under test (e.g. `test_paths_simple.py` for `paths/simple.py`). The plan specifies renaming four test files so their names align with the source package structure; no test logic or imports change in this step. This task has no dependencies on other tasks.

## This Task

- **Rename** the following files in `loaders/target-gcs/tests/`:
  - `test_core.py` → `test_target.py` (tests `target_gcs.target` / GCSTarget)
  - `test_simple_path.py` → `test_paths_simple.py` (tests `target_gcs.paths.simple`)
  - `test_dated_path.py` → `test_paths_dated.py` (tests `target_gcs.paths.dated`)
  - `test_partitioned_path.py` → `test_paths_partitioned.py` (tests `target_gcs.paths.partitioned`)
- **Do not** change test body logic, assertions, or imports. Optionally update docstrings or comments that refer to "core" to "target" in the renamed `test_target.py` for clarity.
- **Leave** `test_sinks.py`, `test_paths_base.py`, and all files under `tests/helpers/` unchanged (names already correct or out of scope).

**Acceptance criteria:** All four renames are done; pytest discovers tests from the new file names; no edits to test logic.

## Testing Needed

- After renames: run the full test suite from `loaders/target-gcs` (e.g. `uv run pytest`) and confirm all tests still pass.
- Run `uv run pytest --collect-only` and confirm the renamed modules appear and no references to the old file names remain in the collected tests.
