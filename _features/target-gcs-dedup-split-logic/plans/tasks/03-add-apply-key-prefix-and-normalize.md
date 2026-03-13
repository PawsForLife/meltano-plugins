# Task Plan: 03-add-apply-key-prefix-and-normalize

## Overview

This task deduplicates key prefix application and path normalization by introducing a single private method `_apply_key_prefix_and_normalize` on `GCSSink` and refactoring `_build_key_for_record` to use it. The same logic currently appears in `_build_key_for_record` (lines 129–132) and in the non-hive branch of `key_name` (lines 149–153); only `_build_key_for_record` is refactored in this task. The non-hive path will use the helper in task 06 via `_compute_non_hive_key`. Behaviour is unchanged; all existing key assertions remain the regression gate.

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Add `_apply_key_prefix_and_normalize(self, base: str) -> str` with Google-style docstring. Refactor `_build_key_for_record` to build `base` (formatted key string) and return `self._apply_key_prefix_and_normalize(base)`; remove the inline `prefixed = (f"{self.config.get('key_prefix', '')}/{base}".replace("//", "/").lstrip("/")` block. |
| `loaders/target-gcs/tests/test_sinks.py` or `loaders/target-gcs/tests/test_partition_key_generation.py` | Only if edge cases (empty prefix, double slash, leading slash) for keys produced by `_build_key_for_record` are not already covered: add tests that build a sink with the relevant config and assert on the key returned by `_build_key_for_record`. |

No new files. No changes to `target.py`, helpers, or other modules.

## Test Strategy

1. **Regression:** Existing tests in `test_sinks.py` and `test_partition_key_generation.py` that call `_build_key_for_record` or assert on keys (e.g. partition path in key, key format) must continue to pass. No behaviour change.
2. **TDD for edge cases (if needed):** Before implementing the helper, determine whether the following are already covered by existing tests for keys produced by `_build_key_for_record`:
   - Empty or missing `key_prefix`: key has no leading slash.
   - Non-empty `key_prefix`: key starts with prefix (and no leading slash after normalization).
   - Double slash (e.g. prefix "foo/" and base "bar" or prefix "foo" and base "/bar"): collapsed to single slash.
   - Leading slash in prefix (e.g. `key_prefix="/asdf"`): stripped so key does not start with `/`.
3. If any of these are not covered, add tests first (build sink with appropriate config, call `_build_key_for_record(record, partition_path)`, assert on the returned key). Prefer exercising via `_build_key_for_record` (or `key_name` for non-hive) rather than calling the private helper directly; black-box style per project rules.
4. Implement `_apply_key_prefix_and_normalize` and refactor `_build_key_for_record`; run full target-gcs test suite.

## Implementation Order

1. **Assess coverage:** Run existing tests; optionally add one or more tests for empty prefix, double slash, or leading slash for `_build_key_for_record` if not covered (TDD: add test, see it fail or already pass, then implement).
2. **Implement `_apply_key_prefix_and_normalize`** in `sinks.py`:
   - Signature: `def _apply_key_prefix_and_normalize(self, base: str) -> str`
   - Body: `prefix = self.config.get("key_prefix", "") or ""`; return `f"{prefix}/{base}".replace("//", "/").lstrip("/")`.
   - Add Google-style docstring: purpose (apply config key_prefix and normalize path), Args (`base`: path segment to prefix and normalize), Returns (normalized key string).
3. **Refactor `_build_key_for_record`:**
   - Keep all logic that builds `base` (timestamp, template, format_map, `base = base_key_name.format_map(format_map)`).
   - Replace the assignment `prefixed = (f"{self.config.get('key_prefix', '')}/{base}".replace("//", "/").lstrip("/")` and `return prefixed` with `return self._apply_key_prefix_and_normalize(base)`.
4. Run full target-gcs test suite and fix any regressions.

## Validation Steps

1. From `loaders/target-gcs/`: run `uv run pytest`; all tests pass.
2. Run `uv run ruff check target_gcs` and `uv run ruff format --check target_gcs`; no new issues.
3. Optionally run `uv run mypy target_gcs` if the project runs it.
4. Confirm that `_build_key_for_record` returns identical key strings for the same inputs as before (existing tests that assert on key content or format are the oracle).

## Documentation Updates

- **Code:** Docstring for `_apply_key_prefix_and_normalize` only. No README or external docs change for this task.
- **AI context:** No update required unless a later task (e.g. 09) refreshes component docs; this task does not change public behaviour or interfaces.
