# Archive: target-gcs file chunking by record count

**Feature:** target-gcs-file-chunking-by-record-count  
**Plugin:** target-gcs (loaders/target-gcs)

---

## The request

The target-gcs loader writes Singer stream data to GCS as JSONL. Originally, one GCS object was written per stream per run, with a single key (using `{stream}`, `{date}`, `{timestamp}`). For large streams this produced very large files, which can be undesirable for downstream (e.g. BigQuery load limits, Spark parallelism).

The requirement was to add **file chunking by record count**: after a configurable number of records, close the current file and open a new one. Each new file must use a **current** timestamp (and optionally a chunk index) in the key so filenames are distinct. When the setting is unset or 0, behaviour must remain one file per stream per run (backward compatible).

Testing needs: unit tests for chunking off (one key/handle, no chunk_index), chunking on (rotation at threshold, key format with chunk_index, record integrity), and regression coverage so existing jobs without the config still produce one file per stream.

---

## Planned approach

**Solution:** Implement rotation entirely inside `GCSSink`. No new dependencies or BatchSink; use the existing Singer SDK `RecordSink` and `process_record` contract.

- **Config:** Add optional `max_records_per_file` (integer) to `GCSTarget.config_jsonschema` in `target.py`; 0 or absent = no chunking. Sink reads via `self.config.get("max_records_per_file", 0)`.
- **Sink state:** Add `_records_written_in_current_file` and `_chunk_index` on `GCSSink`; optional injectable time (`time_fn`) for deterministic key assertions in tests.
- **Key naming:** When chunking is enabled, include `chunk_index` in the key format map so conventions can use `{chunk_index}`; recompute key (with current time and chunk index) when `_key_name` is cleared after rotation. When chunking is disabled, keep existing single cached key and no chunk_index.
- **Rotation:** In `process_record`, before writing: if `max_records_per_file > 0` and `_records_written_in_current_file >= max_records_per_file`, close and release the handle (flush first when supported), clear `_key_name`, increment `_chunk_index`, reset record count. Then write the record and increment the count when chunking is on. The record that would exceed the limit is written to the new file.
- **Tests:** TDD in `test_sinks.py`: schema contract; chunking disabled (one key, one handle, no chunk_index); rotation at threshold, key format with chunk_index, record integrity. Black-box assertions on keys, open/close, and write payloads; time patched for deterministic keys.

Task sequence: (01) config schema and schema test; (02) tests for chunking disabled; (03) sink state and time injection; (04) tests for rotation and key format; (05) key computation with chunk_index; (06) rotation and process_record; (07) flush before close in rotation; (08) README, sample config, meltano.yml, inline docs.

---

## What was implemented

- **Config:** `max_records_per_file` added to `config_jsonschema` in `target.py` (optional integer; 0 or unset = no chunking). Schema and validation covered by tests in `test_sinks.py`.
- **Sink state and time:** `GCSSink` initializes `_records_written_in_current_file` and `_chunk_index`; optional `time_fn` constructor argument allows tests to inject a fixed time for deterministic key assertions. Key computation uses `self._time_fn or time.time`.
- **Key computation:** `key_name` property reads `max_records_per_file`; when chunking is enabled (`max_records > 0`), adds `chunk_index` to the format map so `key_naming_convention` can use `{chunk_index}`. When `_key_name` is empty, key is built with current timestamp (from `time_fn` or `time.time`) and chunk index when chunking is on.
- **Rotation:** `_rotate_to_new_chunk()` flushes the handle when it has a `flush` method, closes it, sets `_gcs_write_handle = None`, clears `_key_name`, increments `_chunk_index`, resets `_records_written_in_current_file`. In `process_record`, rotation runs before write when the count has reached the limit; then the record is written and the counter incremented when chunking is enabled. Record that would exceed the limit is written to the new file.
- **Tests:** Chunking disabled (one key and one handle; key without chunk_index); rotation at threshold (two keys/handles, record that triggers rotation in new file); key format with chunk_index; record integrity (25 records, 25 writes, no duplicate or dropped). All in `test_sinks.py` with docstrings stating WHAT and WHY; time patched for deterministic keys.
- **Documentation:** README documents `max_records_per_file`, `{chunk_index}` and refreshed `{timestamp}` when chunking is on, and chunking behaviour. `sinks.py` docstrings and comments describe rotation and new state. Sample config and meltano.yml include the new setting where applicable. CHANGELOG entry added with pointer to this archive.

Backward compatibility: when `max_records_per_file` is unset or 0, one file per stream per run is unchanged; no rotation and no chunk_index in the key.
