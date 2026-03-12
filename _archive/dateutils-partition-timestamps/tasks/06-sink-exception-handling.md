# Task 06: Sink exception handling

## Background

If Task 05 implements "raise on unparseable" (or on unsupported timezone), `get_partition_path_from_record` may raise `ParserError` or a wrapper (e.g. `ValueError`). The caller `GCSSink._process_record_partition_by_field` in `target_gcs.sinks` must then handle that exception: either re-raise (fail the run), or catch and skip the record, or log and use a fallback path, per product decision. If the product decision is "warning + fallback" and the helper never raises, no change is required in the sink.

Dependencies: Task 05 (implementation must exist and may raise). Reference: `_features/dateutils-partition-timestamps/plans/master/implementation.md` Step 4, `interfaces.md`.

## This Task

- **File:** `loaders/target-gcs/target_gcs/sinks.py`
  - **If** `get_partition_path_from_record` is allowed to raise on unparseable or unsupported timezone:
    - In `_process_record_partition_by_field`, wrap the call to `get_partition_path_from_record` in try/except.
    - Catch the exception type(s) that the helper raises (e.g. `ParserError`, or a wrapper).
    - Implement the chosen behaviour: re-raise (fail run), or log and skip the record (do not write this record), or log and use fallback path for this record. Do not change the method signature of `_process_record_partition_by_field`.
  - **If** the helper never raises (warning + fallback only): No code change; document in the task outcome that this step was N/A.
- **Acceptance criteria:** When the helper raises, the sink behaves as specified (run fails, record skipped, or fallback path used); no unhandled exception from the sink for the expected exception types. Existing tests and Task 07 integration tests pass.

## Testing Needed

- If sink behaviour changes: integration tests in Task 07 will assert on exception propagation or record-not-written when partition field is unparseable. No new unit test in sinks.py is required unless the team adds one for the catch path. Regression: existing sink and partition key tests must still pass.
