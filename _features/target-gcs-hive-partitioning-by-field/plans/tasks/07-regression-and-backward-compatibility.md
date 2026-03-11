# Task Plan: 07-regression-and-backward-compatibility

**Feature:** target-gcs-hive-partitioning-by-field  
**Task:** Satisfy the regression gate and add or confirm an explicit backward-compatibility test so that when `partition_date_field` is unset, behaviour is unchanged.  
**Master plan:** [../master/overview.md](../master/overview.md), [../master/implementation.md](../master/implementation.md), [../master/testing.md](../master/testing.md), [../master/interfaces.md](../master/interfaces.md)

---

## 1. Overview

This task runs after tasks 01–06 have implemented partition-by-field. It ensures (1) no regressions: all existing tests in `loaders/target-gcs/tests/` pass, and (2) backward compatibility is explicitly asserted: when `partition_date_field` is not set, `key_name` and single-key-per-stream (or per-chunk) behaviour match current behaviour. Any failing test not marked as expected failure is treated as a regression and must be fixed before the task is complete. An explicit test may already be satisfied by existing tests (e.g. `test_key_name_includes_default_date_format_if_date_token_used`, `test_one_key_and_one_handle_when_chunking_disabled`, `test_key_has_no_chunk_index_when_chunking_disabled`); if not, a dedicated test is added.

**Scope:** Test execution, regression fixes (in sink or tests as appropriate), and one explicit backward-compatibility test (add or confirm).

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `loaders/target-gcs/tests/test_sinks.py` | Modify | Extend `build_sink` to accept `date_fn` if not already present (from task 04). Add or confirm one explicit backward-compatibility test: sink built **without** `partition_date_field` exhibits unchanged key_name behaviour (run-date based, single key per stream or per chunk). No other test logic changes unless required to fix regressions. |
| `loaders/target-gcs/tests/test_core.py` | No change unless regression | If any test in `test_core.py` fails due to partition-by-field changes, fix the regression (prefer fixing production code in `sinks.py` or `target.py` to preserve test intent). |
| `loaders/target-gcs/gcs_target/sinks.py` | Modify only if regression | If test failures point to a bug in partition-by-field or key_name when `partition_date_field` is unset, fix the implementation so existing tests pass. |
| `loaders/target-gcs/gcs_target/target.py` | Modify only if regression | Only if a failing test indicates target/config behaviour is wrong. |

**No new files.** All work is in existing test and (if needed) production modules.

---

## 3. Test Strategy

**Regression gate (master testing.md):** All existing tests in `loaders/target-gcs/tests/` must pass. No assertions on call counts or logs; fix failures by correcting behaviour or test expectations (prefer behaviour).

**Backward-compatibility test (explicit):**

- **Option A — Confirm coverage:** If existing tests already guarantee that when `partition_date_field` is unset:
  - `key_name` uses run date (e.g. `{date}` from today or from injectable `date_fn`) and does not depend on record content, and
  - Single key per stream when chunking is disabled, and single key per chunk when chunking is enabled,
  then document that in the test (e.g. add a short docstring to an existing test or add a single test that asserts both properties in one place).

- **Option B — Add dedicated test:** Add one test that:
  - Builds a sink with config that **does not** include `partition_date_field` (and optionally uses `date_fn` for determinism).
  - Asserts that `key_name` uses run date (e.g. contains the date from `date_fn` or matches pattern that does not include partition path from record).
  - Optionally asserts that after processing multiple records, the same key is used (single key per stream when chunking off) and key does not contain Hive-style partition segments from record data.

**Recommended test name:** `test_backward_compat_key_name_unchanged_when_partition_date_field_unset` (or equivalent).  
**WHAT:** When `partition_date_field` is unset, key_name and single-handle semantics match pre-feature behaviour (run-date key, no record-driven partition). **WHY:** Regression gate and explicit backward-compatibility requirement.

**Tests that must remain green (no changes to pass/fail logic unless fixing a real regression):**  
`test_extraction_timestamp_is_unix_time`, `test_key_name_includes_prefix_when_provided`, `test_key_name_does_not_start_with_slash`, `test_key_name_includes_stream_name_when_naming_convention_not_provided`, `test_key_name_includes_stream_name_if_stream_token_used`, `test_key_name_includes_default_date_format_if_date_token_used`, `test_key_name_includes_date_format_if_date_token_used_and_date_format_provided`, `test_key_name_includes_timestamp_if_timestamp_token_used`, `test_key_name_uses_injectable_time_fn_when_provided`, config schema tests, GCS client tests, `test_one_key_and_one_handle_when_chunking_disabled`, `test_key_has_no_chunk_index_when_chunking_disabled`, `test_chunking_rotation_at_threshold`, `test_chunking_key_format_includes_chunk_index`, `test_chunking_record_integrity_no_duplicate_or_dropped`, and all tests in `test_core.py`.

---

## 4. Implementation Order

1. **Run full test suite**  
   From repo root (with venv active): `uv run pytest loaders/target-gcs/tests/ -v` (or project test command per README). Record which tests fail, if any.

2. **Fix regressions**  
   For each failing test not marked `@pytest.mark.xfail` or `@unittest.expectedFailure`: determine root cause (sink, target, or test). Prefer fixing production code so that existing test expectations remain valid. Re-run the suite until all tests pass.

3. **Assess backward-compatibility coverage**  
   Review existing tests that do not set `partition_date_field` (e.g. `test_key_name_includes_default_date_format_if_date_token_used`, `test_one_key_and_one_handle_when_chunking_disabled`). If they already assert run-date key and single-key semantics when the option is unset, add a brief docstring or comment that they serve as the backward-compatibility test, or add a single consolidated test that makes the guarantee explicit.

4. **Add explicit test if needed**  
   If no single test clearly asserts “partition_date_field unset → key_name and single-key behaviour unchanged,” add `test_backward_compat_key_name_unchanged_when_partition_date_field_unset` (or equivalent): build sink without `partition_date_field`, optionally with `date_fn` for deterministic key, assert key uses run date and does not depend on record content, and that multiple records use the same key when chunking is disabled.

5. **Final validation**  
   Run `uv run pytest loaders/target-gcs/tests/ -v` again. All tests must pass. No new failures.

---

## 5. Validation Steps

- [ ] `uv run pytest loaders/target-gcs/tests/` (or project test command) exits with code 0.
- [ ] No test is failing unless marked as expected failure.
- [ ] At least one test explicitly or by clear docstring/comment covers backward compatibility when `partition_date_field` is unset (key_name and single-key semantics unchanged).
- [ ] Linters and type checks per project rules pass for any modified files.

---

## 6. Documentation Updates

- **None required for this task.** README and AI context are updated in tasks 08 and 09. This task does not change user-facing config or behaviour; it only validates regression and backward compatibility.

---

## Dependencies

- **Tasks 01–06:** Must be complete. This task assumes config schema, partition resolution, sink date_fn/partition state, key building with partition_date, and process_record/handle lifecycle are implemented. This task does not implement new behaviour; it validates and guards existing behaviour.
