# Task Plan: 04 — Tests for Rotation and Key Format

**Feature:** target-gcs-file-chunking-by-record-count  
**Task file:** `tasks/04-tests-rotation-and-key-format.md`  
**Depends on:** 01-add-config-schema, 02-tests-chunking-disabled, 03-sink-state-and-time-injection

---

## 1. Overview

This task adds three black-box tests in `test_sinks.py` that define the expected behaviour for record-count-based file rotation and key format when chunking is enabled. The tests will **fail** until tasks 05 (key computation with chunk_index) and 06 (rotation and process_record) are implemented; they act as the TDD specification for that behaviour.

**Scope:**

- **Rotation at threshold:** After N records, the sink closes the current handle and opens a new file; the record that would exceed the limit is written to the new file.
- **Key format with chunk_index:** When chunking is on, the key includes `{chunk_index}` so multiple chunks in the same second have distinct keys.
- **Record integrity:** Every record is written exactly once; no duplicates or drops; chunk sizes respect the limit (last chunk may have fewer).

Tests assert on **observable outcomes** (keys passed to `smart_open.open`, write call arguments, number of opens) per master testing plan and development_practices. They do not assert on call counts for their own sake or on log lines.

---

## 2. Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/test_sinks.py` | Add three test functions and any shared helpers (e.g. a helper that patches `Client`, `smart_open.open`, and `gcs_target.sinks.time` and returns the sink plus mocks for assertions). No new files. |

**Specific changes in `test_sinks.py`:**

- **Imports:** Ensure `unittest.mock.patch` (already present) is used; add any needed mock helpers (e.g. `MagicMock` if collecting write args).
- **Test 1 — `test_chunking_rotation_at_threshold`:** Build sink with `max_records_per_file: 2`. Patch `Client`, `smart_open.open`, and `gcs_target.sinks.time` (e.g. `side_effect=[t1, t2, t2]` or two distinct return values so the second key gets a different timestamp or chunk index). Write 3 records via `process_record`. Assert: two distinct keys (extract from `smart_open.open` call args: the GCS path contains the key); exactly two `smart_open.open` calls; the third record appears in the write payloads of the second handle (or equivalent observable).
- **Test 2 — `test_chunking_key_format_includes_chunk_index`:** Config with `key_naming_convention` including `{chunk_index}` (e.g. `{stream}/export_date={date}/{timestamp}_{chunk_index}.jsonl`) and `max_records_per_file: 2`. Patch time so keys are deterministic. Write 3 records. Assert: two keys; one key contains the chunk index value for the first chunk (0) and the other for the second chunk (1) (e.g. in the path passed to `smart_open.open`).
- **Test 3 — `test_chunking_record_integrity_no_duplicate_or_dropped`:** Config with `max_records_per_file: 10`. Mock the handle returned by `smart_open.open` so that `write` can be inspected (e.g. replace with a MagicMock and collect `write.call_args_list` or store payloads in a list). Write 25 records. Assert: 25 write calls; 25 distinct record payloads (no duplicate, no dropped). Optionally assert that the first 10 writes go to the first handle, next 10 to the second, last 5 to the third (if the mock exposes which handle received which call).
- **Docstrings:** Each test has a short docstring stating WHAT is being tested and WHY (e.g. “Rotation after N records; core chunking requirement.”).

---

## 3. Test Strategy

**TDD:** These tests are written **first** and must fail (e.g. no rotation yet, no chunk_index in key). Implementation in tasks 05 and 06 will make them pass.

**Order of tests (implementation order within this task):**

1. **Test 1 — Rotation at threshold**  
   Establishes that rotation occurs and the Nth+1 record goes to the new file. Use patched time and capture `smart_open.open` calls to assert two distinct keys and two opens; assert the third record’s payload is written (e.g. to the second handle’s write mock).

2. **Test 2 — Key format with chunk_index**  
   Establishes that when `key_naming_convention` includes `{chunk_index}`, both keys contain the expected chunk index values (0 and 1). Depends on the same patches; focuses on key path content.

3. **Test 3 — Record integrity**  
   Establishes that 25 records produce 25 writes with 25 distinct records. Use a single mock handle that records all write args, or one mock per open so you can optionally assert per-chunk counts (10, 10, 5).

**Determinism:** Patch `gcs_target.sinks.time` so `time.time()` returns fixed value(s) (e.g. first key build gets 1000, after rotation 1001, or use a list for `side_effect`). This keeps key strings stable for assertions.

**Black-box:** Assert only on:

- Arguments to `smart_open.open` (URL/path → key name).
- Number of times `smart_open.open` is called (and optionally that the handle was closed before the second open if easily observable via mock).
- Content of `write` call arguments (record payloads).

Do **not** assert on internal call counts (e.g. “method X called once”) or log output.

**Validity:** Each test must be able to fail (e.g. assert a wrong value) to be valid; no test that can only pass.

---

## 4. Implementation Order

1. **Add Test 1 — Rotation at threshold**
   - In `test_sinks.py`, add a test that:
     - Patches `gcs_target.sinks.Client`, `gcs_target.sinks.smart_open.open`, and `gcs_target.sinks.time` (e.g. `time.time` returns 1000 then 1001 via `side_effect`).
     - Builds sink with `build_sink({"max_records_per_file": 2, "key_naming_convention": "{stream}_{timestamp}.jsonl"})` or similar.
     - Opens the handle by accessing `sink.gcs_write_handle` or by writing the first record; then writes 2 more records (3 total).
     - Asserts `smart_open.open` was called twice; extracts the two keys from the call args (e.g. from the `gs://bucket/key` path); asserts they differ.
     - Asserts the third record’s body appears in one of the write invocations (e.g. from the second handle’s write mock).
   - Add docstring: WHAT — rotation after N records; WHY — core chunking requirement.

2. **Add Test 2 — Key format with chunk_index**
   - Add a test with `key_naming_convention` that includes `{chunk_index}` (e.g. `"{stream}/export_date={date}/{timestamp}_{chunk_index}.jsonl"`) and `max_records_per_file: 2`.
   - Patch time (and optionally date) for deterministic keys. Write 3 records.
   - Assert two keys; assert one key contains the substring or pattern for chunk index 0 and the other for chunk index 1 (e.g. `_0.jsonl` and `_1.jsonl` in the path).
   - Docstring: WHAT — key includes chunk_index when chunking on; WHY — uniqueness when multiple chunks in same second.

3. **Add Test 3 — Record integrity**
   - Build sink with `max_records_per_file: 10`. Use a mock for the file-like returned by `smart_open.open` that records each `write` call’s argument(s).
   - Write 25 records (e.g. `process_record({"id": i}, {})` for i in 0..24).
   - Assert 25 write calls. Assert 25 distinct payloads (e.g. deserialize each write arg and check uniqueness by record content or id).
   - Optionally: if using a new mock handle per `open`, assert first handle gets 10 writes, second 10, third 5.
   - Docstring: WHAT — every record written exactly once; WHY — correctness of the pipeline.

4. **Run tests**
   - Run `uv run pytest loaders/target-gcs/tests/test_sinks.py -v`. The three new tests are expected to fail until 05 and 06 are done. All other tests (including task 02 tests) must still pass.

---

## 5. Validation Steps

- From `loaders/target-gcs/`: run `uv run pytest tests/test_sinks.py -v`. New tests may fail (expected until 05/06); no regressions in existing or task-02 tests.
- From `loaders/target-gcs/`: run `uv run ruff check gcs_target tests` and `uv run ruff format --check gcs_target tests` (or project equivalent). Fix any issues.
- From `loaders/target-gcs/`: run `uv run mypy gcs_target` if the project runs mypy on the package (tests may be excluded). Resolve any new type issues.
- After tasks 05 and 06 are implemented: re-run the full test suite; the three new tests must pass along with all others.

---

## 6. Documentation Updates

- **No new docs required.** Test docstrings document WHAT and WHY for each case.
- If the master plan or testing doc is updated to reference “task 04 tests,” that can be done in the documentation task (08) or in passing; this task does not mandate changes outside `test_sinks.py`.
