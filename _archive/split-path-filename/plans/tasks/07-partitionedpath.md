# Task Plan: 07 — PartitionedPath: path_for_record and hive_path

## Overview

This task migrates `PartitionedPath` to the split path/filename model. It adds `path_for_record(record)` that uses `hive_path(record)` from the existing `_partitioned` generator, replaces `get_partition_path_from_schema_and_record` for key building with `path_for_record` + `full_key` + `filename_for_current_file`, and removes `key_template`, `record_path`, and `get_chunk_format_map` usage. Partition change detection compares `path_for_record(record)` with `_current_partition_path`; on change, the handle is closed and state reset. Chunking within a partition uses timestamp-only filenames (no `chunk_index`).

**Dependencies:** Task 01 (constants: `PATH_PARTITIONED` must exist), Task 04 (BasePathPattern: `filename_for_current_file`, `full_key`, removal of `key_template`, `get_chunk_format_map`, `_chunk_index`), Task 02 (date_as_partition fix in `_partitioned`).

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/paths/partitioned.py` | Modify: add `path_for_record`, refactor `process_record`, remove `key_template`, `record_path`, `get_partition_path_from_schema_and_record` usage |
| `loaders/target-gcs/tests/unit/paths/test_partitioned.py` | Modify: add new tests, remove/update tests that rely on old key-building behaviour |

---

## Test Strategy

**TDD:** Write failing tests first, then implement. Per `tests/unit/` mirroring source path; file `test_partitioned.py` for `paths/partitioned.py`. Black-box: assert on observable behaviour (returned keys, written payloads, handle open/close via keys), not call counts or log lines.

### Tests to Add (in order)

1. **`test_path_for_record_uses_hive_path_of_record`** — `path_for_record(record)` returns path matching `{stream}/{hive_path}` where `hive_path` is from `hive_path(record)`. With record `{"region": "eu", "dt": "2024-03-11"}`, path contains `region=eu` and `dt=2024-03-11`. Validates path composition per record.
2. **`test_partition_change_closes_handle_and_resets`** — Processing record in partition A then partition B closes the handle and opens a new key for B; `_current_partition_path` and `_records_written_in_current_file` reset. Validates partition change behaviour.
3. **`test_chunking_within_partition`** — With `max_records_per_file=2` and same partition, three records yield two distinct keys (rotation at limit); both keys share the same partition path segment; filenames differ by timestamp. Validates timestamp-only chunking within partition.

### Tests to Update

- **`test_partitioned_path_keys_contain_partition_segments_from_record`** — Keep; assert key format matches `{prefix}/{stream}/{hive_path}/{timestamp}.jsonl`. Update assertions if key shape changes (no `chunk_index`).
- **`test_partitioned_path_partition_change_closes_handle_and_opens_new_key`** — Keep; already validates partition change. May need minor assertion updates for new key format.
- **`test_partitioned_path_partition_return_creates_new_file`** — Keep; validates partition return creates new file.
- **`test_partitioned_path_rotation_at_limit_within_partition`** — Update: remove assertions on `chunk_index`; assert keys differ by timestamp only; same partition path in both keys.
- **`test_partitioned_path_parser_error_when_date_format_unparseable`** — Keep; ParserError propagation unchanged.
- **`test_partitioned_path_current_key_empty_before_first_write`** — Keep.
- **`test_partitioned_path_current_key_equals_key_after_write`** — Keep; may need key format assertion update.

### Tests to Remove

- Any test that asserts on `get_partition_path_from_schema_and_record` being used for key building.
- Any test that asserts on `key_template` or `chunk_index` in keys.

---

## Implementation Order

1. **Tests first** — Add `test_path_for_record_uses_hive_path_of_record`, `test_partition_change_closes_handle_and_resets`, `test_chunking_within_partition`. Update `test_partitioned_path_rotation_at_limit_within_partition` to remove chunk_index assertions. Run pytest; new tests fail.
2. **Add `path_for_record`** — `def path_for_record(self, record: dict[str, Any]) -> str`: `hive_path_str = self.hive_path(record)`; `return PATH_PARTITIONED.format(stream=self.stream_name, hive_path=hive_path_str)`. Import `PATH_PARTITIONED` from `target_gcs.constants`.
3. **Refactor `process_record`** — Resolve `path = path_for_record(record)`. Compare `path` with `_current_partition_path`; on change: `flush_and_close_handle()`, set `_current_partition_path = path`, reset `_records_written_in_current_file` (do not set `_chunk_index`; base no longer has it). Call `maybe_rotate_if_at_limit()`. Compute `filename = filename_for_current_file()`, `key = full_key(path, filename)`. Set `_key_name = key`. Open handle if needed; write record.
4. **Remove `key_template`** — Delete the property from `PartitionedPath`.
5. **Remove `record_path`** — Delete the method; key building is now inline in `process_record`.
6. **Remove `get_partition_path_from_schema_and_record` usage** — Delete import and all calls. Partition path comes from `path_for_record(record)`.
7. **Remove obsolete imports** — Remove `DEFAULT_KEY_NAMING_CONVENTION_HIVE`, `get_partition_path_from_schema_and_record`, `DEFAULT_PARTITION_DATE_FORMAT` from partition_path helpers if no longer used.
8. **Fix partition change reset** — Remove `self._chunk_index = 0` (base no longer has `_chunk_index`). Ensure `_records_written_in_current_file = 0` on partition change.
9. **Run tests** — `uv run pytest tests/unit/paths/test_partitioned.py` from `loaders/target-gcs/`. All tests pass.

---

## Validation Steps

1. **PartitionedPath tests pass:** `cd loaders/target-gcs && uv run pytest tests/unit/paths/test_partitioned.py -v`
2. **Ruff:** `uv run ruff check target_gcs/paths/partitioned.py`
3. **MyPy:** `uv run mypy target_gcs/paths/partitioned.py`
4. **Acceptance:** `path_for_record(record)` returns path with `hive_path(record)`; partition change closes handle and resets; chunking within partition uses timestamp-only filenames; no `get_partition_path_from_schema_and_record`, `key_template`, or `record_path` in PartitionedPath.

---

## Documentation Updates

- **None** for this task. AI context and README updates are in task 10. Interfaces.md already documents `path_for_record` and the new `process_record` flow.

---

## Notes

- **`hive_path(record)`** — PartitionedPath already has `hive_path(record)` that uses `get_hive_path_generator` from `_partitioned`. No change to that method; `path_for_record` delegates to it.
- **Partition change vs rotation** — Partition change resets `_current_partition_path` and `_records_written_in_current_file`; rotation (at `max_records_per_file`) is handled by `maybe_rotate_if_at_limit()` in base, which no longer uses `_chunk_index`.
- **`get_partition_path_from_schema_and_record`** — Task 09 (helpers cleanup) may remove or deprecate this; this task only removes its usage from PartitionedPath.
- **Key format** — Final key: `{key_prefix}/{stream}/{hive_path}/{timestamp}.jsonl` (normalized). No `chunk_index` suffix.
