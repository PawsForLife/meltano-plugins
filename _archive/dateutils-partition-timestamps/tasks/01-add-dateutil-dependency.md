# Task 01: Add dateutil dependency

## Background

Partition path resolution in `target_gcs.helpers.partition_path` will use `dateutil.parser.parse` for string timestamps. The plan requires adding `python-dateutil` to target-gcs so the helper can import and use it. This task has no dependencies; it is the prerequisite for all implementation work. No interface or model changes.

Reference: `_features/dateutils-partition-timestamps/plans/master/dependencies.md`, `implementation.md` Step 1.

## This Task

- **File:** `loaders/target-gcs/pyproject.toml`
  - Add to `[project].dependencies`: `python-dateutil>=2.8.1` (or `>=2.8.1,<3` per project version policy). Version 2.8.1+ provides `ParserError` and `UnknownTimezoneWarning` reliably.
- Run the project install script (e.g. `./install.sh` in `loaders/target-gcs` or project-defined equivalent) so the lockfile and virtual environment include the new dependency.
- **Acceptance criteria:** `from dateutil import parser` and `from dateutil.parser import ParserError` succeed in the target-gcs environment; test suite can run with the new dependency present.

## Testing Needed

- No new test file or test case is required for this task. Verification is that the environment installs and imports succeed. After implementation of later tasks, existing and new tests will run using dateutil.
