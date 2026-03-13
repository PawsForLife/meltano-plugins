# Selected Solution: target-gcs-dedup-split-logic

Implementer guide: what to extract, where it lives, and in what order. Behaviour and tests must remain unchanged.

---

## 1. Helpers / partition_path.py

- **Constant:** Keep `DEFAULT_PARTITION_DATE_FORMAT` only here. No code change in this file.
- **Exports:** Ensure `helpers/__init__.py` exports it if anything besides sinks needs it; sinks will import from `.helpers` or `.helpers.partition_path`.

---

## 2. Sinks.py – imports

- Remove local definition of `DEFAULT_PARTITION_DATE_FORMAT`.
- Add to imports from helpers: `DEFAULT_PARTITION_DATE_FORMAT` (from `partition_path` or from `.helpers`).

---

## 3. Sinks.py – new private methods (order of implementation)

### 3.1 `_flush_and_close_handle(self) -> None`

- **Does:** If `self._gcs_write_handle` is not None: flush (if hasattr), close, set `self._gcs_write_handle = None`.
- **Then refactor:** In `_rotate_to_new_chunk()`, call `_flush_and_close_handle()` then do key/chunk/records/timestamp reset. In `_close_handle_and_clear_state()`, call `_flush_and_close_handle()` then clear `_key_name` and `_current_timestamp`.

### 3.2 `_apply_key_prefix_and_normalize(self, base: str) -> str`

- **Does:** `prefix = self.config.get("key_prefix", "") or ""`; return `f"{prefix}/{base}".replace("//", "/").lstrip("/")`.
- **Then refactor:** In `_build_key_for_record()`, replace the prefixed/normalize lines with a call to this. In `key_name` (or in `_compute_non_hive_key()` once extracted), use this for the final key string.

### 3.3 `_write_record_as_jsonl(self, record: dict) -> None`

- **Does:** `self.gcs_write_handle.write(orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE, default=_json_default))`.
- **Then refactor:** In `_process_record_single_or_chunked()` and `_process_record_hive_partitioned()`, replace the orjson.dumps + write block with `self._write_record_as_jsonl(record)`.

### 3.4 `_maybe_rotate_if_at_limit(self) -> None`

- **Does:** `max_records = self.config.get("max_records_per_file", 0)`; if `max_records and max_records > 0 and self._records_written_in_current_file >= max_records`: call `self._rotate_to_new_chunk()`.
- **Then refactor:** In both record-processing methods, replace the “if at limit then rotate” block with `self._maybe_rotate_if_at_limit()`.

### 3.5 `_compute_non_hive_key(self) -> str`

- **Does:** The current “else” branch of `key_name`: get effective template, timestamp, run date, format_map (stream, date, timestamp, format, optional chunk_index), build base key, apply `_apply_key_prefix_and_normalize(base)`, assign to `self._key_name`, return `self._key_name`.
- **Then refactor:** In `key_name`, when not hive: if not `self._key_name`, call `self._compute_non_hive_key()`; return `self._key_name`.

### 3.6 `_init_hive_partitioning(self) -> None`

- **Does:** Set `self._current_partition_path = None`. Get `x_partition_fields = self.schema.get("x-partition-fields")`. If `isinstance(..., list) and len(...) > 0`, call `validate_partition_fields_schema(self.stream_name, self.schema, x_partition_fields)`.
- **Then refactor:** In `__init__`, replace the “if hive_partitioned” block with `self._init_hive_partitioning()`.

---

## 4. Helpers / partition_schema.py

- **Add:** `_assert_field_required_and_non_null_type(stream_name: str, field_name: str, schema: dict) -> None`. It must:
  - Ensure `schema["required"]` is a list; else ValueError.
  - Ensure `field_name` in `schema.get("properties") or {}`; else ValueError.
  - Ensure `field_name` in required; else ValueError.
  - Get `prop_schema = properties[field_name]`, `raw_type = prop_schema.get("type")`; if None, ValueError.
  - Build `types` (single or list), `non_null = [t for t in types if t != "null"]`; if not non_null, ValueError.
- **Refactor:** In `validate_partition_fields_schema()`, for each field call `_assert_field_required_and_non_null_type(stream_name, field, schema)`. In `validate_partition_date_field_schema()`, call it for `field_name`, then add the existing date-parseable check (string in non_null, etc.).

---

## 5. Testing

- **Regression:** Run full target-gcs test suite; all existing tests must pass.
- **New tests:** Add unit tests only where new surface needs coverage (e.g. `_apply_key_prefix_and_normalize` edge cases, `_assert_field_required_and_non_null_type`). Prefer testing via existing sink/validator tests; add direct unit tests only for new helpers that are not fully covered by existing black-box tests.

---

## 6. Implementation order (suggested)

1. Constant: remove from sinks, import from helpers.
2. `_flush_and_close_handle`; refactor rotate and close_state.
3. `_apply_key_prefix_and_normalize`; refactor _build_key_for_record and key_name path.
4. `_write_record_as_jsonl`; refactor both process_record methods.
5. `_maybe_rotate_if_at_limit`; refactor both process_record methods.
6. `_compute_non_hive_key`; refactor key_name.
7. `_init_hive_partitioning`; refactor __init__.
8. `_assert_field_required_and_non_null_type`; refactor both validators in partition_schema.py.

This order avoids breaking call sites: constant and small helpers first, then key/handle behaviour, then init.
