# Selected Solution — File Chunking by Record Count (Internal)

**Feature:** target-gcs-file-chunking-by-record-count

---

## Approach

Implement record-count-based file rotation entirely inside `GCSSink`. No external library. Config: optional `max_records_per_file` (integer; 0 or unset = no chunking). When the threshold is reached, close the current GCS handle, clear the cached key so the next key uses the current time (and chunk index), then on the next write open a new handle. Key uniqueness when chunking: include `{chunk_index}` in the key so multiple chunks in the same second do not collide.

---

## 1. Config

- **`target.py`:** Add to `config_jsonschema`:
  - `max_records_per_file` (integer, optional). Default/absent or 0 = chunking disabled.
- **Sink:** Read via `self.config.get("max_records_per_file", 0)`. If ≤ 0, behaviour is unchanged (one file per stream).

---

## 2. GCSSink state (new)

- **`_records_written_in_current_file`** (int): Count of records written to the current open file. Initialized to 0. After each write, increment; on rotation, set to 0 (or to 1 if the record that triggered rotation is written to the new file after rotation).
- **`_chunk_index`** (int): 0-based index of the current chunk. Initialized to 0. Increment when rotating to a new file. Used in key when chunking is enabled.

---

## 3. Key naming

- **When chunking disabled:** Keep current behaviour: `key_name` computed once, cached in `_key_name`; tokens `{stream}`, `{date}`, `{timestamp}` (timestamp at first use).
- **When chunking enabled:** After rotation, clear `_key_name` (e.g. set to `""`) so the next access to `key_name` recomputes. When building the key, include `chunk_index` in the format map so the convention can use `{chunk_index}` (e.g. `{stream}/export_date={date}/{timestamp}_{chunk_index}.jsonl`). Use current `time.time()` (or equivalent) for `timestamp` at key build time so each chunk gets a fresh timestamp.
- **Uniqueness:** Using both current timestamp and `_chunk_index` in the key avoids collisions when multiple chunks are created in the same second.

---

## 4. Handle lifecycle

- **Open:** Unchanged. `gcs_write_handle` is lazy: when `_gcs_write_handle` is None, open with `smart_open.open(..., key_name, ...)` and assign to `_gcs_write_handle`.
- **Rotation (when chunking enabled and `_records_written_in_current_file >= max_records_per_file`):**
  1. Flush and close `_gcs_write_handle`.
  2. Set `_gcs_write_handle = None`.
  3. Set `_key_name = ""` (force key recomputation on next use).
  4. Increment `_chunk_index`.
  5. Set `_records_written_in_current_file = 0`.
- **Next write:** `process_record` writes the record. Access to `gcs_write_handle` sees `_gcs_write_handle` is None, so `key_name` is recomputed (new timestamp and chunk index), and a new handle is opened. Then write the record and set `_records_written_in_current_file = 1` (or increment after write).

---

## 5. process_record algorithm

```
1. If chunking enabled and _records_written_in_current_file >= max_records_per_file:
   - Close _gcs_write_handle, set to None.
   - Clear _key_name.
   - Increment _chunk_index.
   - Set _records_written_in_current_file = 0.
2. Write record to gcs_write_handle (opens new handle if needed).
3. If chunking enabled: increment _records_written_in_current_file.
```

Order: check threshold **before** writing the record that would exceed it, so the record that triggers rotation is written to the **new** file (not the old one). So “after writing 100 records, rotate” means: when we have already written 100 records to the current file, rotate, then write the 101st to the new file.

---

## 6. Key property behaviour

- **key_name:** If `_key_name` is non-empty, return it. Else: build key from convention; when chunking enabled, include `chunk_index` in format_map and use current time for `timestamp`; store in `_key_name` and return. When chunking disabled, same as today (no chunk_index).
- **gcs_write_handle:** If `_gcs_write_handle` is None, open with current `key_name` and assign. Return handle. No change to signature or callers.

---

## 7. Sink teardown

On sink close/drain, the existing behaviour (closing open handles) remains. No need to “finalize” the last chunk beyond normal close; the last chunk may contain fewer than `max_records_per_file` records.

---

## 8. Testing focus

- Chunking off: no rotation; one key per stream; key has no chunk index.
- Chunking on: after N records, handle closed and next write uses new key (new timestamp and chunk index); record counts per chunk ≤ N; no duplicate or dropped records.
- Key format: when chunking is on, key includes chunk index (and optionally timestamp) as specified by convention.

---

## 9. References

- Current implementation: `loaders/target-gcs/gcs_target/sinks.py` (`GCSSink`, `key_name`, `gcs_write_handle`, `process_record`).
- Config and schema: `loaders/target-gcs/gcs_target/target.py` (`config_jsonschema`).
- Singer SDK: `RecordSink` — [SDK RecordSink](https://sdk.meltano.com/en/latest/classes/singer_sdk.RecordSink.html). No SDK change; rotation is internal to the sink.
