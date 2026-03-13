# Task Plan: 08 — Sinks and Config Wiring

## Overview

This task wires the sink layer to the migrated path patterns (SimplePath, DatedPath, PartitionedPath) so that `key_naming_convention` is no longer passed or used anywhere. The sink must not pass or handle `key_naming_convention`; pattern constructors receive config without that key being relevant. Key shape is fixed by constants (`PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`) as implemented in tasks 05–07.

**Scope:** GCSSink and its unit tests. No changes to target.py config schema (task 03) or path patterns (tasks 05–07).

**Dependencies:** Tasks 03 (config schema), 05 (SimplePath), 06 (DatedPath), 07 (PartitionedPath) must be complete.

---

## Files to Create/Modify

### 1. `loaders/target-gcs/target_gcs/sinks.py`

**Changes:**
- Verify pattern constructors receive only `stream_name`, `config`, `time_fn`, `date_fn`, `storage_client`, `extraction_date` (and for PartitionedPath: `schema`, `partition_fields`).
- Ensure no `key_naming_convention` is passed as a kwarg or added to config before passing to patterns.
- Ensure `time_fn`, `date_fn`, `storage_client` are passed unchanged to all patterns.
- No new logic; this is a verification and cleanup pass. If the sink currently passes `config` as-is and patterns (after 05–07) do not read `key_naming_convention`, no sink code changes may be required. If any sink-level filtering or handling of `key_naming_convention` exists, remove it.

### 2. `loaders/target-gcs/tests/unit/test_sinks.py`

**Remove:**
- `test_public_api_imports_succeed` imports of `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`; update to import new constants (`PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`) if needed for assertions, or remove those assertions.
- `test_key_name_includes_stream_name_when_naming_convention_not_provided` — key_naming_convention config test.
- `test_key_name_includes_stream_name_if_stream_token_used` — key_naming_convention config test.
- `test_key_name_includes_default_date_format_if_date_token_used` — key_naming_convention config test.
- `test_key_name_includes_date_format_if_date_token_used_and_date_format_provided` — key_naming_convention config test.
- `test_key_name_includes_timestamp_if_timestamp_token_used` — key_naming_convention config test.
- `test_key_name_uses_injectable_time_fn_when_provided` — uses key_naming_convention; replace with constants-based assertion.
- `test_get_effective_key_template_returns_user_template_when_set` — key_naming_convention config test.
- `test_get_effective_key_template_returns_hive_default_when_hive_partitioned_and_no_user_template` — update to assert constants-based key shape (no user template).
- `test_get_effective_key_template_returns_non_partition_default_when_neither_set` — update to assert constants-based key shape.
- `test_chunking_key_format_includes_chunk_index` — chunk_index removed; delete or replace with timestamp-only chunking test.

**Add:**
- `test_key_shape_matches_constants`: Key format matches `{prefix}/{stream}/{path}/{timestamp}.jsonl` for each pattern (SimplePath, DatedPath, PartitionedPath). Use deterministic `time_fn` and `date_fn`; assert key structure, not exact string.

**Update:**
- `test_extraction_timestamp_is_unix_time` — key must match `{stream}/{date}/{timestamp}.jsonl` (SimplePath) or equivalent constants-based format.
- `test_chunking_rotation_at_threshold` — remove `key_naming_convention` from config; key shape from constants.
- Tests that assert on `my_stream_\d+\.jsonl` — update to `my_stream/{date}/\d+\.jsonl` (SimplePath) or equivalent.
- `test_key_has_no_chunk_index_when_chunking_disabled` — update assertion: key must not contain chunk_index; must match constants-based format.

**Config schema tests:** If `test_sinks.py` contains assertions that `key_naming_convention` is in config schema, remove them. Schema removal is task 03; this task only removes sink-level tests for that config.

---

## Test Strategy

**TDD order:** Write or update tests first, then verify sink implementation.

1. **Remove key_naming_convention tests** — Delete or replace tests that pass `key_naming_convention` in config or assert on custom key shapes.
2. **Add `test_key_shape_matches_constants`** — Assert key format `{prefix}/{stream}/{path}/{timestamp}.jsonl` for SimplePath (no prefix), DatedPath, PartitionedPath. Use `_patch_all_pattern_modules`, `build_sink` with `time_fn`, `date_fn`; assert `key_name` matches expected structure via regex or segment checks.
3. **Update existing tests** — Adjust assertions to match constants-based key format; remove chunk_index expectations.
4. **Run full suite** — `uv run pytest` from `loaders/target-gcs/`; fix any regressions.

**Test file:** `loaders/target-gcs/tests/unit/test_sinks.py` (per CONVENTIONS: `test_{source-basename}.py` for `sinks.py`).

**Black-box:** Assert on `key_name` and observable behaviour (open calls, handle lifecycle); do not assert on call counts or internal state.

---

## Implementation Order

1. **Remove obsolete tests** — Delete tests that assert on `key_naming_convention` config or custom key shapes.
2. **Add `test_key_shape_matches_constants`** — One test per pattern mode (SimplePath, DatedPath, PartitionedPath) or a parameterized test asserting key format.
3. **Update remaining tests** — Change assertions to match constants-based key format; fix `test_public_api_imports_succeed` imports.
4. **Verify `sinks.py`** — Confirm no `key_naming_convention` handling; confirm `time_fn`, `date_fn`, `storage_client` passed to patterns. Apply any needed cleanup.
5. **Run tests** — `uv run pytest loaders/target-gcs/tests/unit/test_sinks.py -v`.
6. **Run linters** — `uv run ruff check .`, `uv run mypy target_gcs` from `loaders/target-gcs/`.

---

## Validation Steps

1. **Tests pass:** `uv run pytest` from `loaders/target-gcs/` — all pass.
2. **Ruff:** `uv run ruff check .` — no violations.
3. **MyPy:** `uv run mypy target_gcs` — no errors.
4. **Acceptance criteria:**
   - Sink does not pass or use `key_naming_convention`.
   - Key shape from sink matches constants-based format `{prefix}/{stream}/{path}/{timestamp}.jsonl`.
   - All sink tests pass; no regressions.

---

## Documentation Updates

**For this task:** None. Documentation is task 10. If `AI_CONTEXT_target-gcs.md` or `AI_CONTEXT_QUICK_REFERENCE.md` mention `key_naming_convention` in the sink context, they will be updated in task 10.

**Code comments:** None required for sinks.py unless a non-obvious change is made.
