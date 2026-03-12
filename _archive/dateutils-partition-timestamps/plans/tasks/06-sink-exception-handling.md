# Task Plan: 06-sink-exception-handling

## Overview

This task ensures the GCS sink handles exceptions from `get_partition_path_from_record` when Task 05 has chosen “raise on unparseable” (or on unsupported timezone). If the helper raises `ParserError` or a wrapper (e.g. `ValueError`), the caller `GCSSink._process_record_partition_by_field` must catch and handle them so the run does not fail with an unhandled exception. If Task 05 chose “warning + fallback” and the helper never raises, this task requires no code change and is documented as N/A.

**Scope:** Behavioural change in `target_gcs.sinks` only. No new public APIs; no signature changes to `_process_record_partition_by_field`.

**Dependencies:** Task 05 must be complete. The implementer must know the product decision from Task 05 (raise vs warning+fallback) and the exact exception type(s) the helper raises.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Modify only if the helper raises. Add try/except around the `get_partition_path_from_record` call in `_process_record_partition_by_field`; catch the exception type(s) raised by the helper; implement the chosen behaviour (re-raise, skip record, or use fallback path). Do not change the method signature. |
| *(none)* | If the helper never raises: no file changes; document in the task outcome that this step was N/A. |

**Specific change in `sinks.py` (when “raise” was chosen):**

- **Location:** `_process_record_partition_by_field`, lines 212–219 (the block that calls `get_partition_path_from_record`).
- **Import:** If catching `ParserError`, add `from dateutil.parser import ParserError` (or import the wrapper type used by the helper, e.g. `ValueError` if the helper wraps in ValueError). Prefer catching the same type(s) the helper raises so the contract in `interfaces.md` is honoured.
- **Logic:** Wrap the call in try/except. In the except block, implement exactly one of:
  - **Re-raise:** Re-raise the same exception (fail the run).
  - **Skip record:** Log (e.g. warning with field name and value if safe), then `return` without writing the record.
  - **Fallback path:** Log (e.g. warning), then set `partition_path = self.fallback.strftime(partition_date_format)` and continue with the rest of the method (handle open, write record).
- **Contract:** Do not change the signature of `_process_record_partition_by_field(self, record: dict, context: dict) -> None`.

---

## Test Strategy

- **No new unit test in `sinks.py`** unless the team explicitly adds one for the catch path (e.g. “when helper raises, sink skips record and does not call write”). The task doc states this is optional.
- **Integration coverage:** Task 07 adds (or extends) tests in `test_partition_key_generation.py` that feed a record with an unparseable partition field and assert either exception propagation or that the record is not written (black-box; no assertions on call counts or log lines).
- **Regression:** All existing tests in `loaders/target-gcs/tests/` must pass, including `test_partition_path.py`, `test_partition_key_generation.py`, and `test_sinks.py`. Run the full target-gcs test suite after implementation.

**TDD note:** This task is downstream of Task 05. If the chosen behaviour is “re-raise,” Task 07’s test will expect an exception; if “skip” or “fallback,” Task 07 will assert on record-not-written or on key containing fallback path. The implementer should run Task 07 tests (when present) to confirm the sink behaviour matches the product decision.

---

## Implementation Order

1. **Confirm product decision and exception type.** From Task 05 outcome (or `partition_path.py`), determine: (a) Does `get_partition_path_from_record` raise on unparseable or unsupported timezone? (b) Which exception type(s) are raised (`ParserError`, `ValueError`, or other)?
2. **If the helper never raises:** Document in the task outcome that no code change was required; run the test suite to confirm no regressions. Stop.
3. **If the helper raises:** In `sinks.py`, add the appropriate import for the exception type(s).
4. **Wrap the call:** In `_process_record_partition_by_field`, wrap the `get_partition_path_from_record(...)` call in try/except, catching the determined exception type(s).
5. **Implement chosen behaviour:** In the except block, implement re-raise, skip record (return), or log + use `self.fallback.strftime(partition_date_format)` and continue.
6. **Run tests:** Execute the full target-gcs test suite; fix any regressions. If Task 07 tests exist, run them and ensure they pass for the chosen behaviour.

---

## Validation Steps

1. **Product decision applied:** When the helper is changed to raise on an unparseable partition field value, the sink behaves as specified (run fails, record skipped, or fallback path used). No unhandled exception from the sink for the expected exception types.
2. **Regression:** `uv run pytest` in `loaders/target-gcs/` passes (no failures except explicitly marked xfail).
3. **Task 07:** Any integration test in Task 07 that asserts on unparseable partition field (exception or record-not-written) passes.
4. **Lint/type:** `uv run ruff check .` and `uv run mypy target_gcs` pass in `loaders/target-gcs/`.

---

## Documentation Updates

- **No doc file changes in this task.** AI context and user-facing docs for partition path behaviour are updated in Task 08.
- **In-code:** If a non-obvious choice was made (e.g. “skip record” vs “fallback path”), add a short comment in `_process_record_partition_by_field` above the except block explaining the chosen behaviour (e.g. “On partition parse error: skip record so the run continues.”).
