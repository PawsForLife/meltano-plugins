# Task Plan: 06 — DatedPath

## Overview

Migrate `DatedPath` to build path from `PATH_DATED` at init using extraction date formatted via `DEFAULT_PARTITION_DATE_FORMAT`. Use the same `process_record` flow as SimplePath: `maybe_rotate_if_at_limit()`, `filename_for_current_file()`, `full_key()`. Remove `key_template`, `_build_key`, `get_chunk_format_map`, and `DEFAULT_KEY_NAMING_CONVENTION_HIVE`. Key shape becomes `{stream}/{hive_path}/{timestamp}.jsonl` where `hive_path` = `year=YYYY/month=MM/day=DD`.

**Dependencies:** Task 01 (constants: `PATH_DATED`, `DEFAULT_PARTITION_DATE_FORMAT`), Task 02 (`date_as_partition` fixed), Task 04 (BasePathPattern: `filename_for_current_file`, `full_key`), Task 05 (SimplePath as reference implementation).

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/paths/dated.py` | Modify: path from constants, use new methods, remove key_template/_build_key |
| `loaders/target-gcs/tests/unit/paths/test_dated.py` | Modify: update tests for new key shape, remove key_naming_convention tests, fix rotation test for timestamp-only |

---

## Test Strategy

**TDD:** Write failing tests first, then implement. Per `tests/unit/` mirroring source path; file `test_dated.py` for `paths/dated.py`. Black-box: assert on keys passed to `smart_open.open`, not call counts or internals.

### Tests to Add / Update (in order)

1. **`test_path_from_path_dated_constant`** — Key matches `{stream}/{hive_path}/{timestamp}.jsonl` shape. With `time_fn=lambda: 12345`, `date_fn=lambda: datetime(2024, 3, 11)`, assert key contains `my_stream/`, `year=2024/month=03/day=11`, `12345`, `.jsonl`. Validates path from `PATH_DATED`.
2. **`test_hive_path_is_extraction_date_formatted`** — `hive_path` segment equals `year=YYYY/month=MM/day=DD` from extraction date. Use `extraction_date=datetime(2024, 6, 15)`; assert `year=2024/month=06/day=15` in key. Validates DatedPath semantics.
3. **`test_filename_is_timestamp_jsonl`** — Filename segment is `{timestamp}.jsonl` (no chunk_index). Validates filename format.

### Tests to Modify

4. **`test_dated_path_partition_path_from_extraction_date_in_key`** — Rename or merge into `test_path_from_path_dated_constant`; update assertions for new key shape (no `key_naming_convention`).
5. **`test_dated_path_one_handle_per_run_when_no_chunking_uses_single_key`** — Keep; remove any `key_naming_convention` from config; assert key shape from constants.
6. **`test_dated_path_rotation_at_limit_produces_keys_with_chunk_index`** — **Replace** with `test_dated_path_rotation_at_limit_produces_keys_with_new_timestamp`. Assert: at `max_records_per_file=2`, rotation produces keys with different timestamps (timestamp-only chunking); no `-0`, `-1` in keys. Use `time_fn=lambda: next(timestamps)` with distinct timestamps per call.
7. **`test_dated_path_close_allows_subsequent_write_to_open_new_handle`** — Keep; remove `key_naming_convention` if present.
8. **`test_dated_path_current_key_empty_before_first_write`** — Keep.
9. **`test_dated_path_current_key_equals_key_passed_to_open_after_one_record`** — Keep.

### Tests to Remove

- Any test that asserts on `key_naming_convention` config or `DEFAULT_KEY_NAMING_CONVENTION_HIVE`.
- `test_dated_path_rotation_at_limit_produces_keys_with_chunk_index` (replaced by timestamp-only variant).

### Test Helper Updates

- **`build_dated_sink`:** Remove `key_naming_convention` from default config. Ensure `extraction_date` is injectable for deterministic tests.
- **Imports:** Remove `DEFAULT_KEY_NAMING_CONVENTION_HIVE`; add `PATH_DATED`, `DEFAULT_PARTITION_DATE_FORMAT` from `target_gcs.constants` if needed for assertions.

---

## Implementation Order

1. **Tests first** — Add `test_path_from_path_dated_constant`, `test_hive_path_is_extraction_date_formatted`, `test_filename_is_timestamp_jsonl`; replace rotation test with timestamp-only variant; remove `key_naming_convention` from all test configs. Run pytest; new/updated tests fail.
2. **Update imports** — Replace `DEFAULT_KEY_NAMING_CONVENTION_HIVE` and `helpers.partition_path.DEFAULT_PARTITION_DATE_FORMAT` with `PATH_DATED`, `DEFAULT_PARTITION_DATE_FORMAT` from `target_gcs.constants`.
3. **Init: set `_path`** — `hive_path = self._extraction_date.strftime(DEFAULT_PARTITION_DATE_FORMAT)`; `self._path = PATH_DATED.format(stream=stream_name, hive_path=hive_path)`. Remove `_partition_path` (or rename to `_path`).
4. **Remove `key_template`** — Delete the property.
5. **Remove `_build_key`** — Delete the method.
6. **Update `process_record`** — Same flow as SimplePath: `maybe_rotate_if_at_limit()`; `filename = self.filename_for_current_file()`; `key = self.full_key(self._path, filename)`; `self._key_name = key`; open handle if needed; `write_record_as_jsonl(record)`.
7. **Run tests** — `uv run pytest tests/unit/paths/test_dated.py` from `loaders/target-gcs/`. All pass.

---

## Validation Steps

1. **DatedPath tests pass:** `cd loaders/target-gcs && uv run pytest tests/unit/paths/test_dated.py -v`
2. **Full path tests pass:** `uv run pytest tests/unit/paths/ -v`
3. **Ruff:** `uv run ruff check target_gcs/paths/dated.py`
4. **MyPy:** `uv run mypy target_gcs/paths/dated.py`
5. **Acceptance:** Path built from `PATH_DATED`; hive_path from extraction date; key shape `{stream}/{hive_path}/{timestamp}.jsonl`; no `key_template`, `key_naming_convention`; rotation uses timestamp-only filenames.

---

## Documentation Updates

- **None** for this task. AI context and README updates are in task 10. Interfaces.md already documents DatedPath; no new public API.

---

## Notes

- **SimplePath reference:** DatedPath `process_record` mirrors SimplePath exactly; only `_path` construction differs (DatedPath uses `PATH_DATED` + `DEFAULT_PARTITION_DATE_FORMAT`; SimplePath uses `PATH_SIMPLE` + `date_format`).
- **`extraction_date`:** Injected via constructor; tests use `extraction_date=datetime(...)` for deterministic keys. Production uses `date_fn()` when not provided (from base).
- **Timestamp-only chunking:** After task 04, `maybe_rotate_if_at_limit` does not increment `chunk_index`; next `filename_for_current_file()` yields a new timestamp. Tests must use distinct `time_fn` return values per call to observe different keys on rotation.
