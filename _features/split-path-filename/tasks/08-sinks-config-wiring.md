# 08 — Sinks and Config Wiring

## Background

GCSSink and target must no longer pass or use `key_naming_convention` when constructing path patterns. Pattern constructors receive config without that key. Depends on tasks 03 (config removed), 05–07 (patterns migrated).

## This Task

**Files to modify:**
- `loaders/target-gcs/target_gcs/sinks.py`

**Implementation steps:**
1. Ensure pattern constructors (SimplePath, DatedPath, PartitionedPath) are not passed `key_naming_convention` and do not read it from config.
2. Remove any `key_naming_convention` handling in sink init or pattern selection.
3. Ensure `time_fn`, `date_fn`, `storage_client` are passed to patterns unchanged.

**Tests** in `tests/unit/test_sinks.py`:
- `test_key_shape_matches_constants`: Key format matches `{prefix}/{stream}/{path}/{timestamp}.jsonl`.
- Remove tests for `key_naming_convention` config.
- Remove config schema tests for `key_naming_convention` (if not already removed in task 03).

**Acceptance criteria:**
- Sink does not pass or use `key_naming_convention`.
- Key shape from sink matches constants-based format.
- All sink tests pass.
