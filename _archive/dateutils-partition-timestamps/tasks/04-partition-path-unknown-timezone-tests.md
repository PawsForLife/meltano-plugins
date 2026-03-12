# Task 04: Partition path unknown-timezone tests (TDD, optional)

## Background

The plan optionally detects `UnknownTimezoneWarning` when dateutil cannot resolve a timezone name in the string, and surfaces it via warning or error. If the implementation in Task 05 includes this handling, a test should exist that a string triggering `UnknownTimezoneWarning` results in visible behaviour (warning or error), not silent fallback. This task is optional: if the team defers or skips UnknownTimezoneWarning handling, this task can be skipped or the test marked as xfail until implemented.

Dependencies: None. Reference: `_features/dateutils-partition-timestamps/plans/master/testing.md` (optional test), `implementation.md` Step 2.

## This Task

- **File:** `loaders/target-gcs/tests/helpers/test_partition_path.py`
  - **If** the product decision is to detect and surface `UnknownTimezoneWarning`:
    - Add a test that uses a string which triggers `UnknownTimezoneWarning` (e.g. a timezone name that dateutil does not resolve). Assert that a warning is surfaced or an error is raised, and that the behaviour is not silent fallback. Use black-box style (exception or documented visibility mechanism).
  - **If** UnknownTimezoneWarning handling is not implemented in Task 05: Skip adding the test, or add a test marked `@pytest.mark.xfail` with a note that it will pass when the feature is implemented.
- **Acceptance criteria:** If the feature is implemented, the test exists and passes; if deferred, the task is explicitly skipped or the test is xfail with a clear reason.

## Testing Needed

- Optional test as described. Docstring: WHAT (unsupported timezone → visible warning/error), WHY (no silent fallback for unsupported timezone). Test must be able to fail when the implementation is wrong.
