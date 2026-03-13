# Architecture: target-gcs-dedup-split-logic

## Design and Structure

Refactor is in-place within existing modules. No new packages or top-level components.

- **`target_gcs/sinks.py`:** Add six private methods on `GCSSink`; remove local `DEFAULT_PARTITION_DATE_FORMAT` and import from helpers. Call sites (rotate, close_state, _build_key_for_record, key_name, both process_record paths) delegate to the new methods.
- **`target_gcs/helpers/partition_path.py`:** Sole owner of `DEFAULT_PARTITION_DATE_FORMAT`; no structural change.
- **`target_gcs/helpers/partition_schema.py`:** Add one private helper `_assert_field_required_and_non_null_type`; refactor `validate_partition_fields_schema` and `validate_partition_date_field_schema` to call it, then perform their specific checks (e.g. date-parseable).

## Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **GCSSink** | Owns all new private methods; `key_name` and `__init__` become thin dispatchers to `_compute_non_hive_key` and `_init_hive_partitioning`; record paths call `_write_record_as_jsonl`, `_maybe_rotate_if_at_limit`, and (where applicable) `_flush_and_close_handle`, `_apply_key_prefix_and_normalize`. |
| **partition_path** | Single definition of `DEFAULT_PARTITION_DATE_FORMAT`; `get_partition_path_from_schema_and_record` unchanged. |
| **partition_schema** | `_assert_field_required_and_non_null_type` encapsulates “in properties, in required, non-null type”; public validators delegate to it then add field-specific logic. |

## Data Flow

Unchanged at process level: stdin → Target → sink per stream → GCS. Internal flow:

- **Handle lifecycle:** `_rotate_to_new_chunk` and `_close_handle_and_clear_state` both call `_flush_and_close_handle()` then perform their own state updates (key/chunk/records vs key/timestamp).
- **Key building:** `_build_key_for_record` and (via `_compute_non_hive_key`) `key_name` use `_apply_key_prefix_and_normalize(base)` for the final key string.
- **Record write:** Both `_process_record_single_or_chunked` and `_process_record_hive_partitioned` call `_maybe_rotate_if_at_limit()` then `_write_record_as_jsonl(record)`.
- **Init:** `__init__` branches once on `hive_partitioned` and calls `_init_hive_partitioning()` which sets partition state and runs schema validation.

## Design Patterns

- **Extract method:** Duplicated blocks become single private methods; callers are simplified.
- **Single responsibility:** Each new method does one thing (flush/close, prefix+normalize, write JSONL, maybe rotate, compute non-hive key, init hive).
- **Thin dispatcher:** `key_name` and hive branch in `__init__` only decide which path to call; logic lives in named functions.
- **Single source of truth:** Constant lives in `partition_path`; schema “required + non-null” lives in `_assert_field_required_and_non_null_type`.

Patterns align with `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` (DI for time/date, validation via schema, no new globals).
