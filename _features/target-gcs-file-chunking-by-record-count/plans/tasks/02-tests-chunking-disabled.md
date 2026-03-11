# Task Plan: 02-tests-chunking-disabled

**Feature:** target-gcs-file-chunking-by-record-count  
**Task:** Add tests that lock in backward compatibility when chunking is disabled (`max_records_per_file` unset or 0).

---

## Overview

When `max_records_per_file` is unset or 0, behaviour must match the current implementation: one key and one handle per stream, no rotation, and no `chunk_index` in the key. This task adds two tests in `test_sinks.py` that assert that observable behaviour. The tests will fail until task 03 (sink state and time injection) and task 06 (rotation and process_record) implement the logic that initializes chunking state and skips rotation when the setting is 0 or absent. No production code is changed in this task.

**Depends on:** Task 01 (add config schema) so that config with or without `max_records_per_file` is valid.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/test_sinks.py` | Add two test functions; use existing `build_sink(config=...)`; patch `gcs_target.sinks.Client` and `gcs_target.sinks.smart_open.open` as needed. No new files. |

---

## Test Strategy

**TDD:** These tests are written first (in this task). They define the acceptance criteria for “chunking disabled.” Implementation that makes them pass is done in tasks 03 and 06.

1. **Test 1 — One key and one handle when chunking disabled**
   - **What:** With no `max_records_per_file` (or `max_records_per_file: 0`), multiple records result in a single key and a single handle (no rotation).
   - **Why:** Backward compatibility: existing behaviour must be unchanged when the option is off.
   - **How:** Build sink with config omitting `max_records_per_file` (or with `max_records_per_file: 0`). Patch `Client` and `smart_open.open` (e.g. return a mock handle). Call `process_record` multiple times (e.g. 5) with dummy records. Assert `sink.key_name` is unchanged after the writes (e.g. capture at first and last write, or after each). Assert exactly one handle is used: patch `smart_open.open` and assert it was called once after all `process_record` calls. Docstring: WHAT (one key, one handle when chunking off) and WHY (backward compatibility).

2. **Test 2 — Key has no chunk_index when convention omits it**
   - **What:** When chunking is disabled, the key does not contain a literal `{chunk_index}` and matches the existing pattern (stream, date, timestamp only).
   - **Why:** Ensures key format is unchanged when chunking is disabled.
   - **How:** Build sink without chunking. Use a `key_naming_convention` that does not include `{chunk_index}` (e.g. default or `"{stream}_{timestamp}.jsonl"` or a convention with `{stream}`, `{date}`, `{timestamp}` only). Trigger key computation (e.g. access `key_name` or call `process_record` once with patched Client/smart_open). Assert `sink.key_name` does not contain the literal substring `"{chunk_index}"`. Assert the key matches the expected pattern (e.g. stream name, date, timestamp; no chunk index token). Docstring: WHAT (key format unchanged when chunking off) and WHY (backward compatibility).

**Black-box:** Assert on observable behaviour only: stable `key_name`, number of handle opens (one open = one file), and key string content. Do not assert on log lines or other internal call counts unrelated to “one file” or “key format.”

**Determinism:** For test 2, key content depends on `time.time()` and `datetime.today()`. Either patch `gcs_target.sinks.time` (and optionally date) for fixed values, or assert only that the key does not contain `"{chunk_index}"` and matches a regex for the known pattern (stream, date, timestamp), so tests are stable.

---

## Implementation Order

1. **Add Test 1** in `loaders/target-gcs/tests/test_sinks.py`:
   - Use `build_sink()` with no `max_records_per_file`, or `build_sink({"max_records_per_file": 0})`.
   - In the test, patch `gcs_target.sinks.Client` and `gcs_target.sinks.smart_open.open` (e.g. `open` returns a mock that supports `.write(...)`).
   - Call `sink.process_record(record, context)` multiple times (e.g. 5) with simple dict records and a fixed context.
   - Assert `sink.key_name` is the same before and after (or after each write).
   - Assert `smart_open.open` was called exactly once (observable: one file opened for the stream).
   - Add a docstring: WHAT (one key and one handle when chunking disabled) and WHY (backward compatibility).

2. **Add Test 2** in the same file:
   - Build sink without chunking; optionally set `key_naming_convention` to a template that does not use `{chunk_index}` (e.g. `"{stream}/export_date={date}/{timestamp}.jsonl"`).
   - Trigger key computation (access `key_name` or one `process_record` with mocks).
   - Assert `"{chunk_index}" not in sink.key_name`.
   - Assert key matches the expected pattern (e.g. contains stream name, date, timestamp; regex or substring checks as appropriate). Use patched time/date if needed for deterministic assertions.
   - Add a docstring: WHAT (key has no chunk_index when convention omits it) and WHY (backward compatibility).

3. **Run tests** from `loaders/target-gcs/`: `uv run pytest tests/test_sinks.py -v`. New tests are expected to fail until tasks 03 and 06 are implemented (missing state vars and rotation guard). Do not mark them as xfail; they are the specification for later tasks.

4. **Lint and type-check:** `uv run ruff check .`, `uv run ruff format --check`, `uv run mypy gcs_target`. Fix any issues in the new test code only.

---

## Validation Steps

- From `loaders/target-gcs/`: `uv run pytest tests/test_sinks.py` runs without errors; new tests may fail until tasks 03 and 06 are done (acceptable for this task).
- New tests are not marked as expected failure; they document the desired behaviour.
- From `loaders/target-gcs/`: `uv run ruff check .` and `uv run ruff format --check` pass.
- From `loaders/target-gcs/`: `uv run mypy gcs_target` passes (tests may not be in mypy scope; if they are, no new type errors).
- Acceptance: Two tests added; clear docstrings (WHAT/WHY); assertions on key stability, single handle open, and key content only (no chunk_index literal when chunking off).

---

## Documentation Updates

None. Test docstrings are the documentation for the behaviour. README, sample config, and AI context are updated in task 08.
