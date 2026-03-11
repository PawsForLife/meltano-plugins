# Implementation Plan — Overview: File Chunking by Record Count

**Feature:** target-gcs-file-chunking-by-record-count  
**Plan location:** `_features/target-gcs-file-chunking-by-record-count/plans/master/`

---

## Purpose

Add optional **record-count-based file chunking** to target-gcs so that after a configurable number of records per GCS object, the sink closes the current file and opens a new one. Each new file uses a current timestamp and chunk index in the key so keys remain distinct. When the setting is unset or 0, behaviour is unchanged (one file per stream per run).

---

## Objectives and Success Criteria

- **Config:** Optional `max_records_per_file` (integer); 0 or absent = no chunking.
- **Rotation:** When records written to the current file reach the limit, close handle, clear key cache, increment chunk index, open new handle on next write; the record that would have exceeded the limit is written to the new file.
- **Key uniqueness:** New key uses current time and `{chunk_index}` when chunking is enabled so multiple chunks in the same second do not collide.
- **Backward compatibility:** No rotation when `max_records_per_file` is unset or 0; one file per stream, single timestamp per stream.

---

## Key Requirements and Constraints

- Changes are confined to the target-gcs loader (`loaders/target-gcs/`); no Singer protocol or tap changes.
- Use existing Singer SDK `RecordSink` and `process_record` contract; chunking is internal to `GCSSink`.
- No new external dependencies; use existing `smart_open`, `google.cloud.storage`, `orjson`.
- Time used for key generation must be injectable or testable so tests can assert key/timestamp behaviour without flakiness (per development_practices: non-deterministic systems passed as parameters where practical).

---

## Relationship to Existing Systems

- **GCSSink** (`gcs_target/sinks.py`): Extended with optional record counter, chunk index, rotation logic, and key recomputation when chunking is enabled. Existing `key_name`, `gcs_write_handle`, and `process_record` remain the public surface; behaviour is extended, not replaced.
- **GCSTarget** (`gcs_target/target.py`): Config schema gains one optional property `max_records_per_file`. No change to sink binding or message handling.
- **Config/sample/README:** New setting documented; sample config may show the option; Meltano settings updated if the project documents loader config in `meltano.yml`.

See [architecture.md](architecture.md), [interfaces.md](interfaces.md), and [implementation.md](implementation.md) for structure, contracts, and implementation order.
