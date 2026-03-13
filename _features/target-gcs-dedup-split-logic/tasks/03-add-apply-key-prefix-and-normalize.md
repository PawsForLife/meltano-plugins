# Task 03: Add _apply_key_prefix_and_normalize and refactor _build_key_for_record

## Background

Key prefix application and path normalization (e.g. `replace("//", "/").lstrip("/")`) are duplicated in `_build_key_for_record` and in the non-hive branch of `key_name`. This task introduces a single private method and refactors `_build_key_for_record` to use it. The non-hive key path will use it later via task 06. No dependency on tasks 01–02 for interface; execution order keeps refactors incremental.

## This Task

- In `loaders/target-gcs/target_gcs/sinks.py`:
  - Implement `_apply_key_prefix_and_normalize(self, base: str) -> str`: get `prefix = self.config.get("key_prefix", "") or ""`; return `f"{prefix}/{base}".replace("//", "/").lstrip("/")`. Handle empty prefix so that a bare base does not get a leading slash inappropriately (match current behaviour).
  - Refactor `_build_key_for_record` to build the base key (or existing logic up to the final key string) and call `self._apply_key_prefix_and_normalize(base)` for the final key; remove the duplicated prefix + normalize block.
- Add a Google-style docstring for `_apply_key_prefix_and_normalize` (purpose, Args for `base`, Returns).

**Acceptance criteria:** `_build_key_for_record` returns the same key strings as before for all existing tests; prefix and normalization logic live only in the new method.

## Testing Needed

- If existing tests in `test_sinks.py` or `test_partition_key_generation.py` already assert on final key strings for various `key_prefix` and base values (including empty prefix, double slash, leading slash), no new test is required. If those edge cases are not covered, add unit tests first (TDD) that build a sink and assert on the resulting key via public behaviour (e.g. `key_name` or `_build_key_for_record`), then implement the helper. Prefer testing via public behaviour; avoid asserting on call counts or log output. Run full target-gcs test suite after implementation.
