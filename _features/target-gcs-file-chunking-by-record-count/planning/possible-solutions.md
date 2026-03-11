# Possible Solutions — File Chunking by Record Count

**Feature:** target-gcs-file-chunking-by-record-count

---

## Summary

Record-count-based file rotation for a Singer target is sink-internal logic: count records, close the current handle when a threshold is reached, open a new one with a new key. No standard library or GCS SDK provides this as a drop-in. Options are: (1) implement inside `GCSSink` (recommended), or (2) use a third-party writer that supports rotation (none found that match Singer/RecordSink semantics). An internal solution is selected.

---

## Option A: Internal implementation in GCSSink

**Description:** Add a record counter and rotation logic inside `GCSSink`. When `max_records_per_file` is set, after each write increment the counter; when it reaches the limit, close the handle, clear cached key, increment chunk index, reset counter; next write opens a new handle with a newly computed key (current timestamp + chunk index).

**Pros:**

- Full control over when rotation happens and key format.
- No new dependencies; fits existing Singer SDK `RecordSink` and config pattern.
- Same process, same config file; no orchestration changes.
- Easy to test with mocks (handle open/close, key content).

**Cons:**

- Logic and tests must be maintained in this repo.

**Verdict:** Recommended. Matches the feature spec and existing architecture.

---

## Option B: External “chunked” or “rotating” writer libraries

**Description:** Use a library that writes to GCS (or a generic IO) and rotates output after N records or N bytes.

**Research:**

- **gs-chunked-io:** Streams for Google Storage; chunking is by byte size, not record count. Not a fit.
- **dlt (data load tool):** Supports GCS and JSONL but is a different pipeline model (no Singer stdin/stdout, no RecordSink). Would require replacing the target’s I/O model.
- **jsonl-resumable:** Resumable reads and indexing for JSONL; does not provide “write N records then rotate to new file” for GCS.
- **Google Cloud examples (e.g. chunked_transfer):** Byte-oriented chunked transfer, not record-count rotation.

**Pros:**

- Theoretically less custom code if a matching library existed.

**Cons:**

- No library found that (a) rotates by record count and (b) integrates with Singer targets / RecordSink / config file. Would require a different target design (e.g. batch writer) and possibly different process boundaries.

**Verdict:** Not chosen; no suitable drop-in.

---

## Option C: Switch to BatchSink and batch-level “files”

**Description:** Use the SDK’s `BatchSink` so the target receives batches; treat each batch as a “chunk” and write one GCS object per batch (or aggregate batches up to N records).

**Pros:**

- Uses SDK batching abstractions.

**Cons:**

- Batch sizes are determined by the tap/target framework, not strictly by “max records per file.” Achieving a fixed record count per file would require buffering and splitting batches.
- Larger refactor: different base class, different message flow (BATCH vs RECORD), and possible protocol/state implications.
- Overkill for “rotate after N records” which is a simple counter + close/reopen in the current RecordSink.

**Verdict:** Not chosen; internal record counting in `GCSSink` is simpler and matches the requirement.

---

## Recommendation

Implement chunking **inside `GCSSink`** (Option A): add `max_records_per_file` to config, a per-stream record counter and chunk index, and rotation logic in `process_record` that closes the handle and clears key state so the next write opens a new file with a key that includes current timestamp and (optionally) chunk index.
