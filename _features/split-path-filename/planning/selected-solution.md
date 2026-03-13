# Selected Solution — split-path-filename

## Summary

**Internal solution** using `str.format()` with path and filename constants. No external libraries. Path and filename are split in `constants.py`; `BasePathPattern` provides `filename_for_current_file()` and `full_key(path, filename)`; each pattern builds path from constants and composes the final key.

---

## Constants (`target_gcs/constants.py`)

```python
PATH_SIMPLE = "{stream}/{date}"
PATH_DATED = "{stream}/{hive_path}"
PATH_PARTITIONED = "{stream}/{hive_path}"
FILENAME_TEMPLATE = "{timestamp}.jsonl"
DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"  # unchanged
```

Remove: `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`.

---

## BasePathPattern Changes

### Add

- `filename_for_current_file() -> str`: Returns `FILENAME_TEMPLATE.format(timestamp=round(time_fn()))`. Timestamp is refreshed on each call (or cached per chunk; on rotate, next call gets new timestamp).
- `full_key(path: str, filename: str) -> str`: Joins `path` and `filename`, applies `apply_key_prefix_and_normalize(path + "/" + filename)`.

### Remove

- `key_template` (abstract property).
- `get_chunk_format_map()`.
- `_chunk_index`; all references to `chunk_index` in rotation and format maps.

### Chunking

- `maybe_rotate_if_at_limit()`: On rotate, call `flush_and_close_handle()`, reset `_records_written_in_current_file`, clear `_current_timestamp` (or rely on next `filename_for_current_file()` to refresh). Do **not** increment `_chunk_index`.

---

## SimplePath

- **Path:** At init, `path = PATH_SIMPLE.format(stream=stream_name, date=_extraction_date.strftime(date_format))`. Store as instance attribute.
- **process_record:** `maybe_rotate_if_at_limit()`; `filename = filename_for_current_file()`; `key = full_key(self._path, filename)`; open handle if needed; write record.

---

## DatedPath

- **Path:** At init, `hive_path = _extraction_date.strftime(DEFAULT_PARTITION_DATE_FORMAT)`; `path = PATH_DATED.format(stream=stream_name, hive_path=hive_path)`. Store as instance attribute.
- **process_record:** Same flow as SimplePath.

---

## PartitionedPath

- **Path per record:** `path_for_record(record) -> str`: `hive_path = self.hive_path(record)`; return `PATH_PARTITIONED.format(stream=stream_name, hive_path=hive_path)`.
- **Partition change:** Compare `path_for_record(record)` with `_current_partition_path`; on change, `flush_and_close_handle()`, set `_current_partition_path`, reset `_records_written_in_current_file`.
- **process_record:** Resolve partition path; handle partition change; `maybe_rotate_if_at_limit()`; `filename = filename_for_current_file()`; `key = full_key(path_for_record(record), filename)`; open handle if needed; write record.

---

## get_partition_path_from_schema_and_record

- **DatedPath:** Does not use it; uses extraction date directly.
- **PartitionedPath:** Feature spec: use `hive_path(record)` for path. Partition change = compare `hive_path(record)` outputs. `get_partition_path_from_schema_and_record` can be removed from PartitionedPath. The `_partitioned` module provides `get_hive_path_generator` and `hive_path(record)`; ensure output matches Hive format (field=value, date as year/month/day).
- **Pre-existing bug:** `_partitioned.string_functions.date_as_partition` does not return a value; it must `return date_value.strftime(...)` for `hive_path(record)` to work. Fix during implementation.

---

## Config and Docs

- Remove `key_naming_convention` from `target.py` config_jsonschema, `meltano.yml`, README.
- Remove `date_format` from key-building flow if no longer used. SimplePath uses `{date}`; `date_format` may still be needed for `PATH_SIMPLE.format(date=...)`. Keep `date_format` in config for SimplePath `{date}` token.

---

## Implementation Order (from feature file)

1. Update constants.
2. Remove key_naming_convention from config and path patterns.
3. Add `filename_for_current_file`, `full_key` to BasePathPattern; remove `get_chunk_format_map`.
4. Remove `_chunk_index`; chunking uses timestamp only.
5. SimplePath: path at init from constants.
6. DatedPath: path at init from constants.
7. PartitionedPath: path_for_record from constants; use hive_path(record).
8. Update tests and README.
