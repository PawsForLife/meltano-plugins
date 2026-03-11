# Implementation Plan — Testing: File Chunking by Record Count

**Feature:** target-gcs-file-chunking-by-record-count

---

## Test Strategy

- **TDD:** Write or extend tests first; implement until they pass. Tests validate observable behaviour (keys, record counts, number of opened handles/files), not internal call counts or log lines (black-box).
- **Location:** All new tests in `loaders/target-gcs/tests/test_sinks.py`. Use existing sink-build helpers (e.g. `build_sink(config=...)`) and mocks for GCS client and `smart_open`.
- **Determinism:** Use fixed or patched time in tests that assert key content so that `timestamp` and ordering are stable.

---

## Test Cases

### 1. Chunking disabled (backward compatibility)

- **What:** With `max_records_per_file` unset or 0, exactly one key and one handle per stream; no rotation.
- **Why:** Ensures existing behaviour is unchanged when the option is not used.
- **How:** Build sink with config without `max_records_per_file` (or `max_records_per_file: 0`). Write more than one record (e.g. 5). Assert `key_name` is unchanged after multiple writes; assert only one handle is opened (e.g. one `smart_open.open` call, or one close). Assert no `chunk_index` in key if convention does not require it.

### 2. Chunking enabled — rotation at threshold

- **What:** When `max_records_per_file` is N, after N records the current handle is closed and the next write opens a new handle with a new key (new timestamp and/or chunk index).
- **Why:** Core requirement that files are rotated after N records.
- **How:** Build sink with `max_records_per_file: 2`. Patch time to return a known value, then allow a second value after “rotation.” Write 3 records. Assert two distinct keys (e.g. different chunk_index or timestamp). Assert handle was closed and reopened (e.g. two `smart_open.open` calls, or one close before the second open). Record that triggered rotation (3rd record) is written to the new file.

### 3. Key format with chunk_index

- **What:** When chunking is on, key computation includes `chunk_index` in the format map so a convention like `{stream}/export_date={date}/{timestamp}_{chunk_index}.jsonl` produces distinct keys per chunk.
- **Why:** Uniqueness when multiple chunks are created in the same second.
- **How:** Set `key_naming_convention` to include `{chunk_index}`. Enable chunking, write past one rotation. Assert the two keys differ and both contain the expected chunk index values (0 and 1).

### 4. Record integrity — no duplicate or dropped records

- **What:** Every record is written exactly once; record count in each chunk ≤ max_records_per_file; last chunk may have fewer.
- **Why:** Correctness of the pipeline.
- **How:** With chunking (e.g. max 10), write 25 records. Capture all write payloads (e.g. mock the handle’s `write` and collect arguments). Assert 25 write calls with 25 distinct records. Optionally assert first chunk gets 10, second 10, third 5 (or similar), depending on how the mock exposes “which file” is written to.

### 5. Chunking disabled — key has no chunk_index when convention omits it

- **What:** When chunking is off, key format is unchanged; if the convention does not use `{chunk_index}`, key is as today.
- **How:** Build sink without chunking. Assert `key_name` does not contain a literal `{chunk_index}` and matches the existing pattern (stream, date, timestamp only).

### 6. Integration (optional, if environment allows)

- **What:** Run tap → target-gcs with `max_records_per_file` set; verify multiple GCS objects per stream with distinct keys and correct record counts.
- **Why:** End-to-end validation. May be skipped if no GCS available in CI; unit tests above are sufficient for merge.

---

## Test Implementation Notes

- Use existing patterns from `test_sinks.py`: patch `gcs_target.sinks.Client` and `smart_open.open`; build sink via helper with config dict.
- For time: patch `gcs_target.sinks.time` so `time.time()` returns a fixed value, then a different value after “rotation,” so keys are predictable.
- Assert on returned or observable data (e.g. `sink.key_name`, number of open/close calls, write call args), not on “called_once” or log messages.
- Add docstrings to each test: WHAT is being tested and WHY (e.g. “Ensures that when chunking is disabled, only one file per stream is used and key format is unchanged.”).

---

## Regression

- Existing tests in `test_sinks.py` and `test_core.py` must continue to pass. If any test uses a config that now includes an extra key, ensure default behaviour is unchanged (no chunking).
- No test may be marked as expected failure unless there is a known, documented reason.
