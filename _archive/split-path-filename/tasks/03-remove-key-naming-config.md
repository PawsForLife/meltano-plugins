# 03 — Remove key_naming_convention from Config

## Background

The feature removes `key_naming_convention` from config entirely; key shape is fixed by constants. Depends on task 01 (constants exist). Must complete before path patterns are updated, since patterns will no longer read this config.

## This Task

**Files to modify:**
- `loaders/target-gcs/target_gcs/target.py`
- `loaders/target-gcs/meltano.yml`

**Implementation steps:**
1. In `target.py`: Remove `key_naming_convention` from `config_jsonschema` (the `th.Property` entry).
2. In `meltano.yml`: Remove `key_naming_convention` from settings and config example.
3. **TDD first:** Update or add test that asserts `key_naming_convention` is not in config schema (e.g. in `test_sinks.py` or `test_target.py`). Run test; it may fail until removal is done.
4. Remove any config schema tests that assert on `key_naming_convention` presence or behaviour.

**Acceptance criteria:**
- Config schema has no `key_naming_convention`.
- meltano.yml has no `key_naming_convention` in settings or example.
- Tests assert schema does not include it; all tests pass.

## Testing Needed

- Test: `test_config_schema_excludes_key_naming_convention` — load `GCSTarget.config_jsonschema` and assert `"key_naming_convention"` not in `(schema.get("properties") or {})`.
- Remove: Any tests that pass or assert on `key_naming_convention` config.
