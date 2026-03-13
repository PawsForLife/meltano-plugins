# 01 — Update Constants

## Background

The feature replaces config-driven `key_naming_convention` with fixed path and filename constants. Constants are the foundation; all path patterns will depend on them. No task dependencies.

## This Task

**Files to modify:**
- `loaders/target-gcs/target_gcs/constants.py`
- `loaders/target-gcs/target_gcs/paths/__init__.py`

**Implementation steps:**
1. In `constants.py`:
   - Add `PATH_SIMPLE = "{stream}/{date}"`
   - Add `PATH_DATED = "{stream}/{hive_path}"`
   - Add `PATH_PARTITIONED = "{stream}/{hive_path}"`
   - Add `FILENAME_TEMPLATE = "{timestamp}.jsonl"`
   - Remove `DEFAULT_KEY_NAMING_CONVENTION`
   - Remove `DEFAULT_KEY_NAMING_CONVENTION_HIVE`
   - Keep `DEFAULT_PARTITION_DATE_FORMAT` unchanged
2. In `paths/__init__.py`: Remove exports of removed constants; add exports for new ones if referenced elsewhere.

**Acceptance criteria:**
- New constants exist with exact values per feature spec.
- Old constants removed; no imports of removed constants remain.
- Ruff, MyPy pass.

## Testing Needed

- No new unit tests for constants (values are used by path patterns; pattern tests validate usage).
- Existing tests that import removed constants will fail; fix imports in subsequent tasks (02–09) as patterns are migrated.
