# 07 — PartitionedPath: path_for_record and hive_path

## Background

PartitionedPath must use `path_for_record(record)` with `hive_path(record)` from `_partitioned`; partition change = compare path outputs; key building via `full_key`. Replaces `get_partition_path_from_schema_and_record` for key generation. Depends on tasks 01 (constants), 04 (BasePathPattern methods).

## This Task

**Files to modify:**
- `loaders/target-gcs/target_gcs/paths/partitioned.py`

**Implementation steps (TDD first):**

1. **Tests first** in `tests/unit/paths/test_partitioned.py`:
   - `test_path_for_record_uses_hive_path_of_record`: `path_for_record(record)` returns path with hive_path from record.
   - `test_partition_change_closes_handle_and_resets`: On partition change, new file opened; record count reset.
   - `test_chunking_within_partition`: At max_records, rotate; new filename; same partition path.
   - Remove tests using `get_partition_path_from_schema_and_record` for key building.

2. **Implementation:**
   - Add `path_for_record(self, record: dict[str, Any]) -> str`: `hive_path = self.hive_path(record)`; `return PATH_PARTITIONED.format(stream=stream_name, hive_path=hive_path)`.
   - Partition change: compare `path_for_record(record)` with `_current_partition_path`; on change, `flush_and_close_handle()`, set `_current_partition_path`, reset `_records_written_in_current_file`.
   - In `process_record`: resolve path via `path_for_record(record)`; handle partition change; `maybe_rotate_if_at_limit()`; `filename_for_current_file()`; `full_key(path, filename)`; open handle; write record.
   - Remove `get_partition_path_from_schema_and_record` usage for key building; remove `key_template`, `record_path`; use `hive_path(record)` from `_partitioned`.
   - Import `PATH_PARTITIONED` from `target_gcs.constants`.

**Acceptance criteria:**
- `path_for_record(record)` returns path with `hive_path(record)`.
- Partition change detection works; handle closed and reset on change.
- Chunking within partition works.
- Tests pass.
