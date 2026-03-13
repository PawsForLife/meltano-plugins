# Implementation — split-path-filename

## Implementation Order

TDD: write failing tests first, then implement. Order below reflects dependencies; tests for each step precede implementation.

---

## Step 1: Update Constants

**File:** `loaders/target-gcs/target_gcs/constants.py`

- Add: `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`.
- Remove: `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`.
- Keep: `DEFAULT_PARTITION_DATE_FORMAT`.

**File:** `loaders/target-gcs/target_gcs/paths/__init__.py`

- Remove exports of removed constants; add exports for new ones if used elsewhere.

---

## Step 2: Fix date_as_partition Bug

**File:** `loaders/target-gcs/target_gcs/paths/_partitioned/string_functions.py` (or equivalent)

- Ensure `date_as_partition(date_value, ...)` returns `date_value.strftime(...)`.
- Add/update test in `tests/unit/paths/_partitioned/` or `tests/unit/helpers/` as appropriate.

---

## Step 3: Remove key_naming_convention from Config

**File:** `loaders/target-gcs/target_gcs/target.py`

- Remove `key_naming_convention` from `config_jsonschema`.

**File:** `loaders/target-gcs/meltano.yml`

- Remove `key_naming_convention` from settings and config example.

---

## Step 4: BasePathPattern — Add Methods, Remove Chunk Index

**File:** `loaders/target-gcs/target_gcs/paths/base.py`

- Add `filename_for_current_file(self) -> str`: `return FILENAME_TEMPLATE.format(timestamp=round(time_fn()))`.
- Add `full_key(self, path: str, filename: str) -> str`: `return self.apply_key_prefix_and_normalize(f"{path}/{filename}")`.
- Remove `key_template` property (and all subclass implementations).
- Remove `get_chunk_format_map()`.
- Remove `_chunk_index`; in `maybe_rotate_if_at_limit()`, do not increment chunk index; only flush, close, reset `_records_written_in_current_file`; next `filename_for_current_file()` yields new timestamp.

**Tests first:** `tests/unit/paths/test_base.py` — `filename_for_current_file`, `full_key`, key_prefix, chunking via timestamp.

---

## Step 5: SimplePath

**File:** `loaders/target-gcs/target_gcs/paths/simple.py`

- At init: `date_fmt = config.get("date_format", "%Y-%m-%d")`; `date_str = _extraction_date.strftime(date_fmt)`; `_path = PATH_SIMPLE.format(stream=stream_name, date=date_str)`.
- In `process_record`: `maybe_rotate_if_at_limit()`; `filename = filename_for_current_file()`; `key = full_key(self._path, filename)`; open handle if needed; write record.
- Remove `key_template`, `_build_key`, `get_chunk_format_map` usage; remove import of `DEFAULT_KEY_NAMING_CONVENTION`.

**Tests first:** `tests/unit/paths/test_simple.py` — path from constants; filename = timestamp.jsonl.

---

## Step 6: DatedPath

**File:** `loaders/target-gcs/target_gcs/paths/dated.py`

- At init: `hive_path = _extraction_date.strftime(DEFAULT_PARTITION_DATE_FORMAT)`; `_path = PATH_DATED.format(stream=stream_name, hive_path=hive_path)`.
- In `process_record`: same flow as SimplePath.
- Remove `key_template`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE` import.

**Tests first:** `tests/unit/paths/test_dated.py` — path from constants; filename = timestamp.jsonl.

---

## Step 7: PartitionedPath

**File:** `loaders/target-gcs/target_gcs/paths/partitioned.py`

- Add `path_for_record(self, record) -> str`: `hive_path = self.hive_path(record)`; `return PATH_PARTITIONED.format(stream=stream_name, hive_path=hive_path)`.
- Partition change: compare `path_for_record(record)` with `_current_partition_path`; on change, `flush_and_close_handle()`, set `_current_partition_path`, reset `_records_written_in_current_file`.
- In `process_record`: resolve path via `path_for_record(record)`; handle partition change; `maybe_rotate_if_at_limit()`; `filename_for_current_file()`; `full_key(path, filename)`; open handle; write record.
- Remove `get_partition_path_from_schema_and_record` usage for key building; remove `key_template`, `record_path`; use `hive_path(record)` from `_partitioned`.

**Tests first:** `tests/unit/paths/test_partitioned.py` — path from `path_for_record`; `hive_path(record)`; partition change; chunking.

---

## Step 8: Sinks and Config Wiring

**File:** `loaders/target-gcs/target_gcs/sinks.py`

- Pattern constructors no longer receive or use `key_naming_convention`.
- Ensure `time_fn`, `date_fn`, `storage_client` passed to patterns unchanged.

**Tests:** `tests/unit/test_sinks.py` — remove `key_naming_convention` tests; assert key shape from constants.

---

## Step 9: Helpers Cleanup

**File:** `loaders/target-gcs/target_gcs/helpers/partition_path.py`

- If `get_partition_path_from_schema_and_record` is no longer used by PartitionedPath, consider removal or deprecation. DatedPath does not use it; PartitionedPath uses `hive_path(record)`.
- Verify `DEFAULT_PARTITION_DATE_FORMAT` import path (constants vs helpers) is consistent.

---

## Dependency Injection

- `time_fn` and `date_fn` remain injectable in `GCSSink` and path patterns for deterministic tests.
- No new injectables required.

---

## Files Modified (Summary)

| File | Changes |
|------|---------|
| `constants.py` | Add path/filename constants; remove key_naming_convention defaults |
| `paths/__init__.py` | Update exports |
| `paths/base.py` | Add `filename_for_current_file`, `full_key`; remove `key_template`, `get_chunk_format_map`, `_chunk_index` |
| `paths/simple.py` | Path from constants; use new methods; remove key_template |
| `paths/dated.py` | Path from constants; use new methods; remove key_template |
| `paths/partitioned.py` | `path_for_record`; use `hive_path(record)`; remove get_partition_path usage |
| `paths/_partitioned/string_functions.py` | Fix `date_as_partition` return |
| `target.py` | Remove key_naming_convention from config |
| `sinks.py` | No key_naming_convention passed to patterns |
| `meltano.yml` | Remove key_naming_convention |
| `helpers/partition_path.py` | Possibly remove or reduce `get_partition_path_from_schema_and_record` |
