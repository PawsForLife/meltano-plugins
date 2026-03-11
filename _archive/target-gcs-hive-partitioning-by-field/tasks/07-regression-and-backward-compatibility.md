# Background

The feature must not change behaviour when `partition_date_field` is unset. All existing tests must remain green, and key_name / single-handle semantics must match current behaviour. This task ensures the regression gate is satisfied and adds an explicit test that unset config leaves behaviour unchanged.

**Dependencies:** Tasks 01–06 complete. This task validates the full implementation against backward-compatibility requirements.

**Plan reference:** `plans/master/testing.md` (Unit tests: backward compatibility, Existing key_name tests).

---

# This Task

- **File:** `loaders/target-gcs/tests/test_sinks.py`
- Run the full test suite for the target-gcs plugin; fix any regressions (failing tests not marked xfail) so all pass.
- Add or confirm an explicit test: when `partition_date_field` is not set, key_name and single-key-per-stream (or per-chunk) behaviour is unchanged. This can be covered by existing tests (e.g. `test_key_name_includes_default_date_format_if_date_token_used`) and/or a dedicated test that builds a sink without partition_date_field and asserts key uses run date and does not depend on record content.
- **Acceptance criteria:** All existing tests in test_sinks.py (and test_core.py if present) pass. No new failures. Explicit backward-compatibility test exists and passes.

---

# Testing Needed

- **Existing key_name tests still pass:** All current tests that do not set `partition_date_field` continue to pass (run-date key, prefix, timestamp, chunk_index, etc.). **WHAT:** No regression when feature unused. **WHY:** Regression gate.
- **key_name when partition_date_field unset:** Same as today: single key per stream (or per chunk). **WHAT:** key_name property behaviour unchanged. **WHY:** Existing callers and tests.

Run `uv run pytest loaders/target-gcs/tests/` (or project test command) and ensure green. Resolve any regressions before marking task complete.
