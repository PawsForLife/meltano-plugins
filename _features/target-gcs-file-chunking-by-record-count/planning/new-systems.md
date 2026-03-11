# New Systems — File Chunking by Record Count

**Feature:** target-gcs-file-chunking-by-record-count

---

## Summary

No new modules or services. New behaviour is confined to the existing `GCSSink`: optional config, per-stream counters, key recomputation on rotation, and optional `{chunk_index}` token. New tests extend the existing sink test module.

---

## 1. New Config / Schema

- **Setting:** `max_records_per_file` (optional integer).
- **Semantics:** Maximum records per GCS object. When 0 or unset, chunking is disabled (current behaviour).
- **Where:** `GCSTarget.config_jsonschema` in `target.py`; read in `GCSSink` via `self.config.get("max_records_per_file", 0)`.
- **Meltano:** If loader config is documented in `meltano.yml`, add a setting entry for `max_records_per_file`.

---

## 2. New State in GCSSink

- **Record counter:** e.g. `_records_written_in_current_file` (int), incremented in `process_record` after each write; reset to 0 (or 1) when opening a new chunk.
- **Chunk index (optional but recommended):** e.g. `_chunk_index` (int), incremented when rotating to a new file; used in key when chunking is enabled so keys stay unique (e.g. `{timestamp}_{chunk_index}.jsonl`).

No new classes or modules; state lives on the existing `GCSSink` instance.

---

## 3. New Key Token (Optional)

- **Token:** `{chunk_index}`.
- **When:** Only relevant when `max_records_per_file > 0`. Key naming convention may include `{chunk_index}` so each chunk has a distinct key even if timestamps collide (e.g. same second).
- **Default convention with chunking:** e.g. `{stream}/export_date={date}/{timestamp}_{chunk_index}.jsonl` or keep existing convention and append `_{chunk_index}` when chunking is on.

---

## 4. New Logic (Functions / Methods)

- **Rotation helper:** A small method or inline block in `process_record`: when `_records_written_in_current_file >= max_records_per_file`, (1) flush and close `_gcs_write_handle`, (2) set `_gcs_write_handle = None`, (3) clear `_key_name` (so next `key_name` use gets fresh timestamp and chunk index), (4) increment `_chunk_index`, (5) reset `_records_written_in_current_file` to 0. The next write will trigger a new handle open via the existing `gcs_write_handle` property.
- **Key name:** When chunking is enabled, key computation (in property or helper) must use current timestamp at key build time and include `chunk_index` in the format map. When chunking is disabled, behaviour stays as today (single cached key, no chunk index).

No new public classes or modules; logic is inside `GCSSink`.

---

## 5. New Tests

- Chunking disabled: `max_records_per_file` unset or 0 → one file per stream; key unchanged from current behaviour.
- Chunking enabled: after N records, handle is closed and next write opens a new handle; new key uses current timestamp (and chunk index if present).
- Key uniqueness: with chunking, keys for consecutive chunks differ (timestamp and/or chunk index).
- Record integrity: no record lost, no record written twice; record count per chunk ≤ `max_records_per_file`; last chunk may have fewer.

All in `loaders/target-gcs/tests/test_sinks.py` (or equivalent sink test module). No new test modules required.

---

## 6. Documentation

- **README:** Describe `max_records_per_file`, “one file per stream” when unset vs “multiple files per stream when set”, and the optional `{chunk_index}` token.
- **Inline:** Short docstrings/comments in `sinks.py` for the new state and rotation behaviour.

No new docs folders or external systems.
