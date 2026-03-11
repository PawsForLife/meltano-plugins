# Implementation Plan — Interfaces: File Chunking by Record Count

**Feature:** target-gcs-file-chunking-by-record-count

---

## Public Interfaces Created or Modified

### 1. GCSTarget.config_jsonschema

**File:** `loaders/target-gcs/gcs_target/target.py`

**Change:** Add one optional property:

- `max_records_per_file` (integer, optional). Description: Maximum records per GCS object; when set and > 0, the sink rotates to a new file after this many records. When 0 or absent, chunking is disabled (one file per stream per run).

**Contract:** Schema remains a valid Singer SDK `th.PropertiesList`. Existing properties unchanged. Sink reads via `self.config.get("max_records_per_file", 0)`.

---

### 2. GCSSink — constructor and instance state

**File:** `loaders/target-gcs/gcs_target/sinks.py`

**Constructor:** `__init__(self, target, stream_name, schema, key_properties)` — unchanged signature. New instance attributes (private, implementation detail):

- `_records_written_in_current_file: int` — count of records written to the current open file. Initialized to 0.
- `_chunk_index: int` — 0-based index of the current chunk. Initialized to 0.

**Contract:** External callers do not depend on these; they are used only inside the sink.

---

### 3. GCSSink.key_name (property)

**Signature:** `@property def key_name(self) -> str`

**Behaviour:**

- **Chunking disabled** (`max_records_per_file` ≤ 0 or absent): Unchanged. If `_key_name` is set, return it. Else compute once with `stream`, `date`, `timestamp` (current time at first use), cache in `_key_name`, return. No `chunk_index` in format map.
- **Chunking enabled:** If `_key_name` is non-empty, return it. Else: compute key with `stream`, `date`, `timestamp` (current time at key build time), and `chunk_index` in the format map so that convention may use `{chunk_index}`; cache in `_key_name`; return. When rotation runs, `_key_name` is cleared so the next access recomputes.

**Contract:** Returned string is a valid GCS object key (no leading slash, key_prefix applied). When chunking is on, format_map includes `chunk_index` so that a convention like `{stream}/export_date={date}/{timestamp}_{chunk_index}.jsonl` works.

---

### 4. GCSSink.gcs_write_handle (property)

**Signature:** `@property def gcs_write_handle(self) -> FileIO` (or the actual type returned by `smart_open.open`)

**Behaviour:** If `_gcs_write_handle` is not None, return it. Else open with `smart_open.open("gs://{bucket}/{key_name}", "wb", ...)` (using current `key_name`), assign to `_gcs_write_handle`, return. After rotation, `_gcs_write_handle` is set to None so the next access opens a new handle with the new key.

**Contract:** Callers receive a writeable binary handle. Closing is the sink’s responsibility on rotation and on sink drain/close.

---

### 5. GCSSink.process_record

**Signature:** `def process_record(self, record: dict, context: dict) -> None`

**Behaviour:**

1. **If chunking enabled** (`max_records_per_file` > 0) **and** `_records_written_in_current_file >= max_records_per_file`: flush and close `_gcs_write_handle`, set `_gcs_write_handle = None`, clear `_key_name` (e.g. set to `""`), increment `_chunk_index`, set `_records_written_in_current_file = 0`.
2. Write the record to `gcs_write_handle` (which may open a new handle if needed).
3. If chunking enabled, increment `_records_written_in_current_file`.

**Contract:** Each record is written exactly once. Record count per file when chunking is ≤ `max_records_per_file`; last chunk may have fewer. No change to Singer RECORD message handling or schema.

---

## Data Models

No new Pydantic or dataclass models. Config is validated by the existing Singer SDK schema. Chunking state is two integers on the sink instance.

---

## Dependencies Between Interfaces

- Config schema (`max_records_per_file`) is read by the sink; no other component depends on it.
- Rotation clears `_key_name` and `_gcs_write_handle`; the next `key_name` access recomputes (and may use a time source); the next `gcs_write_handle` access opens a new handle using that key.
- For deterministic tests, the key computation should use an injectable time source where feasible; see [implementation.md](implementation.md) and [testing.md](testing.md).
