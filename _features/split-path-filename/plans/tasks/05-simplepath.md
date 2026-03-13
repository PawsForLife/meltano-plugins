# Task Plan: 05 — SimplePath

## Overview

This task migrates `SimplePath` to the split path/filename model. The path is built from `PATH_SIMPLE` at init using `stream` and `date` tokens; `process_record` uses `filename_for_current_file()` and `full_key()` from `BasePathPattern`. Chunking uses timestamp-only filenames (no `chunk_index`). All `key_template`, `_build_key`, `get_chunk_format_map`, and `key_naming_convention` usage is removed.

**Dependencies:** Task 01 (constants: `PATH_SIMPLE` must exist), Task 04 (BasePathPattern: `filename_for_current_file`, `full_key` must exist; `key_template`, `get_chunk_format_map`, `_chunk_index` removed).

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/paths/simple.py` | Modify: path from `PATH_SIMPLE` at init; `process_record` uses `filename_for_current_file`, `full_key`; remove `key_template`, `_build_key`, `get_chunk_format_map`; remove `DEFAULT_KEY_NAMING_CONVENTION` import |
| `loaders/target-gcs/tests/unit/paths/test_simple.py` | Modify: add new tests; update/remove tests for new key shape and timestamp-only chunking |

---

## Test Strategy

**TDD:** Write failing tests first, then implement. Per `.cursor/CONVENTIONS.md`: test file `test_simple.py` under `tests/unit/paths/` mirrors `target_gcs/paths/simple.py`.

### Tests to Add (in order)

1. **`test_path_from_path_simple_constant`** — With `time_fn=lambda: 12345`, `date_fn=lambda: datetime(2024, 3, 11)`, after one `process_record`, key matches `{stream}/{date}/{timestamp}.jsonl` (e.g. `my_stream/2024-03-11/12345.jsonl`). Validates path format from `PATH_SIMPLE`.
2. **`test_filename_is_timestamp_jsonl`** — Filename segment (last path component) is `{timestamp}.jsonl`. Validates filename format.
3. **`test_uses_date_format_from_config`** — With `date_format="%Y"`, path contains year only (e.g. `my_stream/2024/12345.jsonl`). Validates config-driven date token.
4. **`test_rotation_at_limit_uses_timestamp_only`** — With `max_records_per_file=2`, processing 5 records opens multiple handles; keys differ by timestamp segment only (no `chunk_index`). Replaces `test_simple_path_rotation_at_limit_produces_keys_with_chunk_index`.

### Tests to Update

- **`test_simple_path_key_generation_single_path_matches_stream_date_timestamp_format`** — Rename or merge into `test_path_from_path_simple_constant`; assert key shape `{stream}/{date}/{timestamp}.jsonl` instead of `my_stream_...`.
- **`test_simple_path_one_handle_when_no_chunking_uses_single_key`** — Keep; key shape changes to `{stream}/{date}/{timestamp}.jsonl`; no logic change.
- **`test_simple_path_close_allows_subsequent_write_to_open_new_handle`** — Keep; no logic change.
- **`test_simple_path_current_key_empty_before_first_write`** — Keep.
- **`test_simple_path_current_key_equals_key_passed_to_open_after_one_record`** — Keep.

### Tests to Remove

- **`test_simple_path_rotation_at_limit_produces_keys_with_chunk_index`** — Replaced by `test_rotation_at_limit_uses_timestamp_only`; removes `key_naming_convention` and `chunk_index` assertions.

### Fixtures and Helpers

- **`_build_simple_path`** — Retain; ensure `extraction_date` is passed (required for path building). Default `date_fn=lambda: datetime(2024, 3, 11)` for deterministic tests.
- **`_key_from_open_call`** — Retain; extracts key from `smart_open.open` call args.

---

## Implementation Order

1. **Tests first** — Add `test_path_from_path_simple_constant`, `test_filename_is_timestamp_jsonl`, `test_uses_date_format_from_config`, `test_rotation_at_limit_uses_timestamp_only`; update `test_simple_path_key_generation_single_path_matches_stream_date_timestamp_format` to assert new key shape; remove `test_simple_path_rotation_at_limit_produces_keys_with_chunk_index`. Run pytest; new/updated tests fail (SimplePath still uses old implementation).
2. **Import change** — Replace `from target_gcs.constants import DEFAULT_KEY_NAMING_CONVENTION` with `from target_gcs.constants import PATH_SIMPLE`.
3. **Init: build path** — In `__init__` (or a method called from `__init__`): `date_fmt = config.get("date_format", "%Y-%m-%d")`; `date_str = self._extraction_date.strftime(date_fmt)`; `self._path = PATH_SIMPLE.format(stream=stream_name, date=date_str)`.
4. **Remove `key_template`** — Delete the `key_template` property from `SimplePath`.
5. **Remove `_build_key`** — Delete the method.
6. **Update `process_record`** — `maybe_rotate_if_at_limit()`; `filename = self.filename_for_current_file()`; `key = self.full_key(self._path, filename)`; `self._key_name = key`; open handle if needed; `write_record_as_jsonl(record)`.
7. **Run tests** — `uv run pytest tests/unit/paths/test_simple.py -v` from `loaders/target-gcs/`. All pass.
8. **Ruff and MyPy** — `uv run ruff check target_gcs/paths/simple.py`; `uv run mypy target_gcs/paths/simple.py`.

---

## Validation Steps

1. **Unit tests pass:** `cd loaders/target-gcs && uv run pytest tests/unit/paths/test_simple.py -v`
2. **Full target-gcs tests:** `uv run pytest -v` (no regressions in other path or sink tests)
3. **Ruff:** `uv run ruff check target_gcs/paths/simple.py`
4. **MyPy:** `uv run mypy target_gcs`
5. **Acceptance:** Path built from `PATH_SIMPLE` at init; `process_record` uses `filename_for_current_file`, `full_key`; key shape `{stream}/{date}/{timestamp}.jsonl`; no `key_template`, `_build_key`, `get_chunk_format_map`, or `key_naming_convention` references.

---

## Documentation Updates

- **None** for this task. AI context and README updates are in task 10. No new public API beyond what `interfaces.md` already documents.

---

## Notes

- **Path format:** `PATH_SIMPLE` is `"{stream}/{date}"`; full key is `{stream}/{date}/{timestamp}.jsonl` after `full_key` joins path and filename.
- **Key prefix:** `full_key` applies `key_prefix` via `apply_key_prefix_and_normalize`; tests may assert with or without prefix depending on config.
- **Chunking:** `maybe_rotate_if_at_limit` (from base) flushes and closes; next `filename_for_current_file()` yields new timestamp. No `chunk_index` in key.
