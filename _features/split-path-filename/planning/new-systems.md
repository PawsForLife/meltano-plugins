# New Systems — split-path-filename

## Summary

The feature introduces fixed path and filename constants and new methods on `BasePathPattern`. No new modules or external dependencies are added.

---

## Constants (`target_gcs/constants.py`)

| Constant | Value | Purpose |
|----------|-------|---------|
| `PATH_SIMPLE` | `"{stream}/{date}"` | Path part for SimplePath (no Hive). |
| `PATH_DATED` | `"{stream}/{hive_path}"` | Path part for DatedPath (extraction date only). |
| `PATH_PARTITIONED` | `"{stream}/{hive_path}"` | Path part for PartitionedPath (schema-driven). |
| `FILENAME_TEMPLATE` | `"{timestamp}.jsonl"` | Filename for all patterns. |

`DEFAULT_PARTITION_DATE_FORMAT` remains; used by `_partitioned` and DatedPath.

---

## BasePathPattern Methods

| Method | Signature | Behavior |
|--------|-----------|----------|
| `filename_for_current_file()` | `-> str` | Returns `{timestamp}.jsonl` with current timestamp. Refreshes timestamp on each call (or on rotate). |
| `full_key(path, filename)` | `(path: str, filename: str) -> str` | Applies `key_prefix` to `path/filename`, normalizes slashes, returns final key. |

---

## Path Pattern Flow

| Pattern | Path Source | Filename Source |
|---------|-------------|-----------------|
| SimplePath | `PATH_SIMPLE.format(stream=..., date=...)` at init | `filename_for_current_file()` |
| DatedPath | `PATH_DATED.format(stream=..., hive_path=extraction_date_formatted)` at init | `filename_for_current_file()` |
| PartitionedPath | `PATH_PARTITIONED.format(stream=..., hive_path=hive_path(record))` per record | `filename_for_current_file()` |

All patterns call `full_key(path, filename)` to produce the final key.

---

## Chunking Behavior

- **Timestamp-only:** No `chunk_index`. Assume ≥1 second between chunks.
- On rotate: `flush_and_close_handle`; reset `_records_written_in_current_file`; next `filename_for_current_file()` uses new timestamp.

---

## DatedPath vs PartitionedPath Path Semantics

- **DatedPath:** `hive_path` = extraction date formatted via `DEFAULT_PARTITION_DATE_FORMAT` (e.g. `year=2024/month=03/day=13`).
- **PartitionedPath:** `hive_path` = `hive_path(record)` from `_partitioned.get_hive_path_generator` (field=value from partition fields).
