# Background

When `partition_date_field` is set, process_record must: (1) resolve partition path for the record, (2) on partition change close handle and clear `_key_name` and `_current_partition_path` (and reset chunk index on partition change per architecture), (3) on chunk rotation (max_records_per_file) close and clear key, increment chunk index, keep partition path, (4) build key via `_build_key_for_record`, (5) open handle if none for that key, (6) write record. When the partition "returns" (same value again), do not reopen the old file—build a new key (new timestamp/chunk). This task implements the full process_record branch and handle lifecycle.

**Dependencies:** Tasks 01–05 (config, partition resolution, date_fn/state, key building).

**Plan reference:** `plans/master/architecture.md` (Data flow, Handle lifecycle), `plans/master/implementation.md` (process_record), `plans/master/testing.md` (Chunking with partition, Partition change).

---

# This Task

- **File:** `loaders/target-gcs/gcs_target/sinks.py`
- **process_record when partition_date_field is set:**
  1. Resolve partition path: `get_partition_path_from_record(record, partition_date_field, partition_date_format or DEFAULT_HIVE_FORMAT, self._date_fn() if self._date_fn else datetime.today())`.
  2. If partition_path != _current_partition_path: call close/clear logic (same as rotation but also clear _current_partition_path and set to new path; reset _chunk_index on partition change per architecture).
  3. If chunking and _records_written_in_current_file >= max_records_per_file: rotate (close, clear key, increment chunk index, reset count); keep _current_partition_path.
  4. Build key = _build_key_for_record(record, partition_path).
  5. If handle is None or key changed, close if needed and open new handle for key.
  6. Write record to handle; increment _records_written_in_current_file if chunking.
- **process_record when partition_date_field is unset:** Leave existing logic unchanged (current key_name, single handle, existing rotation).
- Reuse existing smart_open and Client() pattern for opening handles. On partition change, set _current_partition_path to the new path after clearing (so next write uses it for key building).
- **Acceptance criteria:** Chunking with same partition produces multiple keys with same partition path; partition A then B then A produces three distinct keys (A, B, A' where A' is new file); drain/close still closes the single open handle.

---

# Testing Needed

- **Chunking with partition: rotation within partition:** Sink with `partition_date_field` and `max_records_per_file=2`; process three records with same partition value. Assert two keys (chunk 0 and chunk 1) with same partition path segment. Use mock or capture keys passed to open. **WHAT:** Rotation creates new key but same partition. **WHY:** Chunking interaction.
- **Partition change closes handle and new key on return:** Process record partition A, then B, then A again. Assert three keys (A, B, A') where A' is a new key (e.g. new timestamp), not reopening A. **WHAT:** Option (c) behaviour: no reopen; new file when partition returns. **WHY:** Handle strategy.

Assert on observable behaviour (keys opened or written); do not assert "close was called once." Use fixed date_fn and time_fn for deterministic key assertions.
