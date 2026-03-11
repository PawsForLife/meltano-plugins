# Background

Core behaviour: when `max_records_per_file` is N, after N records the sink rotates to a new file; the new key uses current time and `chunk_index`; every record is written exactly once. These tests define the expected behaviour and will fail until key computation (05) and rotation (06) are implemented.

**Depends on:** 01, 02, 03.

# This Task

- **File:** `loaders/target-gcs/tests/test_sinks.py`
- Use `build_sink(config=...)`, patch `Client` and `smart_open.open`. For deterministic keys, patch `gcs_target.sinks.time` so `time.time()` returns a known value, then a second value after "rotation" (e.g. side_effect or return_value list).
- **Test 1 — Rotation at threshold:** Config `max_records_per_file: 2`. Write 3 records. Assert two distinct keys (e.g. different chunk_index or timestamp). Assert the handle was closed and reopened (e.g. two `smart_open.open` calls, or one close before the second open). Assert the record that triggered rotation (3rd record) is written to the new file (e.g. via mock write call args or handle used). Docstring: WHAT — rotation after N records; WHY — core chunking requirement.
- **Test 2 — Key format with chunk_index:** Set `key_naming_convention` to include `{chunk_index}` (e.g. `{stream}/export_date={date}/{timestamp}_{chunk_index}.jsonl`). Enable chunking (e.g. `max_records_per_file: 2`), write past one rotation (e.g. 3 records). Assert the two keys differ and both contain the expected chunk index values (0 and 1). Docstring: WHAT — key includes chunk_index when chunking on; WHY — uniqueness when multiple chunks in same second.
- **Test 3 — Record integrity:** With chunking (e.g. `max_records_per_file: 10`), write 25 records. Capture all write payloads (e.g. mock the handle's `write` and collect arguments). Assert 25 write calls with 25 distinct records (no duplicate, no dropped). Optionally assert first chunk gets 10, second 10, third 5. Docstring: WHAT — every record written exactly once; WHY — correctness of the pipeline.
- Assert on observable outcomes (keys, write call args, open/close count), not call counts or logs. Each test must be able to fail (e.g. wrong expectation) to be valid.

# Testing Needed

- Run the new tests; they fail until tasks 05 and 06 are done. After 05 and 06, all three tests must pass.
- Ensure existing tests and task 02 tests still pass.
