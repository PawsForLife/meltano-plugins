# Implementation: target-gcs-dedup-split-logic

## Implementation Order

Execute in this order to avoid breaking call sites and to satisfy dependencies (see [interfaces.md](interfaces.md)):

1. **Constant:** Remove `DEFAULT_PARTITION_DATE_FORMAT` from `sinks.py`; import from `.helpers.partition_path` (or `.helpers` if exported there). Ensure `helpers/__init__.py` exports it if needed.
2. **`_flush_and_close_handle`:** Implement; refactor `_rotate_to_new_chunk` and `_close_handle_and_clear_state` to call it, then perform their own state updates.
3. **`_apply_key_prefix_and_normalize`:** Implement; refactor `_build_key_for_record` and (after step 6) `_compute_non_hive_key` to use it.
4. **`_write_record_as_jsonl`:** Implement; refactor `_process_record_single_or_chunked` and `_process_record_hive_partitioned` to call it instead of inline orjson.dumps + write.
5. **`_maybe_rotate_if_at_limit`:** Implement; refactor both record-processing methods to call it before writing.
6. **`_compute_non_hive_key`:** Implement (using `_apply_key_prefix_and_normalize`); refactor `key_name` so the non-hive branch calls it when `_key_name` is not set, then returns `_key_name`.
7. **`_init_hive_partitioning`:** Implement; refactor `__init__` so the hive branch only calls `self._init_hive_partitioning()`.
8. **`_assert_field_required_and_non_null_type`:** Implement in `partition_schema.py`; refactor `validate_partition_fields_schema` (per field) and `validate_partition_date_field_schema` (single field, then date-parseable check) to use it.

## Files to Create or Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Remove local constant; add import; add six private methods; replace duplicated blocks and branches with calls to them. |
| `loaders/target-gcs/target_gcs/helpers/partition_path.py` | No code change; remains sole owner of constant. |
| `loaders/target-gcs/target_gcs/helpers/partition_schema.py` | Add `_assert_field_required_and_non_null_type`; refactor both public validators to call it. |
| `loaders/target-gcs/target_gcs/helpers/__init__.py` | Add `DEFAULT_PARTITION_DATE_FORMAT` to exports if anything other than sinks needs it from a single entry point; sinks may import from `partition_path` directly. |

## Code Organization

- New methods live on `GCSSink` in `sinks.py`; keep existing method order where sensible (e.g. handle-related, then key-related, then record-processing).
- `_assert_field_required_and_non_null_type` is module-private in `partition_schema.py` (leading underscore); not exported from `helpers/__init__.py`.

## Dependency Injection

No new DI. Existing `time_fn` and `date_fn` (and `storage_client`) remain; new methods use `self.config`, `self.gcs_write_handle`, and existing instance state only.

## Implementation Details (sinks.py)

- **`_flush_and_close_handle`:** Replicate current 4-line block: if handle exists, flush if hasattr, close, set to None.
- **`_apply_key_prefix_and_normalize`:** Handle empty prefix (avoid leading slash on bare base); `replace("//", "/").lstrip("/")` as today.
- **`_maybe_rotate_if_at_limit`:** Use `config.get("max_records_per_file", 0)`; treat 0 or missing as “no limit”; compare `_records_written_in_current_file >= max_records` when max_records > 0.
- **`_compute_non_hive_key`:** Move current `key_name` else-branch body (template, timestamp, date, format_map, base key, prefix+normalize, assign `_key_name`, return). Use `_apply_key_prefix_and_normalize` for the final key.
- **`_init_hive_partitioning`:** Set `_current_partition_path = None`; read `x_partition_fields`; if list and non-empty, call `validate_partition_fields_schema(self.stream_name, self.schema, x_partition_fields)`. Only call when `hive_partitioned` is true (caller responsibility).

## Implementation Details (partition_schema.py)

- **`_assert_field_required_and_non_null_type`:** Validate in order: (1) `schema["required"]` is a list else ValueError; (2) `field_name` in `schema.get("properties") or {}` else ValueError; (3) `field_name` in required else ValueError; (4) get property schema, `raw_type = prop_schema.get("type")`; if None, ValueError; (5) types = single or list, non_null = filter out "null"; if not non_null, ValueError. Reuse existing error message style (stream name, field name, reason).
