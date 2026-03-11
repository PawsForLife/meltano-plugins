# Master Plan — Architecture: Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**See:** [overview.md](overview.md), [interfaces.md](interfaces.md)

---

## Design approach

- **Internal implementation** within target-gcs; no new top-level modules.
- **Handle strategy (option c):** One active GCS write handle per sink. When the partition value **changes**, close the handle and clear current key/partition state. When the partition value **returns** (same value seen again later), do not reopen the old file; build a **new** key (e.g. new timestamp or chunk index) and open a new file. Result: one open handle; no dict of handles; no reopen of the same path; multiple files per partition when records interleave.

---

## Component breakdown

### 1. Config (GCSTarget)

- **Location:** `gcs_target/target.py`
- **Responsibility:** Extend `config_jsonschema` with `partition_date_field` (optional string) and `partition_date_format` (optional string; default Hive-style). No change to sink class binding.

### 2. Partition resolution

- **Location:** `gcs_target/sinks.py` (module-level or GCSSink; see interfaces.md).
- **Responsibility:** Given record, config, and fallback date: read configured field → parse as date/datetime (ISO + fallback format) → format with `partition_date_format` → return partition path string. On missing or unparseable value, return path from fallback date (or sentinel; see selected-solution). Parsing is single-path: try parse; if invalid, use fallback; no re-validation downstream (validation-over-testing rule).

### 3. Key construction (GCSSink)

- **When partition-by-field is off:** Unchanged. `key_name` from run date, `{date}`, `{timestamp}`, `{chunk_index}` as today.
- **When partition-by-field is on:** Key is built **per record** (not cached for the whole stream). Tokens: `{stream}`, `{partition_date}`, `{timestamp}`, `{chunk_index}` (if chunking). `{partition_date}` is the partition path string for that record. After a partition change, the next write gets a new key (new file), including when the partition “returns.”

### 4. Sink state (GCSSink)

- **Existing:** `_gcs_write_handle`, `_key_name`, `_records_written_in_current_file`, `_chunk_index`, `_time_fn`.
- **New when partition-by-field is on:** `_current_partition_path: Optional[str]`, and key/handle are cleared when partition changes. No dict of handles; no “reopen same path.”

### 5. Handle lifecycle

- **First write for a partition (or after a change):** Build key for this record (with current partition path, timestamp, chunk index). Open handle for that key. Write record.
- **Partition change:** Close handle, clear `_key_name` and `_current_partition_path`. Next write builds a new key (possibly same partition path again → new file).
- **Chunking (max_records_per_file) with partition-by-field:** Rotation applies **within** the current partition. On rotation: close handle, clear key, increment chunk index, reset record count; next key uses same partition path but new chunk index (and/or timestamp). On partition change: close, clear key and partition path, reset chunk index for the new partition.

### 6. Drain / close

- On sink drain, close the single open handle if any. No iteration over a handle dict.

---

## Data flow (partition-by-field on)

1. RECORD arrives → `process_record(record, context)`.
2. Resolve partition path from record via partition-resolution helper (fallback if missing/invalid).
3. If partition path ≠ `_current_partition_path`: close handle, clear `_key_name` and `_current_partition_path`, (if chunking reset or keep chunk index per design).
4. Build key for this record: prefix + template with `stream`, `partition_date`, `timestamp`, optional `chunk_index`.
5. If no handle open, open handle for that key.
6. Write record to handle.
7. If chunking and record count reached, rotate (close, clear key, increment chunk index) — same partition path, new key next time.

---

## Design patterns and principles

- **Dependency injection:** Run date (and optionally time) for key building and fallback must be injectable (e.g. `time_fn` already exists; add or extend for date used in partition fallback and in key template so tests are deterministic). See [interfaces.md](interfaces.md).
- **Validation over re-checking:** Parse record field once into a date; if parsing fails, use fallback. Once a partition path string is produced, do not re-validate.
- **Single responsibility:** Partition resolution is a pure function (record, config, fallback_date → path string). Sink owns handle lifecycle and key building.
- **References:** `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` (config schema, typing, DI); `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` (key naming, handle).
