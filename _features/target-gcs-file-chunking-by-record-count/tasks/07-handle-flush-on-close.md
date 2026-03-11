# Background

When the handle is closed during rotation, any buffered data must be flushed so no records are lost. The sink uses `smart_open.open(..., "wb", ...)`; the returned handle may buffer writes. The plan requires an explicit flush before close in the rotation block when the handle supports it.

**Depends on:** 06-rotation-and-process-record (rotation block exists).

# This Task

- **File:** `loaders/target-gcs/gcs_target/sinks.py`
- In the rotation block (inside `process_record`, before closing the handle): if the handle has a `flush` method (e.g. `if hasattr(self._gcs_write_handle, "flush")` or the handle type is known to support it), call `flush()` before `close()`.
- If the handle does not support `flush`, no-op; do not raise. Prefer a guard so code works with any file-like returned by `smart_open`.
- **Acceptance criteria:** Rotation still closes the handle and clears state; no regression in tests. If the runtime handle supports flush, it is called before close.

# Testing Needed

- All existing and new tests in `test_sinks.py` must still pass. No new test is strictly required for flush (black-box: we assert record integrity and open/close behaviour; flush is an implementation detail). If the test suite already asserts that all written records appear in the correct chunk, that suffices. Do not add tests that assert "flush was called" (internal behaviour).
