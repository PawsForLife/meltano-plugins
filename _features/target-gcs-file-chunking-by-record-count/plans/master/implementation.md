# Implementation Plan — Implementation: File Chunking by Record Count

**Feature:** target-gcs-file-chunking-by-record-count

---

## Implementation Order

Follow TDD: add or extend tests first, then implement. Models and config schema (interfaces) are defined before rotation logic. Time source for key generation is made injectable so tests can assert key/timestamp behaviour without flakiness.

---

## Step-by-Step Sequence

### 1. Config schema (target)

**File:** `loaders/target-gcs/gcs_target/target.py`

- Add to `config_jsonschema`: `th.Property("max_records_per_file", th.IntegerType, required=False, description="Maximum records per GCS object; 0 or unset = no chunking.")`.
- No other changes to the target class.

---

### 2. Sink state and time injection (sinks)

**File:** `loaders/target-gcs/gcs_target/sinks.py`

- In `GCSSink.__init__`: initialize `self._records_written_in_current_file: int = 0` and `self._chunk_index: int = 0`.
- Add optional dependency for time: e.g. accept an optional `time_fn` (e.g. `time.time`) on the target or sink, or use a module-level default and allow tests to patch `time.time`. Preferred: pass `time_fn` from target config or sink constructor (e.g. `getattr(target, "_time_fn", time.time)`) so tests can inject a fixed or controllable time without patching. Document in [interfaces.md](interfaces.md) and [testing.md](testing.md).
- If the project prefers minimal API change, use `time.time` in code and have tests patch `gcs_target.sinks.time` for deterministic keys; then no new constructor parameter.

---

### 3. Key computation with chunk_index (sinks)

**File:** `loaders/target-gcs/gcs_target/sinks.py`

- In `key_name` property: obtain `max_records = self.config.get("max_records_per_file", 0)`. When computing a new key (when `_key_name` is empty), build format_map with `stream`, `date`, `timestamp`. If `max_records` and `max_records > 0`, add `chunk_index=self._chunk_index` to the format_map so that `key_naming_convention` may use `{chunk_index}`. Use current time (via `time.time()` or injected `time_fn`) for `timestamp` when building the key.
- When chunking is disabled, do not add `chunk_index` to format_map (existing behaviour); existing conventions without `{chunk_index}` continue to work.

---

### 4. Rotation and process_record (sinks)

**File:** `loaders/target-gcs/gcs_target/sinks.py`

- At the start of `process_record`: if `max_records_per_file > 0` and `_records_written_in_current_file >= max_records_per_file`, run rotation:
  - If `_gcs_write_handle` is not None: flush (if the handle supports it), close it, set `_gcs_write_handle = None`.
  - Set `_key_name = ""`.
  - Increment `_chunk_index`.
  - Set `_records_written_in_current_file = 0`.
- Then write the record to `gcs_write_handle` (same as today).
- After the write: if `max_records_per_file > 0`, increment `_records_written_in_current_file`.

---

### 5. Handle flush on close

Ensure that when the handle is closed during rotation, any buffered data is flushed. The current code uses `smart_open.open(..., "wb", ...)`. Check whether the returned handle requires an explicit `flush()` before `close()`; if so, call flush before close in the rotation block.

---

## Files to Create or Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/gcs_target/target.py` | Add `max_records_per_file` to `config_jsonschema`. |
| `loaders/target-gcs/gcs_target/sinks.py` | Add state (`_records_written_in_current_file`, `_chunk_index`); extend `key_name` with chunk_index and time at build; add rotation and counter update in `process_record`. |
| `loaders/target-gcs/tests/test_sinks.py` | New tests (see [testing.md](testing.md)). |
| `loaders/target-gcs/sample.config.json` | Optionally add `max_records_per_file` example. |
| `loaders/target-gcs/meltano.yml` | Add setting for `max_records_per_file` if loader config is documented there. |
| `loaders/target-gcs/README.md` | Document new setting and key tokens (see [documentation.md](documentation.md)). |

---

## Code Organization

- All rotation and chunking logic stays inside `GCSSink` in `sinks.py`. No new modules.
- Optional: extract a small helper `_rotate_to_new_chunk(self) -> None` that performs close, clear key, increment chunk index, reset count; keeps `process_record` readable.

---

## Dependency Injection

- **Time:** Use injectable time (constructor param or target attribute) for key timestamp so tests can assert key content. If not added, tests patch `time.time` for deterministic keys.
- **GCS client:** Remain as today (instantiated in property); tests continue to patch `Client` and `smart_open.open` as in existing sink tests.
