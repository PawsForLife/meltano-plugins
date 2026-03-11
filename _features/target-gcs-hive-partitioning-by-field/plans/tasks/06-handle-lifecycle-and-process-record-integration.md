# Task Plan: 06-handle-lifecycle-and-process-record-integration

**Feature:** target-gcs-hive-partitioning-by-field  
**Task:** Wire partition resolution and key building into `process_record`; implement full handle lifecycle when `partition_date_field` is set (close on partition change, new key when partition returns, chunk rotation within partition).  
**Master plan:** [../master/overview.md](../master/overview.md), [../master/implementation.md](../master/implementation.md), [../master/architecture.md](../master/architecture.md), [../master/interfaces.md](../master/interfaces.md), [../master/testing.md](../master/testing.md)

---

## 1. Overview

This task implements the **process_record** branch when `partition_date_field` is set and the full **handle lifecycle** for partition-by-field: (1) resolve partition path per record, (2) on partition change close handle and clear key/partition state and reset chunk index, (3) on chunk rotation (max_records_per_file) rotate within current partition, (4) build key via `_build_key_for_record`, (5) open handle when none or when key changed, (6) write record and increment count if chunking. When `partition_date_field` is unset, existing process_record logic remains unchanged. Option (c) behaviour: when a partition "returns" (same value again), do not reopen the old file—build a new key (new timestamp/chunk) and open a new handle. Drain/close still closes the single open handle.

**Scope:** `sinks.py` only—process_record conditional branch and any shared close/clear helper used on partition change. Tests in `test_sinks.py` for chunking-with-partition and partition-change-then-return.

**Dependencies:** Tasks 01–05 must be complete (config schema, partition resolution, date_fn/partition state, key building). Assumes `get_partition_path_from_record`, `_build_key_for_record`, `_current_partition_path`, `_date_fn`, and `DEFAULT_PARTITION_DATE_FORMAT` (or equivalent) exist in sinks.

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `loaders/target-gcs/gcs_target/sinks.py` | Modify | **process_record:** When `config.get("partition_date_field")` is set: (1) Resolve partition path via `get_partition_path_from_record(record, partition_date_field, partition_date_format or DEFAULT_PARTITION_DATE_FORMAT, self._date_fn() if self._date_fn else datetime.today())`. (2) If `partition_path != _current_partition_path`: call close/clear logic (same as rotation: close handle, clear `_key_name`, set `_current_partition_path` to the new path, reset `_chunk_index` per architecture). (3) If chunking and `_records_written_in_current_file >= max_records_per_file`: call `_rotate_to_new_chunk()` (keep `_current_partition_path`). (4) Build `key = _build_key_for_record(record, partition_path)`. (5) If `_gcs_write_handle is None` or `_key_name != key`: close handle if present, set `_key_name = key`, open new handle for key (reuse existing smart_open + Client pattern). (6) Write record to handle; if chunking increment `_records_written_in_current_file`. When `partition_date_field` is unset: keep existing process_record body unchanged. Ensure handle open uses the key from step (5) and that `gcs_write_handle` property or inline open does not overwrite `_key_name` when partition-by-field is on (may require opening via a path that uses the built key explicitly). |
| `loaders/target-gcs/tests/test_sinks.py` | Modify | Add two tests (TDD first): **Chunking with partition:** Sink with `partition_date_field` and `max_records_per_file=2`; process three records with same partition value; assert two distinct keys (chunk 0 and chunk 1) with same partition path segment (e.g. capture keys passed to open or assert on sink state). **Partition change then return:** Process record for partition A, then B, then A again; assert three distinct keys (A, B, A') where A' is a new key (e.g. new timestamp), not a reopen of A. Use fixed `date_fn` and `time_fn` for deterministic keys. Assert on observable behaviour (keys opened or written); do not assert on "close was called once." |

No new files.

---

## 3. Test Strategy

TDD: write the two behavioural tests first, then implement the process_record branch until they pass.

**Location:** `loaders/target-gcs/tests/test_sinks.py`.

| Test | What | Why |
|------|------|-----|
| **Chunking with partition: rotation within partition** | Build sink with `partition_date_field` (e.g. `"dt"`), `max_records_per_file=2`, fixed `date_fn`/`time_fn`. Process three records with same partition value (e.g. `{"dt": "2024-03-11"}`). Assert two keys are produced (chunk 0 and chunk 1) and both contain the same partition path segment (e.g. `year=2024/month=03/day=11`). Capture keys via mock on `smart_open.open` or by inspecting sink state after writes. | Validates that chunk rotation creates a new key within the same partition (chunking interaction). |
| **Partition change closes handle and new key on return** | Build sink with `partition_date_field`, fixed `date_fn`/`time_fn`. Process one record partition A (e.g. `{"dt": "2024-03-10"}`), then one record partition B (`{"dt": "2024-03-11"}`), then one record partition A again. Assert three distinct keys (e.g. A path, B path, A' path where A' differs from A by timestamp/chunk). | Validates option (c): no reopen; when partition returns, a new file is created. |

Black box: assert on keys (paths) produced or passed to open; do not assert on call counts (e.g. "close was called once"). Use deterministic `date_fn` and `time_fn` so key strings are predictable. If the sink does not expose keys directly, mock `smart_open.open` and collect the key from the URI (e.g. `gs://bucket/key`) and assert on the list of keys.

---

## 4. Implementation Order

1. **Add tests** in `test_sinks.py`:
   - `test_chunking_with_partition_rotation_within_partition` — Sink with partition_date_field, max_records_per_file=2, date_fn/time_fn fixed. Process three records same partition. Assert two keys, same partition path segment in both.
   - `test_partition_change_then_return_creates_three_distinct_keys` — Process A, B, A. Assert three distinct keys; third key (A') is not identical to first (A).
2. **Run tests** — expect failures (process_record does not yet implement partition branch).
3. **Implement process_record branch in `sinks.py`:**
   - At top of `process_record`, if not `config.get("partition_date_field")`: keep existing logic (current block) and return.
   - Else (partition-by-field on):
     - Resolve partition path: `partition_path = get_partition_path_from_record(record, self.config["partition_date_field"], self.config.get("partition_date_format") or DEFAULT_PARTITION_DATE_FORMAT, self._date_fn() if self._date_fn else datetime.today())`.
     - If `partition_path != self._current_partition_path`: close handle (flush if present, close, set `_gcs_write_handle = None`), clear `_key_name = ""`, set `_current_partition_path = partition_path`, reset `_chunk_index = 0`, reset `_records_written_in_current_file = 0`.
     - If chunking and `_records_written_in_current_file >= max_records_per_file`: call `_rotate_to_new_chunk()`.
     - `key = self._build_key_for_record(record, partition_path)`.
     - If `_gcs_write_handle is None` or `_key_name != key`: if handle exists, flush and close and set to None; set `_key_name = key`; open handle (e.g. `smart_open.open(f"gs://{bucket}/{key}", "wb", transport_params={"client": Client()})`) and assign to `_gcs_write_handle`.
     - Write record: `_gcs_write_handle.write(orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE))`.
     - If chunking: `_records_written_in_current_file += 1`.
4. **Handle open for partition-by-field:** Ensure the handle is opened with the built `key` (not `self.key_name` which may behave differently when partition_date_field is set). Use the same Client() and smart_open pattern as existing `gcs_write_handle` property, but with the explicit key from step above.
5. **Run tests** — both new tests and existing tests pass. Ensure drain/close still closes the single handle (existing drain behaviour should suffice).
6. **Lint/format** per project rules (Ruff, types).

---

## 5. Validation Steps

- [ ] `test_chunking_with_partition_rotation_within_partition` passes: two keys, same partition path.
- [ ] `test_partition_change_then_return_creates_three_distinct_keys` passes: three distinct keys; A' ≠ A.
- [ ] All existing tests in `test_sinks.py` pass (no regression when partition_date_field is unset).
- [ ] Full test suite for `loaders/target-gcs` passes.
- [ ] Linter/type checker passes for `sinks.py` and `test_sinks.py`.
- [ ] Drain/close behaviour: single open handle is closed when sink is closed (no change to drain contract).

---

## 6. Documentation Updates

**This task:** Update the `process_record` docstring in `sinks.py` to describe the partition-by-field branch: when `partition_date_field` is set, partition path is resolved per record; on partition change the handle is closed and state cleared and chunk index reset; on chunk rotation within partition a new key is used; key is built via `_build_key_for_record`; when partition "returns" a new key (new file) is used. Keep concise per content_length rules. No README or AI context changes in this task (task 08 / 09).
