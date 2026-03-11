# Task Plan: 01-add-config-schema

**Feature:** target-gcs-file-chunking-by-record-count  
**Task:** Add optional `max_records_per_file` to target config JSON schema.

---

## Overview

This task extends the target-gcs config schema with a single optional property so the sink can read `max_records_per_file` for record-count-based file chunking. The target's `config_jsonschema` is the single source of truth for allowed config; adding the property here enables validation and makes the option available to the sink via `self.config.get("max_records_per_file", 0)`. No other target behaviour (e.g. `default_sink_class`) changes. Later tasks (sink state, rotation, key computation) depend on this schema being present.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/gcs_target/target.py` | Add one `th.Property` to `config_jsonschema`: `max_records_per_file` (IntegerType, required=False, description as in task doc). |
| `loaders/target-gcs/tests/test_sinks.py` | Add tests that assert the schema exposes `max_records_per_file`, that it is not required, and that the property type is integer; optionally assert config with and without the key validates. |

No new files. No changes to `test_core.py`, `sinks.py`, or sample config (handled in task 08).

---

## Test Strategy

**TDD:** Add or extend tests first in `test_sinks.py` (schema assertions already live there, e.g. `test_config_schema_has_no_credentials_file`), then implement the schema change until tests pass.

1. **Schema structure (black-box):** Assert `GCSTarget.config_jsonschema["properties"]` contains `max_records_per_file` and that the property is not in `required` (or that config without the key is valid). Assert the property's `type` is integer (per Singer SDK schema shape, e.g. `"type": "integer"` in the property dict).
2. **Config validation (optional but recommended):** If the SDK or test harness supports it, assert that config `{"bucket_name": "b", "max_records_per_file": 1000}` validates and that config `{"bucket_name": "b"}` (no `max_records_per_file`) also validates.

Docstrings: WHAT (schema exposes `max_records_per_file` for chunking) and WHY (sink needs it; config is validated by schema). No assertions on call counts or log lines.

---

## Implementation Order

1. **Add tests** in `loaders/target-gcs/tests/test_sinks.py`:
   - Test that `config_jsonschema["properties"]` includes `max_records_per_file` with type integer and is not required.
   - Optionally: test that full config with `max_records_per_file: 1000` and minimal config without the key both validate (if the test pattern exists in the repo).
2. **Run tests** — they should fail (property not yet in schema).
3. **Implement** in `loaders/target-gcs/gcs_target/target.py`:
   - Inside the existing `th.PropertiesList(...)`, add:  
     `th.Property("max_records_per_file", th.IntegerType, required=False, description="Maximum records per GCS object; 0 or unset = no chunking.")`.
4. **Run tests and lint** — all new and existing tests pass; ruff/mypy clean.

---

## Validation Steps

- From `loaders/target-gcs/`: `uv run pytest tests/test_sinks.py` passes (including new schema tests).
- From `loaders/target-gcs/`: `uv run ruff check .` and `uv run ruff format --check` pass.
- From `loaders/target-gcs/`: `uv run mypy gcs_target` passes.
- Manual smoke: Config that includes `"max_records_per_file": 1000` and config without the key both validate (e.g. via target instantiation or SDK validation if used in tests).
- Acceptance criteria met: Schema documents the property; config with `"max_records_per_file": 1000` validates; config without the key still validates.

---

## Documentation Updates

None for this task. README, sample config, and Meltano settings are covered in task 08 (documentation-and-sample-config). No changes to AI context or master plan docs are required for adding a single schema property.
