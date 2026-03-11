# Impacted Systems — File Chunking by Record Count

**Feature:** target-gcs-file-chunking-by-record-count  
**Scope:** target-gcs loader (PawsForLife/meltano-plugins); package `gcs_target` under `loaders/target-gcs/`.

---

## Summary

Chunking by record count affects the GCS sink’s state, key generation, and handle lifecycle. No changes to the Singer protocol, tap, or other plugins. Config schema and Meltano settings gain one optional setting.

---

## 1. Modules / Files

| Path | Impact |
|------|--------|
| `loaders/target-gcs/gcs_target/sinks.py` | **Primary.** `GCSSink`: add record counter; key recomputation on rotation; close/reopen handle when count threshold reached; optional `{chunk_index}` in key. |
| `loaders/target-gcs/gcs_target/target.py` | **Config only.** Add `max_records_per_file` (optional integer) to `config_jsonschema`. |
| `loaders/target-gcs/meltano.yml` | Add setting for `max_records_per_file` under target-gcs if the project documents loader config there. |
| `loaders/target-gcs/sample.config.json` | Optionally add `max_records_per_file` example (e.g. `1000` or omit to show default “no chunking”). |
| `loaders/target-gcs/README.md` | Document the new setting, behaviour when set vs unset, and key tokens (e.g. `{chunk_index}` when chunking). |
| `loaders/target-gcs/tests/test_sinks.py` | New tests: chunk rotation at threshold; no rotation when unset/0; key uses current timestamp and chunk index per chunk; no duplicate or dropped records. |

---

## 2. Interfaces

- **`GCSSink.key_name` (property):** Today returns a single cached key. With chunking, the key must be recomputed after each rotation (new timestamp and chunk index). So: either clear `_key_name` on rotation so the next read recomputes, or make the property compute from current `_chunk_index` and timestamp when chunking is enabled.
- **`GCSSink.gcs_write_handle` (property):** Today opens one handle per stream and keeps it. With chunking, the sink must close the handle when the record count hits `max_records_per_file`, set `_gcs_write_handle = None`, then allow the property to open a new handle (with the new key) on next write.
- **`GCSSink.process_record(record, context)`:** Remains the single entry for writing records. After writing a record, increment the counter; if counter >= `max_records_per_file`, perform rotation (flush/close handle, clear key state, reset counter or increment chunk index) so the next record goes to a new file.
- **`GCSTarget.config_jsonschema`:** Add optional integer property `max_records_per_file` (0 or absent = no chunking). No change to existing properties.

---

## 3. Behavioural Changes

- **Current:** One GCS object per stream per run; key uses one timestamp (at first key use). One open handle per stream for the run.
- **With chunking disabled (default):** Unchanged: one file per stream, one timestamp per stream.
- **With chunking enabled:** After every `max_records_per_file` records, current file is closed and a new file is opened; key for the new file uses current time and (if implemented) chunk index so object keys are distinct.

---

## 4. Dependencies

- **singer_sdk:** No API change; `RecordSink` and `process_record` contract unchanged. Chunking is internal to the sink.
- **smart_open / google.cloud.storage:** No change; only the key and lifecycle (close/open) change.
- **orjson:** No change.

---

## 5. Out of Scope (Not Impacted)

- Tap or other extractors.
- Singer message format (SCHEMA, RECORD, STATE).
- State file handling.
- Other loaders or targets.
- `date_format` or existing key tokens except addition of optional `{chunk_index}` when chunking is on.
