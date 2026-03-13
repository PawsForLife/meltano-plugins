# Pipeline Scratchpad

## Feature: document-test-structure-intent

**Pipeline State:** Phase 5 complete (all tasks implemented); Phase 6 Not started.
**Task Completion Status:** 01-add-test-structure-rule completed; 02-update-patterns completed; 03-optional-conventions completed. All tests passing for docs-only changes (5 pre-existing failures in target-gcs tests unrelated to this feature).
**Task count:** 3 (task 03 optional).
**Tasks directory:** `_features/document-test-structure-intent/tasks/`.
**Ordered task files:** `01-add-test-structure-rule.md`, `02-update-patterns.md`, `03-optional-conventions.md`.
**Execution Order:** 01-add-test-structure-rule → 02-update-patterns → 03-optional-conventions (01 and 02 required; 03 optional).
**Output directory:** `_features/document-test-structure-intent/planning/` — contains `impacted-systems.md`, `new-systems.md`, `possible-solutions.md`, `selected-solution.md`.
**Plan location:** `_features/document-test-structure-intent/plans/master/` — overview.md, architecture.md, interfaces.md, implementation.md, testing.md, dependencies.md, documentation.md.
**Task plan created:** 01-add-test-structure-rule at plans/tasks/01-add-test-structure-rule.md.
**Task plan created:** 02-update-patterns at plans/tasks/02-update-patterns.md.
**Task plan created:** 03-optional-conventions at plans/tasks/03-optional-conventions.md.

**Key findings:**
- **Impacted:** `.cursor/rules/development_practices.mdc` (primary — has TDD/black-box but no structure/scoping); `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` (test layout exists but lacks one-file-per-module, unit/integration boundaries, thin integration); CONVENTIONS and workflows optional.
- **New content:** Four concepts — one test file per source module; unit tests in-scope (single module); integration tests thin (wire behaviour, trust callees, no re-validation); avoid duplication and mixing.
- **Options considered:** Extend development_practices (A), new test-structure.mdc (B), CONVENTIONS only (C), development_practices + CONVENTIONS pointer (D).

**Selected solution:** Internal docs only. Add a “Test structure and scoping” subsection to `.cursor/rules/development_practices.mdc` with the four bullets. Update `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` “Testing & TDD” / test layout to match. Optional: one-line pointer in CONVENTIONS. No new rule file; no code or test changes.

**Phase 2 key decisions:**
- **Single subsection in development_practices:** “Test structure and scoping” with four bullets; no new rule file.
- **PATTERNS aligned:** AI_CONTEXT_PATTERNS.md “Testing & TDD” / test layout updated to match rule (one file per module, unit/integration, thin integration, no duplication/mixing).
- **Optional CONVENTIONS:** One-line pointer to the rule for test layout; omit if discoverability from CONVENTIONS not needed.
- **Verification:** Read updated rule and PATTERNS for consistency; no new automated tests.

---

## Feature: restructure-target-gcs-tests

**Pipeline State:** Phase 2 Complete; Phase 3–6 Not started.
**Task Completion Status:** Research (Phase 1) complete; planning docs written; master plan (Phase 2) complete.
**Execution Order:** (empty until Phase 3 completes.)
**Plan location:** `_features/restructure-target-gcs-tests/plans/master/` — overview.md, architecture.md, interfaces.md, implementation.md, testing.md, dependencies.md, documentation.md.

**Phase 1 summary:**
- **Output directory:** `_features/restructure-target-gcs-tests/planning/` — contains `impacted-systems.md`, `new-systems.md`, `possible-solutions.md`, `selected-solution.md`.
- **Test-to-source mapping:** Flat layout; 1:1 mapping. Renames: `test_core.py` → `test_target.py`; `test_simple_path.py` → `test_paths_simple.py`; `test_dated_path.py` → `test_paths_dated.py`; `test_partitioned_path.py` → `test_paths_partitioned.py`. Keep `test_sinks.py`, `test_paths_base.py`, and `tests/helpers/*` names.
- **Split/consolidate:** Merge sink-relevant tests from `test_partition_key_generation.py` into `test_sinks.py`; remove tests that only re-validate partition_path / partition_schema / path behaviour (already covered by unit tests). Delete `test_partition_key_generation.py` after merge.
- **What to skip:** Integration tests that duplicate unit tests (e.g. partition path format, schema validation); duplicate "valid hive schema" and "fallback date in key" tests per existing scratchpad notes.
- **Rules:** Unit = one file per source module, black-box (inputs → outputs / state). Integration = only in test_sinks.py, assert sink’s key paths and pattern selection, not lower-level behaviour.

**Phase 2 key decisions:**
- **Task ordering:** (1) Renames only; (2) Merge test_partition_key_generation into test_sinks + remove duplicates + delete file; (3) Optional shared helpers; (4) CI/script path updates; (5) Verification. Step 2 depends on Step 1.
- **File mapping table:** See `plans/master/implementation.md`. Renames: test_core→test_target; test_simple_path→test_paths_simple; test_dated_path→test_paths_dated; test_partitioned_path→test_paths_partitioned. test_partition_key_generation→removed (tests merged into test_sinks).
- **Duplicates:** Keep `test_hive_partitioned_valid_schema_constructs_successfully`; remove the other "valid hive schema" test. Keep one "fallback date in key" test in test_sinks; do not add a second when merging.
- **File length:** If test_sinks.py exceeds 500 lines after merge, split per content_length.mdc (e.g. test_sinks_integration.py or submodule).

---

## Redundant tests in target-gcs (2025-03-13)

**Scope:** loaders/target-gcs tests only. No feature file; direct analysis.

**Findings:**

1. **Duplicate "valid hive schema constructs" (test_sinks.py)**
   - `test_sink_init_hive_partitioned_valid_x_partition_fields_succeeds` and `test_hive_partitioned_valid_schema_constructs_successfully` both: build_sink with hive_partitioned true and valid x-partition-fields (field in properties + required), assert sink constructs (e.g. stream_name).
   - **Action:** Remove one (e.g. the first); keep `test_hive_partitioned_valid_schema_constructs_successfully`.

2. **Duplicate "fallback date in key when no x-partition-fields" (test_sinks vs test_partition_key_generation)**
   - `test_sinks.test_hive_partitioned_true_no_x_partition_fields_key_contains_fallback_date` and `test_partition_key_generation.test_hive_partitioned_true_without_x_partition_fields_key_contains_fallback_date` both: hive_partitioned true, schema with no x-partition-fields, date_fn, assert key contains year=2024/month=03/day=11.
   - **Action:** Remove the one in test_partition_key_generation; keep the integration test in test_sinks.

**Not redundant (keep):**
- Unit tests in `test_partition_schema.py` vs sink-init validation in `test_sinks.py`: different levels (unit vs integration); both useful.
- Decimal/JSON: helper tests in `test_json_parsing.py` vs sink tests in `test_sinks.py`: unit vs integration.
- Duplicate helpers `build_sink` / `_key_from_open_call` in test_sinks and test_partition_key_generation: duplication of helpers, not of test cases; consolidation could be a separate refactor.
