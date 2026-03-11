# Task 04: Add is_sorted to DynamicStream (streams.py)

## Background

`DynamicStream` must accept an `is_sorted` argument and set `self.is_sorted` on the instance so the Singer SDK can use it for resumable incremental state. This task is required before task 05 (wire in discover_streams) so that the constructor accepts the new keyword. No dependency on task 03 for this file; task 05 depends on both 03 and 04.

## This Task

- **File:** `taps/restful-api-tap/restful_api_tap/streams.py`
- **Changes:**
  1. **__init__ parameter list:** Add `is_sorted: Optional[bool] = False` (e.g. after `flatten_records`, before `authenticator`).
  2. **Docstring Args:** Add an entry for `is_sorted`: when True, stream is declared sorted by replication_key for resumable state; default False.
  3. **Instance attribute:** After existing attribute assignments (e.g. after `self.flatten_records = flatten_records`), add `self.is_sorted = is_sorted`.
- **Acceptance criteria:** `DynamicStream(..., is_sorted=True)` results in `stream.is_sorted is True`; default is False; SDK can read `stream.is_sorted`; no change to pagination, URL params, or record emission.

## Testing Needed

- Task 01 tests will still fail until task 05 passes `is_sorted` from config. After task 05, task 01 tests assert that discovered streams have the correct `is_sorted` value. No new test file in this task; unit test that instantiates `DynamicStream` with `is_sorted=True`/`False` and asserts `stream.is_sorted` is optional and can be covered in task 01's black-box discovery tests.
