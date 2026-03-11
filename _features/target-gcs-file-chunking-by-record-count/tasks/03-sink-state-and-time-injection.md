# Background

Rotation logic needs per-stream state: how many records have been written to the current file and which chunk index we are on. Tests that assert key content need deterministic timestamps; the plan specifies injectable or patchable time for key generation.

**Depends on:** 01-add-config-schema.

# This Task

- **File:** `loaders/target-gcs/gcs_target/sinks.py`
- In `GCSSink.__init__`: after existing `_gcs_write_handle` and `_key_name` initialization, add:
  - `self._records_written_in_current_file: int = 0` — records written to the current open file; reset on rotation.
  - `self._chunk_index: int = 0` — 0-based chunk index; incremented on rotation.
- **Time for key generation:** Prefer optional dependency injection (e.g. `time_fn` from target or sink constructor) so tests can pass a fixed or controllable time without patching. If the project prefers minimal API change, use `time.time()` in code and document that tests patch `gcs_target.sinks.time` for deterministic keys. Do not add a new constructor parameter if the team standard is to patch `time` in tests; in that case add a one-line comment in the key-computation block that time is patchable for tests.
- **Acceptance criteria:** Existing tests in `test_sinks.py` still pass. No rotation or key logic changes yet; this task is state and (if applicable) time injection only.

# Testing Needed

- Run existing `test_sinks.py`; all must pass.
- If time_fn is added: add a test that builds a sink with a custom time_fn returning a fixed value and asserts key_name contains that timestamp (or add that assertion in a later task when key_name uses it). If time is left as `time.time()` and patch is documented: no new test here; task 04/05 tests will patch time.
