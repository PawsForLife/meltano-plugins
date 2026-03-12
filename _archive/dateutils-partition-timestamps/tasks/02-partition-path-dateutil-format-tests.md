# Task 02: Partition path dateutil-format tests (TDD)

## Background

The plan replaces `datetime.fromisoformat` and `strptime("%Y-%m-%d")` in `get_partition_path_from_record` with dateutil-based parsing. Per TDD, tests for the new behaviour are written first and must fail until the implementation is added in a later task. This task adds tests for dateutil-parsable string formats that the current implementation does not support (e.g. `"2024/03/11"`, `"11 Mar 2024 12:00:00"`). Existing tests for valid ISO date, valid ISO datetime, missing field, non-string, and custom format must be retained and will continue to pass once dateutil is wired in.

Dependencies: None. Interface: `get_partition_path_from_record` signature unchanged; tests assert on return value only.

Reference: `_features/dateutils-partition-timestamps/plans/master/testing.md`, `implementation.md` Step 2.

## This Task

- **File:** `loaders/target-gcs/tests/helpers/test_partition_path.py`
  - Add 2–3 test cases that call `get_partition_path_from_record` with a record whose partition date field is a **string** that dateutil parses but the current code does not (e.g. `"2024/03/11"`, `"11 Mar 2024 12:00:00"`, or `"March 11, 2024"`).
  - Use the same pattern as existing tests: fixed `FALLBACK_DATE`, `DEFAULT_HIVE_FORMAT`, and a single partition field (e.g. `created_at`).
  - For each case, assert that the returned path equals the expected Hive-style path (e.g. `"year=2024/month=03/day=11"`) or the path implied by the custom format if used.
  - Do not remove or alter existing tests (`test_partition_path_valid_iso_date_in_field`, `test_partition_path_valid_iso_datetime_in_field`, `test_partition_path_missing_field_uses_fallback`, `test_partition_path_custom_format`).
- **Acceptance criteria:** New tests fail with the current implementation (no dateutil yet); they will pass after Task 05. Each test has a clear docstring stating WHAT is being tested and WHY (per project rules).

## Testing Needed

- New tests as described above. Follow black-box style: assert only on the returned partition path string. No assertions on internal calls or log output. Tests must be able to fail (assert a specific return value; wrong implementation will cause failure).
