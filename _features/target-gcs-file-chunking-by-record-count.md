# Feature request: File chunking by record count (target-gcs)

**Plugin:** target-gcs (loaders/target-gcs)
**Variant:** PawsForLife/meltano-plugins (Pet Circle); aligns with Datateer/target-gcs structure
**Status:** Request

---

## Background

The project uses **target-gcs** from PawsForLife/meltano-plugins to write Singer stream data to GCS as JSONL. In the current implementation (`target_gcs/sinks.py`), `GCSSink` extends `RecordSink`, opens a single GCS write handle per stream, and computes the object key once (using `{stream}`, `{date}`, `{timestamp}`). All records for that stream in a run are written to one object. The `timestamp` in the key is fixed at the time the key is first computed (start of writing that stream).

For large streams, a single very large file can be undesirable for downstream (e.g. BigQuery load limits, Spark parallelism, or operational preference for smaller files). The requirement is to **chunk** output so that after a configurable number of records have been written to a file, the target closes that file and opens a new one, using the **current** time (and optionally a chunk index) for the new key so that filenames are distinct and reflect when each chunk was created.

---

## This Task

Add support for **file chunking by record count** so that:

1. **Config:** A new optional setting (e.g. `max_records_per_file` or `chunk_size`) specifies the maximum number of records to write to a single GCS object. When the count is reached, the current file is closed and a new file is opened.

2. **Key per chunk:** The object key for each new file must use a **current** timestamp (and optionally a chunk index) at the time the new chunk is started, not the run start time. So the key naming convention continues to support `{timestamp}` (and optionally `{chunk_index}` if added), where `timestamp` is refreshed when rotating to a new file.

3. **Behaviour:** The sink maintains a record counter per stream. When writing a record would exceed `max_records_per_file`, the sink flushes and closes the current handle, clears or updates the key state so the next key uses the new timestamp (and chunk index if applicable), opens a new GCS handle, then writes the record. Remaining records in the run continue into the new file until the count is reached again.

4. **Backward compatibility:** When `max_records_per_file` is not set (or is 0/disabled), behaviour remains as today: one file per stream per run, single timestamp.

---

## Proposed direction (research summary)

- **Schema:** Add `max_records_per_file` (optional integer; 0 or unset = no chunking). Optionally add `chunk_index` or similar to the key tokens so keys are `{stream}/{date}/{timestamp}_part{N}.jsonl` or `{stream}/{date}/{timestamp}.jsonl` with timestamp updated per chunk.
- **Sink state:** The sink currently caches `_key_name` and opens `gcs_write_handle` once. For chunking: (1) add a record counter; (2) in `process_record`, after writing, increment the counter; (3) if counter >= `max_records_per_file`, close the handle, set `_gcs_write_handle = None`, clear `_key_name` (so the next access to `key_name` recomputes with `time.time()` and optionally increment chunk index), then on next write a new handle is opened via `gcs_write_handle`.
- **Key uniqueness:** Using `round(time.time())` at chunk rotation may collide if two chunks start in the same second. Options: (a) include chunk index in the key (e.g. `{timestamp}_{chunk_index}.jsonl`), or (b) use a more precise timestamp (e.g. microseconds), or (c) both. Recommendation: include chunk index in the key convention when chunking is enabled.
- **Meltano SDK:** The target uses `RecordSink`; batching does not create new files. Chunk rotation is entirely implemented inside the sink (count + close/reopen on threshold).

---

## Testing Needed

- **Unit:** With `max_records_per_file` set (e.g. 100), after 100 records the sink closes the current handle and opens a new one; the new key uses a timestamp (and chunk index if present) from the rotation time.
- **Unit:** With `max_records_per_file` unset or 0, exactly one file per stream is used (no rotation); behaviour matches current implementation.
- **Unit:** Record count resets (or chunk index increments) correctly across rotations; no record is lost or written twice.
- **Integration:** Run a tap → target-gcs pipeline with `max_records_per_file` set; confirm multiple objects per stream in GCS with distinct keys and correct record counts per object.
- **Regression:** Existing jobs without the new config produce a single file per stream as before.
