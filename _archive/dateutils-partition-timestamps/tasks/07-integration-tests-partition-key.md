# Task 07: Integration tests (partition key)

## Background

After the partition path helper uses dateutil (Task 05) and optional sink exception handling (Task 06), integration tests at the sink level ensure that a record with a dateutil-parsable non-ISO timestamp produces a key containing the expected partition path, and that unparseable partition field behaviour (exception or record not written) is observable. Tests use the existing `build_sink` helper and GCS mocks; black-box assertions on the key passed to `smart_open.open` or on raised exception.

Dependencies: Task 05; Task 06 if the sink catches and handles exceptions. Reference: `_features/dateutils-partition-timestamps/plans/master/implementation.md` Step 5, `testing.md`.

## This Task

- **File:** `loaders/target-gcs/tests/test_partition_key_generation.py`
  - **Add or extend** a test that builds a sink with `partition_date_field` and feeds a record whose partition field is a **dateutil-parsable non-ISO string** (e.g. `"2024/03/11"` or `"11 Mar 2024"`). Call the code path that resolves the partition path and builds the key (e.g. `process_record` with GCS mocks, or the helper that builds the key). Assert that the key passed to `smart_open.open` (or the resulting key name) contains the expected partition path segment (e.g. `year=2024/month=03/day=11`). Use existing `build_sink`, `_key_from_open_call`, and patch for `smart_open.open` / Client as in existing tests.
  - **If** the helper raises on unparseable: Add a test that a record with an unparseable partition field (e.g. `"not-a-date"`) causes an exception to propagate from the sink, or that the record is not written (assert on observable outcome: exception or that the write handle was not called for that record). Black-box only; no assertions on internal call counts.
- **Acceptance criteria:** New tests pass with the implementation from Task 05 (and 06). Docstrings state WHAT (sink key contains partition from dateutil format; unparseable → exception or record not written) and WHY (integration guarantee). All existing tests in this file continue to pass.

## Testing Needed

- New integration tests as above. Each test must be able to fail (wrong partition path or missing exception would fail the test). Use deterministic `date_fn` and config so keys are predictable.
