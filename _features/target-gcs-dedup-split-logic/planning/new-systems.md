# New Systems: target-gcs-dedup-split-logic

New or moved shared functions and split branches. All under `loaders/target-gcs/target_gcs/`; no new packages.

---

## 1. New shared helpers (where they will live)

### 1.1 Sink-internal helpers (private methods on `GCSSink` in `sinks.py`)

- **`_flush_and_close_handle()`**  
  - **Purpose:** Flush (if supported) and close `_gcs_write_handle`, set to `None`.  
  - **Used by:** `_rotate_to_new_chunk()`, `_close_handle_and_clear_state()`.  
  - **Location:** `target_gcs/sinks.py` (new private method on `GCSSink`).

- **`_apply_key_prefix_and_normalize(base: str) -> str`**  
  - **Purpose:** Return `f"{key_prefix}/{base}".replace("//", "/").lstrip("/")` using `self.config.get("key_prefix", "")`.  
  - **Used by:** `_build_key_for_record()`, `key_name` (via `_compute_non_hive_key()`).  
  - **Location:** `target_gcs/sinks.py`.

- **`_write_record_as_jsonl(record: dict) -> None`**  
  - **Purpose:** Serialize record with `orjson.dumps(..., default=_json_default)` and write to `self.gcs_write_handle`.  
  - **Used by:** `_process_record_single_or_chunked()`, `_process_record_hive_partitioned()`.  
  - **Location:** `target_gcs/sinks.py`.

- **`_maybe_rotate_if_at_limit() -> None`**  
  - **Purpose:** If `max_records_per_file` is set and `_records_written_in_current_file >= max_records`, call `_rotate_to_new_chunk()`.  
  - **Used by:** Both record-processing methods.  
  - **Location:** `target_gcs/sinks.py`.

### 1.2 Constant (single source of truth)

- **`DEFAULT_PARTITION_DATE_FORMAT`**  
  - **Location:** Keep only in `target_gcs/helpers/partition_path.py`; remove from `sinks.py` and import from helpers (e.g. `from .helpers.partition_path import ... get_partition_path_from_schema_and_record, DEFAULT_PARTITION_DATE_FORMAT`).  
  - **Expose:** Re-export from `helpers/__init__.py` if other code needs it; sinks already import from `.helpers`.

### 1.3 Partition schema helper (shared validation)

- **New in `target_gcs/helpers/partition_schema.py`:**  
  - **`_assert_field_required_and_non_null_type(stream_name: str, field_name: str, schema: dict) -> None`**  
  - **Purpose:** Raise `ValueError` if `field_name` not in `schema["properties"]`, not in `schema["required"]`, or has no non-null type (same types/non_null logic as today).  
  - **Used by:** `validate_partition_fields_schema()` (per field) and `validate_partition_date_field_schema()` (single field).  
  - **Location:** `target_gcs/helpers/partition_schema.py` (private module-level or same file).

---

## 2. Split branch logic (new named functions)

### 2.1 Non-hive key computation

- **`_compute_non_hive_key() -> str`**  
  - **Purpose:** Contains the current “else” branch of `key_name`: compute effective template, timestamp, date, format_map, apply prefix/normalize, return key. Sets `self._key_name` and returns it (or keep as property that delegates to this for the compute path).  
  - **Location:** `target_gcs/sinks.py` (private method).  
  - **Caller:** `key_name` property: if hive return `_key_name`, else return `_compute_non_hive_key()` (and cache in `_key_name` as today).

### 2.2 Hive init

- **`_init_hive_partitioning() -> None`**  
  - **Purpose:** Contains the current “if hive_partitioned” block from `__init__`: set `_current_partition_path = None`, read `x_partition_fields`, if non-empty call `validate_partition_fields_schema(...)`.  
  - **Location:** `target_gcs/sinks.py` (private method).  
  - **Caller:** `GCSSink.__init__`: if `config.get("hive_partitioned")` then call `_init_hive_partitioning()`.

---

## 3. No new files

- All new functions live in existing modules: `sinks.py`, `helpers/partition_path.py` (constant only), `helpers/partition_schema.py`.  
- Helpers `__init__.py`: add `DEFAULT_PARTITION_DATE_FORMAT` to exports only if we want a single public import point; sinks can import from `partition_path` directly.

---

## 4. Summary

| New / changed item                         | Module                    | Type        |
|-------------------------------------------|---------------------------|------------|
| `_flush_and_close_handle`                  | `sinks.py`                | New method |
| `_apply_key_prefix_and_normalize`          | `sinks.py`                | New method |
| `_write_record_as_jsonl`                   | `sinks.py`                | New method |
| `_maybe_rotate_if_at_limit`                | `sinks.py`                | New method |
| `_compute_non_hive_key`                    | `sinks.py`                | New method |
| `_init_hive_partitioning`                  | `sinks.py`                | New method |
| `DEFAULT_PARTITION_DATE_FORMAT`           | `partition_path.py` only  | Remove from sinks, import |
| `_assert_field_required_and_non_null_type`| `partition_schema.py`     | New helper |
