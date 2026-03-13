# Task Plan: 04 — BasePathPattern Add Methods, Remove Chunk Index

## Overview

This task refactors `BasePathPattern` to support the split path/filename model. It adds `filename_for_current_file()` and `full_key(path, filename)` for path patterns to compose keys, and removes `key_template`, `get_chunk_format_map`, and `_chunk_index`. Chunking uses timestamp-only filenames (no chunk index). Subclasses (SimplePath, DatedPath, PartitionedPath) are not updated in this task; they will be migrated in tasks 05–07. Subclass tests may fail until those tasks complete.

**Dependencies:** Task 01 (constants: `FILENAME_TEMPLATE` must exist), Task 03 (config: `key_naming_convention` removed).

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/paths/base.py` | Modify: add methods, remove properties/attributes, update rotation |
| `loaders/target-gcs/tests/unit/paths/test_base.py` | Modify: add new tests, remove obsolete tests, update `_MinimalPattern` |

---

## Test Strategy

**TDD:** Write failing tests first, then implement. Per `tests/unit/` mirroring source path; file `test_base.py` for `paths/base.py`.

### Tests to Add (in order)

1. **`test_filename_for_current_file_returns_timestamp_jsonl`** — With `time_fn=lambda: 12345`, assert `filename_for_current_file()` returns `"12345.jsonl"`. Validates core filename contract.
2. **`test_filename_for_current_file_uses_injected_time_fn`** — Deterministic `time_fn` yields predictable filename; asserts DI for deterministic tests.
3. **`test_full_key_joins_path_and_filename`** — `full_key("a/b", "c.jsonl")` returns normalized key (path + filename, prefix applied). Validates key composition.
4. **`test_full_key_applies_key_prefix`** — With `key_prefix="x/y"`, result starts with prefix. Validates prefix application.
5. **`test_maybe_rotate_resets_records_no_chunk_index`** — After rotate at `max_records_per_file`, next `filename_for_current_file()` has new timestamp; no `chunk_index` in key. Validates timestamp-only chunking.

### Tests to Remove

- `test_key_template_returns_user_template_when_set`
- `test_key_template_returns_hive_default_when_hive_partitioned_and_no_user_template`
- `test_key_template_returns_non_partition_default_when_neither_set`
- `test_key_template_empty_user_template_uses_default`
- `test_constants_match_expected_values` (tests removed constants)
- `test_get_chunk_format_map_returns_stream_date_timestamp_format`
- `test_get_chunk_format_map_includes_chunk_index_when_chunking_enabled`
- `test_get_chunk_format_map_omits_chunk_index_when_chunking_disabled`
- `test_chunk_index_in_key_template_produces_suffix_before_extension`
- `test_maybe_rotate_if_at_limit_at_limit_clears_handle_and_increments_chunk_index` (replaced by `test_maybe_rotate_resets_records_no_chunk_index`)

### Test Helper Updates

- **`_MinimalPattern`:** Remove `key_template` property. Keep `process_record` and `close` as no-ops. Subclass only needs to satisfy abstract `process_record` and `close`.
- **Imports:** Remove `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`. Add `FILENAME_TEMPLATE` from `target_gcs.constants` if needed for assertions.

---

## Implementation Order

1. **Tests first** — Add the five new tests; remove the ten obsolete tests; update `_MinimalPattern` and imports. Run pytest; new tests fail, removed tests gone.
2. **Add `filename_for_current_file`** — `return FILENAME_TEMPLATE.format(timestamp=round(time_fn()))`; use `self._time_fn or time.time`. Import `FILENAME_TEMPLATE` from `target_gcs.constants`.
3. **Add `full_key`** — `return self.apply_key_prefix_and_normalize(f"{path}/{filename}")`. Handle edge: ensure path and filename join correctly (e.g. path without trailing slash).
4. **Remove `key_template`** — Delete the abstract property from `BasePathPattern`. Subclasses still implement it until 05–07; base no longer requires it.
5. **Remove `get_chunk_format_map`** — Delete the method from `BasePathPattern`. Subclasses will fail when they call it until 05–07.
6. **Remove `_chunk_index`** — Delete from `__init__`; remove all references. In `maybe_rotate_if_at_limit`, remove `self._chunk_index += 1`; keep flush, close, reset `_records_written_in_current_file`, refresh `_current_timestamp` (optional; next `filename_for_current_file()` yields new timestamp anyway).
7. **Run tests** — `uv run pytest tests/unit/paths/test_base.py` from `loaders/target-gcs/`. Base tests pass. Subclass tests (test_simple, test_dated, test_partitioned) may fail; acceptable until 05–07.

---

## Validation Steps

1. **Base tests pass:** `cd loaders/target-gcs && uv run pytest tests/unit/paths/test_base.py -v`
2. **Ruff:** `uv run ruff check target_gcs/paths/base.py`
3. **MyPy:** `uv run mypy target_gcs/paths/base.py`
4. **Acceptance:** `filename_for_current_file()` and `full_key()` work per interface; `maybe_rotate_if_at_limit` uses timestamp-only; `key_template`, `get_chunk_format_map`, `_chunk_index` removed from base.

---

## Documentation Updates

- **None** for this task. AI context and README updates are in task 10. No new public API beyond what interfaces.md already documents.

---

## Notes

- **Subclass breakage:** Removing `get_chunk_format_map` and `key_template` from base will cause `SimplePath`, `DatedPath`, and `PartitionedPath` to fail when they call these. This is expected; tasks 05–07 will migrate subclasses to use `filename_for_current_file()` and `full_key()`.
- **`full_key` path/filename join:** Use `f"{path.rstrip('/')}/{filename.lstrip('/')}"` or equivalent to avoid double slashes; `apply_key_prefix_and_normalize` already collapses `//`.
- **`_current_timestamp`:** May be retained for caching if needed; `filename_for_current_file()` calls `time_fn()` each time. Per spec, timestamp-only means each call can yield a new value; rotation resets record count so next file gets a new timestamp on next write.
