# Task Plan: 07 — Handle Flush on Close

**Feature:** target-gcs-file-chunking-by-record-count  
**Task file:** `tasks/07-handle-flush-on-close.md`  
**Depends on:** 06-rotation-and-process-record (rotation block must exist in `process_record`)

---

## 1. Overview

This task ensures that when the GCS write handle is closed during rotation, any buffered data is flushed first so no records are lost. The sink uses `smart_open.open(..., "wb", ...)`; the returned handle may buffer writes. The change is confined to the **rotation block** inside `process_record`: before calling `close()` on the handle, call `flush()` if the handle supports it. Handles that do not support `flush` are left unchanged (no-op); the code must not raise. This keeps behaviour correct for any file-like object returned by `smart_open` and avoids data loss when the implementation uses a buffered writer.

**Scope:**

- Add a guarded `flush()` call immediately before `close()` in the rotation block.
- Use a runtime check (e.g. `hasattr(self._gcs_write_handle, "flush")`) so code works with any file-like returned by `smart_open`; do not assume a specific type.
- No change to rotation logic (close, clear key, increment chunk index, reset counter); no new config or public API.

---

## 2. Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/gcs_target/sinks.py` | In the rotation block (inside `process_record`), before closing `_gcs_write_handle`: if the handle has a `flush` method, call `flush()`; then call `close()` as today. No new methods or classes. |

**Specific change in `sinks.py`:**

- **Location:** The rotation block that runs when `max_records_per_file > 0` and `_records_written_in_current_file >= max_records_per_file`, where `_gcs_write_handle` is not None.
- **Insert:** Immediately before `close()` (or equivalent that sets the handle to None), add:
  - If the handle supports flush: `if hasattr(self._gcs_write_handle, "flush"): self._gcs_write_handle.flush()` (or equivalent guard and call).
- **Behaviour:** If the handle has no `flush` attribute, do nothing and proceed to close. Do not raise. After the block, state is as today (handle closed, key cleared, chunk index incremented, counter reset).

---

## 3. Test Strategy

**No new test is required** for flush itself. Per master testing plan and development_practices (black-box testing): tests assert observable behaviour (record integrity, keys, number of opens/closes), not internal implementation details such as "flush was called." Do **not** add a test that asserts `flush` was invoked.

**Regression and coverage:**

- All existing tests in `loaders/target-gcs/tests/test_sinks.py` (including chunking-disabled, rotation at threshold, key format with chunk_index, record integrity) must still pass.
- If the test suite already asserts that all written records appear in the correct chunks and that rotation closes the handle and opens a new one, that suffices to validate that flush-before-close does not break behaviour.
- Run the full target-gcs test suite from `loaders/target-gcs/` after the change; fix any regressions.

---

## 4. Implementation Order

1. **Locate the rotation block**  
   In `loaders/target-gcs/gcs_target/sinks.py`, inside `process_record`, find the block that runs when rotation is triggered (e.g. when `max_records_per_file > 0` and `_records_written_in_current_file >= max_records_per_file`) and where `_gcs_write_handle` is not None.

2. **Add flush before close**  
   Immediately before the line that closes the handle (and sets `_gcs_write_handle = None`), insert:
   - A guard that checks whether the handle has a `flush` method (e.g. `hasattr(self._gcs_write_handle, "flush")`).
   - If true, call `self._gcs_write_handle.flush()`.
   - Then perform the existing close and handle cleanup.

3. **Run tests**  
   From `loaders/target-gcs/`, run `uv run pytest` (with venv active). Resolve any failing tests; ensure no regression.

4. **Run linters**  
   Run `uv run ruff check .` and `uv run ruff format --check .` (and `uv run mypy gcs_target` if applicable). Fix any issues.

---

## 5. Validation Steps

- **Rotation still works:** Tests that assert rotation at threshold (e.g. two distinct keys, two `smart_open.open` calls after writing past the limit) still pass.
- **Record integrity:** Tests that assert all records are written exactly once and chunk sizes are correct still pass.
- **No regression:** All tests in `test_sinks.py` and any other target-gcs tests pass (no new failures except explicitly marked xfail).
- **Handle without flush:** Code path is guarded; a handle without `flush` does not raise; close still runs. (Optional: if a test uses a mock handle without `flush`, it should still pass; no change to mock required if existing mocks already support close.)

---

## 6. Documentation Updates

- **No new user-facing documentation** is required for this change (internal behaviour only).
- **Master plan:** The master implementation plan already describes "flush (if the handle supports it)" in the rotation step; no change to `_features/.../plans/master/implementation.md` is required unless adding a one-line note that the guard is `hasattr(..., "flush")` for clarity. Prefer leaving implementation.md as-is and keeping the detail in this task plan.
- **README / sample config:** No updates; no new config or API.
