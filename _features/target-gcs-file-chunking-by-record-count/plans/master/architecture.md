# Implementation Plan — Architecture: File Chunking by Record Count

**Feature:** target-gcs-file-chunking-by-record-count

---

## System Design and Structure

Chunking is implemented **inside the existing GCSSink**. No new modules or services. Data flow remains: Target parses Singer messages → routes RECORDs to the sink for each stream → sink writes to GCS. The only addition is conditional rotation inside the sink when a per-stream record count reaches the configured limit.

---

## Component Breakdown and Responsibilities

| Component | Responsibility |
|-----------|-----------------|
| **GCSTarget** (`target.py`) | Declare `max_records_per_file` in `config_jsonschema`; pass config to sinks unchanged. |
| **GCSSink** (`sinks.py`) | Read `max_records_per_file` from config; maintain `_records_written_in_current_file` and `_chunk_index`; in `process_record`, check count before write, rotate (close handle, clear key, increment chunk index, reset count) when at limit, then write; recompute key when chunking and `_key_name` is cleared so new key uses current time and `chunk_index`. |

---

## Data Flow and Interactions

1. **First record for a stream:** Sink has no handle; `key_name` is computed (timestamp at that time; if chunking, chunk_index 0); handle is opened; record is written; if chunking, `_records_written_in_current_file` = 1.
2. **Subsequent records (chunking off):** Same key and handle; write; no counter.
3. **Subsequent records (chunking on):** Before write, if `_records_written_in_current_file >= max_records_per_file`: close handle, set `_gcs_write_handle = None`, clear `_key_name`, increment `_chunk_index`, set `_records_written_in_current_file = 0`. Then write (which may open new handle and recompute key); increment `_records_written_in_current_file`.
4. **Sink close/drain:** Existing behaviour; any open handle is closed. Last chunk may have fewer than `max_records_per_file` records.

---

## Design Patterns and Principles

- **Single responsibility:** Rotation logic lives in the sink; config schema in the target.
- **Backward compatibility:** Chunking is opt-in via config; default (0 or absent) preserves current one-file-per-stream behaviour.
- **Key lifecycle:** When chunking is disabled, key is computed once and cached (current behaviour). When chunking is enabled, key is cleared on rotation so the next read recomputes with current time and new chunk index; format map includes `chunk_index` so convention can use `{chunk_index}`.
- **Dependency injection:** For testability, time used in key generation should be injectable (e.g. optional `time_fn` or passed clock). See [implementation.md](implementation.md) and [testing.md](testing.md).

---

## References

- Current sink/key/handle behaviour: `loaders/target-gcs/gcs_target/sinks.py`.
- Config schema: `loaders/target-gcs/gcs_target/target.py`.
- Patterns: `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` (config schema, sink options, black-box tests).
