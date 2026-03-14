# split-path-filename — Archive Summary

## The request

The target-gcs loader used `key_naming_convention` config to control path and filename format, adding complexity and configuration surface. The goal was to simplify by:

- Removing `key_naming_convention` entirely
- Using fixed path and filename constants in `constants.py`
- Keeping `key_prefix` for user-controlled prefix
- Using timestamp-only chunking (no `chunk_index`; assume ≥1 second between chunks)

Greenfields project—no backwards compatibility required.

**Fixed path formats:**

| Pattern         | Path part              | Filename            |
| --------------- | ---------------------- | ------------------- |
| SimplePath      | `{stream}/{date}`      | `{timestamp}.jsonl` |
| DatedPath       | `{stream}/{hive_path}` | `{timestamp}.jsonl` |
| PartitionedPath | `{stream}/{hive_path}` | `{timestamp}.jsonl` |

DatedPath uses extraction date formatted via `DEFAULT_PARTITION_DATE_FORMAT`; PartitionedPath uses `hive_path(record)` from `_partitioned`.

**Testing:** Black-box tests for path patterns, sinks, and config schema; TDD; no `key_naming_convention` or `chunk_index` assertions.

---

## Planned approach

**Solution:** Internal `str.format()` with path and filename constants. No external libraries. Path and filename split in `constants.py`; `BasePathPattern` provides `filename_for_current_file()` and `full_key(path, filename)`; each pattern builds path from constants and composes the final key.

**Constants:** `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`; remove `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`.

**BasePathPattern:** Add `filename_for_current_file() -> str`, `full_key(path, filename) -> str`; remove `key_template`, `get_chunk_format_map`, `_chunk_index`.

**Path patterns:** SimplePath and DatedPath build path at init from constants; PartitionedPath uses `path_for_record(record)` with `hive_path(record)`. All use `filename_for_current_file()` and `full_key()` in `process_record`.

**Pre-existing bug:** `date_as_partition` in `_partitioned/string_functions.py` did not return the formatted string; fix before PartitionedPath migration.

**Implementation order (10 tasks):**

1. Update constants
2. Fix `date_as_partition` return
3. Remove `key_naming_convention` from config and meltano.yml
4. Add `filename_for_current_file`, `full_key` to BasePathPattern; remove chunk index
5. SimplePath: path from `PATH_SIMPLE` at init
6. DatedPath: path from `PATH_DATED` at init
7. PartitionedPath: `path_for_record` with `hive_path(record)`; partition change detection
8. Sinks config wiring: no `key_naming_convention` passed to patterns
9. Helpers cleanup: remove `get_partition_path_from_schema_and_record` and `helpers/partition_path.py`
10. Documentation: README, AI context, CHANGELOG

---

## What was implemented

All 10 tasks completed. Summary:

**Constants (01):** Added `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`; removed `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`; updated `paths/__init__.py` exports.

**Bug fix (02):** `date_as_partition` now returns the formatted date string; unit tests in `tests/unit/paths/_partitioned/test_string_functions.py`.

**Config (03):** Removed `key_naming_convention` from `config_jsonschema`, meltano.yml; added `test_config_schema_excludes_key_naming_convention`; removed obsolete key-template and chunk-index tests.

**BasePathPattern (04):** Added `filename_for_current_file()`, `full_key(path, filename)`; removed `key_template`, `get_chunk_format_map`, `_chunk_index`; chunking uses timestamp only.

**Path patterns (05–07):** SimplePath builds `_path` from `PATH_SIMPLE` at init; DatedPath from `PATH_DATED` with extraction date; PartitionedPath uses `path_for_record(record)` with `hive_path(record)`. All use `filename_for_current_file()` and `full_key()` in `process_record`. Removed `_build_key`, `record_path`, `get_partition_path_from_schema_and_record` usage.

**Sinks (08):** Sink does not pass or use `key_naming_convention`; added `test_key_shape_matches_constants`; key shape from constants.

**Helpers (09):** Removed `get_partition_path_from_schema_and_record` and `helpers/partition_path.py`; `DEFAULT_PARTITION_DATE_FORMAT` single source in `constants.py`; deleted `test_partition_path.py`.

**Documentation (10):** README config table and Hive section updated; key format table added; AI context (config schema, key tokens, path patterns) updated; CHANGELOG entries for Removed and Changed.

**Outcome:** Key format fixed via constants; chunking timestamp-only; config surface reduced; all tests pass; ruff and mypy pass.
