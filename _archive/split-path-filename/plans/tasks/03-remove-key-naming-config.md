# Task Plan: 03 — Remove key_naming_convention from Config

## Overview

This task removes `key_naming_convention` from the target-gcs config schema and Meltano plugin definition. Key shape is fixed by constants (added in task 01); users no longer configure key templates. Path patterns will stop reading this config in tasks 04–07; this task prepares the config surface.

**Scope:** Config schema and Meltano settings only. No path pattern or sink logic changes. Depends on task 01 (constants exist). Must complete before path patterns are updated (tasks 04–07).

---

## Files to Create/Modify

### Modify

| File | Change |
|------|--------|
| `loaders/target-gcs/target_gcs/target.py` | Remove the `key_naming_convention` `th.Property` from `config_jsonschema`. |
| `loaders/target-gcs/meltano.yml` | Remove `key_naming_convention` from `settings` list and from `config` example; remove the comment referencing it. |
| `loaders/target-gcs/tests/unit/test_sinks.py` | Add `test_config_schema_excludes_key_naming_convention`; remove tests that pass or assert on `key_naming_convention` config. |
| `loaders/target-gcs/tests/unit/paths/test_base.py` | Remove tests that assert on `key_template` derived from `key_naming_convention` (these tests will be obsolete when task 04 removes `key_template`). |
| `loaders/target-gcs/tests/unit/paths/test_simple.py` | Remove or update chunking test that passes `key_naming_convention` with `{chunk_index}`. |
| `loaders/target-gcs/tests/unit/paths/test_dated.py` | Remove or update chunking test that passes `key_naming_convention` with `{chunk_index}`. |

### Create

None.

---

## Test Strategy

**TDD:** Add the schema-exclusion test first; run it (fails until removal). Remove obsolete tests; implement removal; re-run.

### Test File

`loaders/target-gcs/tests/unit/test_sinks.py` — config schema is defined on `GCSTarget`; sinks tests already cover config behaviour. Per `.cursor/CONVENTIONS.md`, `test_sinks.py` corresponds to `sinks.py`; schema tests live here because schema is consumed by sinks.

### Tests to Add (First)

1. **`test_config_schema_excludes_key_naming_convention`**  
   Load `GCSTarget.config_jsonschema`; assert `"key_naming_convention"` not in `(schema.get("properties") or {})`. WHAT: Config schema no longer exposes key_naming_convention. WHY: Regression guard for config removal.

### Tests to Remove

| File | Test(s) | Reason |
|------|---------|--------|
| `test_sinks.py` | `test_key_name_includes_stream_name_when_naming_convention_not_provided` | Asserts on user key_naming_convention override |
| `test_sinks.py` | `test_key_name_includes_stream_name_if_stream_token_used` | Passes key_naming_convention; asserts token expansion |
| `test_sinks.py` | `test_key_name_includes_default_date_format_if_date_token_used` | Passes key_naming_convention with `{date}` |
| `test_sinks.py` | `test_key_name_includes_custom_date_format_when_date_format_config_set` | Passes key_naming_convention with `{date}` |
| `test_sinks.py` | `test_key_name_includes_timestamp_if_timestamp_token_used` | Passes key_naming_convention with `{timestamp}` |
| `test_sinks.py` | `test_timestamp_in_key_uses_injected_time_fn` | Passes key_naming_convention |
| `test_sinks.py` | `test_get_effective_key_template_returns_user_template_when_set` | Asserts on user key_naming_convention |
| `test_sinks.py` | `test_get_effective_key_template_returns_hive_default_when_hive_partitioned_and_no_user_template` | Asserts on key shape when key_naming_convention omitted |
| `test_sinks.py` | `test_get_effective_key_template_returns_non_partition_default_when_neither_set` | Asserts on default key shape |
| `test_sinks.py` | `test_chunking_key_format_includes_chunk_index` | Passes key_naming_convention with `{chunk_index}` |
| `test_sinks.py` | Chunking test that passes `key_naming_convention: "{stream}_{timestamp}.jsonl"` | Config no longer valid |
| `test_base.py` | `test_key_template_returns_user_template_when_set` | Asserts on key_naming_convention behaviour |
| `test_base.py` | `test_key_template_returns_hive_default_when_hive_partitioned_and_no_user_template` | Asserts on key_naming_convention default |
| `test_base.py` | `test_key_template_returns_non_partition_default_when_neither_set` | Asserts on key_naming_convention default |
| `test_base.py` | `test_key_template_empty_user_template_uses_default` | Asserts on key_naming_convention empty/whitespace |
| `test_simple.py` | Chunking test with `key_naming_convention: "{stream}_{timestamp}-{chunk_index}.{format}"` | Config no longer valid |
| `test_dated.py` | Chunking test with `key_naming_convention: "{stream}/{partition_date}/{timestamp}-{chunk_index}.{format}"` | Config no longer valid |

**Black-box style:** Schema test asserts on schema structure only; no call counts or log assertions.

---

## Implementation Order

1. **TDD:** Add `test_config_schema_excludes_key_naming_convention` to `test_sinks.py`. Run `uv run pytest loaders/target-gcs/tests/unit/test_sinks.py::test_config_schema_excludes_key_naming_convention -v` — fails (property still present).
2. Remove `key_naming_convention` from `config_jsonschema` in `target.py`.
3. Remove `key_naming_convention` from `meltano.yml` (settings and config example).
4. Re-run schema test — passes.
5. Remove obsolete tests from `test_sinks.py`, `test_base.py`, `test_simple.py`, `test_dated.py` per table above.
6. For chunking tests in `test_simple.py` and `test_dated.py`: if the test asserts only on chunking behaviour (e.g. multiple files created) and can run without `key_naming_convention`, update config to omit it and adjust assertions for new key shape (from constants). If the test asserts on `chunk_index` in the key, remove it.
7. Run full test suite from `loaders/target-gcs/` — fix any remaining failures (e.g. imports of removed constants from task 01).
8. Run ruff and mypy.

---

## Validation Steps

1. **Tests:** `uv run pytest` from `loaders/target-gcs/` — all pass.
2. **Lint:** `uv run ruff check .` — no violations.
3. **Types:** `uv run mypy target_gcs` — no errors.
4. **Schema:** `test_config_schema_excludes_key_naming_convention` passes.
5. **Meltano:** `meltano.yml` has no `key_naming_convention` in settings or config.

---

## Documentation Updates

- **README:** Task 10 (documentation) will update the config table and key-naming sections. This task does not modify README.
- **Changelog:** Add entry under `loaders/target-gcs/CHANGELOG.md`: `### Removed` — "key_naming_convention removed from config; key shape is now fixed by internal constants."
