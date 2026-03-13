# 06 — DatedPath: Path from Constants

## Background

DatedPath must build path from `PATH_DATED` at init using extraction date formatted via `DEFAULT_PARTITION_DATE_FORMAT`. Same `process_record` flow as SimplePath. Depends on tasks 01 (constants), 02 (date_as_partition fixed), 04 (BasePathPattern methods).

## This Task

**Files to modify:**
- `loaders/target-gcs/target_gcs/paths/dated.py`

**Implementation steps (TDD first):**

1. **Tests first** in `tests/unit/paths/test_dated.py`:
   - `test_path_from_path_dated_constant`: Key matches `{stream}/{hive_path}/{timestamp}.jsonl` shape.
   - `test_hive_path_is_extraction_date_formatted`: hive_path = `year=YYYY/month=MM/day=DD`.
   - Remove tests for `key_naming_convention`.

2. **Implementation:**
   - At init: `hive_path = _extraction_date.strftime(DEFAULT_PARTITION_DATE_FORMAT)`; `_path = PATH_DATED.format(stream=stream_name, hive_path=hive_path)`.
   - In `process_record`: same flow as SimplePath — `maybe_rotate_if_at_limit()`; `filename = filename_for_current_file()`; `key = full_key(self._path, filename)`; open handle if needed; write record.
   - Remove `key_template`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE` import.
   - Import `PATH_DATED`, `DEFAULT_PARTITION_DATE_FORMAT` from `target_gcs.constants`.

**Acceptance criteria:**
- Path built from `PATH_DATED` at init; hive_path from extraction date.
- `process_record` uses `filename_for_current_file`, `full_key`.
- Tests pass; key shape matches `{stream}/{hive_path}/{timestamp}.jsonl`.
