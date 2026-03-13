# 05 — SimplePath: Path from Constants

## Background

SimplePath must build path from `PATH_SIMPLE` at init and use `filename_for_current_file()` and `full_key()` in `process_record`. Depends on tasks 01 (constants), 04 (BasePathPattern methods).

## This Task

**Files to modify:**
- `loaders/target-gcs/target_gcs/paths/simple.py`

**Implementation steps (TDD first):**

1. **Tests first** in `tests/unit/paths/test_simple.py`:
   - `test_path_from_path_simple_constant`: Key matches `{stream}/{date}/{timestamp}.jsonl` shape.
   - `test_filename_is_timestamp_jsonl`: Filename segment is `{timestamp}.jsonl`.
   - `test_uses_date_format_from_config`: With `date_format="%Y"`, path contains year only.
   - Remove tests for `key_naming_convention`.

2. **Implementation:**
   - At init: `date_fmt = config.get("date_format", "%Y-%m-%d")`; `date_str = _extraction_date.strftime(date_fmt)`; `_path = PATH_SIMPLE.format(stream=stream_name, date=date_str)`.
   - In `process_record`: `maybe_rotate_if_at_limit()`; `filename = filename_for_current_file()`; `key = full_key(self._path, filename)`; open handle if needed; write record.
   - Remove `key_template`, `_build_key`, `get_chunk_format_map` usage.
   - Remove import of `DEFAULT_KEY_NAMING_CONVENTION`.
   - Import `PATH_SIMPLE` from `target_gcs.constants`.

**Acceptance criteria:**
- Path built from `PATH_SIMPLE` at init.
- `process_record` uses `filename_for_current_file`, `full_key`.
- Tests pass; key shape matches `{stream}/{date}/{timestamp}.jsonl`.
