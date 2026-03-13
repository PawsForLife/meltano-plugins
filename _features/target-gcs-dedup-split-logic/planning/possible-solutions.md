# Possible Solutions: target-gcs-dedup-split-logic

Internal refactor only (no new external libraries). Options for unifying duplication and splitting switch logic.

---

## A. Unifying duplicated logic

### A1. Handle flush/close

- **Option 1 – Private method on GCSSink:** Add `_flush_and_close_handle()`; `_rotate_to_new_chunk()` and `_close_handle_and_clear_state()` call it, then do their own state updates (key/chunk/records vs key/timestamp).  
  - **Pros:** Single place for flush/close; clear ownership.  
  - **Cons:** None significant.  
- **Option 2 – Leave duplicated:** Keep the 4-line block in both places.  
  - **Pros:** No indirection.  
  - **Cons:** Future changes (e.g. error handling) must be done twice.

**Recommendation:** Option 1.

### A2. Key prefix + normalization

- **Option 1 – Private method:** `_apply_key_prefix_and_normalize(base: str) -> str` in `sinks.py`.  
  - **Pros:** One implementation; same behaviour for hive and non-hive keys.  
  - **Cons:** One extra method.  
- **Option 2 – Helper in helpers:** e.g. `helpers/key_utils.py` with `apply_key_prefix(prefix: str, base: str) -> str`.  
  - **Pros:** Reusable outside sink.  
  - **Cons:** Currently only sink uses it; adds a new module for one function.

**Recommendation:** Option 1 (sink-private method).

### A3. Record serialization + write

- **Option 1 – Private method:** `_write_record_as_jsonl(record)` on GCSSink.  
  - **Pros:** Single place for orjson options and default; easy to test via sink behaviour.  
  - **Cons:** None.  
- **Option 2 – Helper in helpers/json_parsing.py:** e.g. `serialize_record_to_jsonl(record) -> bytes` and caller does handle.write.  
  - **Pros:** Pure function.  
  - **Cons:** Two call sites still do write; duplication of “serialize + write” pattern remains unless sink wraps it.

**Recommendation:** Option 1 (sink method that does serialize + write).

### A4. Rotate-if-at-limit

- **Option 1 – Private method:** `_maybe_rotate_if_at_limit()` that checks config and count, then calls `_rotate_to_new_chunk()` if needed.  
  - **Pros:** Both record paths call same logic; no duplicated condition.  
  - **Cons:** None.  
- **Option 2 – Inline in both:** Keep as-is.  
  - **Cons:** Same 5-line block in two places.

**Recommendation:** Option 1.

### A5. `DEFAULT_PARTITION_DATE_FORMAT`

- **Option 1 – Single source in partition_path:** Define only in `helpers/partition_path.py`; sinks import from helpers.  
  - **Pros:** One constant; partition_path is the natural owner.  
  - **Cons:** Sinks depend on helpers (already do).  
- **Option 2 – Sinks-only constant:** Keep in sinks, partition_path takes it as default arg (already does).  
  - **Cons:** Constant lives in sink layer; partition_path docstring/default reference “year=%Y/...” in two places.

**Recommendation:** Option 1 (constant only in partition_path; sinks import).

### A6. Partition schema validation (properties / required / non-null)

- **Option 1 – Shared private helper:** `_assert_field_required_and_non_null_type(stream_name, field_name, schema)` in `partition_schema.py`; both validators call it, then add their specific checks (e.g. date-parseable).  
  - **Pros:** No duplicated “in properties, in required, non-null type” logic.  
  - **Cons:** Slightly more indirection.  
- **Option 2 – Leave duplicated:** Keep both validators self-contained.  
  - **Cons:** Same validation structure in two places.

**Recommendation:** Option 1.

---

## B. Splitting switch/branch logic

### B1. `key_name` property (hive vs non-hive)

- **Option 1 – Extract non-hive branch:** `_compute_non_hive_key() -> str` holds the current “else” block; `key_name` returns `_key_name` when hive, else (if not cached) calls `_compute_non_hive_key()`, caches, returns.  
  - **Pros:** Named function for non-hive path; property stays a thin dispatcher.  
  - **Cons:** None.  
- **Option 2 – Strategy object:** e.g. KeyComputer for hive vs non-hive.  
  - **Cons:** Overkill for two branches; more types and wiring.

**Recommendation:** Option 1.

### B2. `__init__` hive setup

- **Option 1 – Extract method:** `_init_hive_partitioning()`; `__init__` calls it when `config.get("hive_partitioned")`.  
  - **Pros:** Init branch is one line; hive logic named and testable.  
  - **Cons:** None.  
- **Option 2 – Leave in __init__:** Keep branch inline.  
  - **Cons:** Constructor does more; harder to test hive init in isolation.

**Recommendation:** Option 1.

### B3. `process_record` dispatcher

- **Current:** Already dispatches to `_process_record_hive_partitioned` and `_process_record_single_or_chunked`.  
- **Change:** No structural change; only use new shared helpers inside those two methods (write, maybe_rotate).

---

## C. Summary

| Area              | Chosen approach                                              |
|-------------------|--------------------------------------------------------------|
| Handle close      | One private method `_flush_and_close_handle()`                |
| Key prefix        | One private method `_apply_key_prefix_and_normalize(base)`   |
| Record write      | One private method `_write_record_as_jsonl(record)`          |
| Rotate at limit   | One private method `_maybe_rotate_if_at_limit()`             |
| Constant          | Single definition in `partition_path.py`; sinks import      |
| Schema validation | Shared helper `_assert_field_required_and_non_null_type`      |
| key_name          | Split non-hive into `_compute_non_hive_key()`                |
| __init__ hive     | Split into `_init_hive_partitioning()`                       |
