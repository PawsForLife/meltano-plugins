# Interfaces: target-gcs-dedup-split-logic

## Public Interfaces (unchanged)

- **GCSTarget:** Config schema, `get_sink`, `_add_sink_with_client` — no signature or behaviour change.
- **GCSSink:** Constructor `(target, stream_name, schema, key_properties, *, time_fn=None, date_fn=None, storage_client=None)`; properties `key_name`, `gcs_write_handle`; method `process_record(record, context)` — unchanged externally.
- **partition_path:** `get_partition_path_from_schema_and_record(schema, record, extraction_date, *, partition_date_format=DEFAULT_PARTITION_DATE_FORMAT) -> str` — unchanged. `DEFAULT_PARTITION_DATE_FORMAT` remains the single public constant (sinks import it).
- **partition_schema:** `validate_partition_fields_schema(stream_name, schema, partition_fields) -> None` and `validate_partition_date_field_schema(stream_name, field_name, schema) -> None` — same signatures and raised exceptions; implementation delegates to new internal helper.

## New Private Interfaces (GCSSink, sinks.py)

| Method | Signature | Behaviour |
|--------|-----------|-----------|
| `_flush_and_close_handle` | `(self) -> None` | If `_gcs_write_handle` is not None: flush (if hasattr), close, set `_gcs_write_handle = None`. |
| `_apply_key_prefix_and_normalize` | `(self, base: str) -> str` | `prefix = self.config.get("key_prefix", "") or ""`; return `f"{prefix}/{base}".replace("//", "/").lstrip("/")`. |
| `_write_record_as_jsonl` | `(self, record: dict) -> None` | Write `orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE, default=_json_default)` to `self.gcs_write_handle`. |
| `_maybe_rotate_if_at_limit` | `(self) -> None` | If `max_records_per_file` is set and > 0 and `_records_written_in_current_file >= max_records`, call `_rotate_to_new_chunk()`. |
| `_compute_non_hive_key` | `(self) -> str` | Compute effective template, timestamp, date, format_map (stream, date, timestamp, format, optional chunk_index), build base key, call `_apply_key_prefix_and_normalize(base)`, assign to `_key_name`, return `_key_name`. |
| `_init_hive_partitioning` | `(self) -> None` | Set `_current_partition_path = None`; get `x_partition_fields` from schema; if non-empty list, call `validate_partition_fields_schema(...)`. |

## New Private Interface (partition_schema.py)

| Function | Signature | Behaviour |
|----------|-----------|-----------|
| `_assert_field_required_and_non_null_type` | `(stream_name: str, field_name: str, schema: dict) -> None` | Raise `ValueError` if: `required` is not a list; `field_name` not in `schema["properties"]`; `field_name` not in `required`; property has no type; after resolving single/list type, no non-null type. Messages include stream_name and field_name. |

## Data Models

No new data models. Existing dict-based config and schema usage unchanged. Record remains `dict`; partition path remains `str`.

## Dependencies Between Interfaces

- `_rotate_to_new_chunk` and `_close_handle_and_clear_state` depend on `_flush_and_close_handle`.
- `_build_key_for_record` and `_compute_non_hive_key` depend on `_apply_key_prefix_and_normalize`.
- `_process_record_single_or_chunked` and `_process_record_hive_partitioned` depend on `_maybe_rotate_if_at_limit` and `_write_record_as_jsonl`.
- `key_name` (non-hive path) depends on `_compute_non_hive_key` (which uses `_apply_key_prefix_and_normalize`).
- `__init__` (hive path) depends on `_init_hive_partitioning`.
- `validate_partition_fields_schema` and `validate_partition_date_field_schema` depend on `_assert_field_required_and_non_null_type`.
- Sinks import `DEFAULT_PARTITION_DATE_FORMAT` from `target_gcs.helpers.partition_path` (or from `.helpers` if re-exported there).
