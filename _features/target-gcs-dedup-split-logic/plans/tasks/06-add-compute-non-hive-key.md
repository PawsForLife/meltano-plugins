# Task Plan: 06-add-compute-non-hive-key

## Overview

This task moves the non-hive key computation from the `key_name` property into a dedicated private method `_compute_non_hive_key(self) -> str` and refactors `key_name` so the non-hive branch delegates to it when `_key_name` is not set. Behaviour and caching semantics are unchanged; key strings and when they are computed remain the same. Depends on task 03 so that `_apply_key_prefix_and_normalize` exists and is used for the final key.

**Feature context:** Part of target-gcs-dedup-split-logic (split switch logic into named functions). See [master implementation.md](../master/implementation.md) step 6 and [interfaces.md](../master/interfaces.md) (`_compute_non_hive_key`).

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Add `_compute_non_hive_key`; refactor `key_name` non-hive branch to call it when `_key_name` is unset. |

**No new files.** No changes to helpers, target.py, or tests (other than running the existing suite).

### sinks.py — Specific changes

1. **Add `_compute_non_hive_key`** (place after `_get_effective_key_template`, before `_build_key_for_record`, or in a logical key-related block so call order is clear):
   - Signature: `def _compute_non_hive_key(self) -> str`
   - Body: Resolve effective template via `_get_effective_key_template()`; get timestamp `round((self._time_fn or time.time)())`; get run date and format `date` via `_date_fn` or `datetime.today()` and `config.get("date_format", "%Y-%m-%d")`; build `format_map` with `stream`, `date`, `timestamp`, `format=self.output_format`, and `chunk_index` when `max_records_per_file` is set and > 0; set `base = base_key_name.format_map(format_map)`; set `self._key_name = self._apply_key_prefix_and_normalize(base)`; return `self._key_name`.
   - Docstring: Google-style; purpose (compute and cache the non-hive object key from template, timestamp, date, and optional chunk_index; applies key prefix and normalization). Returns: the computed key string (and assigns it to `_key_name`).

2. **Refactor `key_name` property**:
   - Hive branch: leave unchanged (`if self.config.get("hive_partitioned"): return self._key_name`).
   - Non-hive branch: when `_key_name` is not set, call `return self._compute_non_hive_key()` instead of the current inline block; when `_key_name` is set, `return self._key_name`. Remove the entire inline block that computes `extraction_timestamp`, `base_key_name`, `prefixed_key_name`, `run_date`, `date`, `format_map`, and assigns `self._key_name`.

## Test Strategy

- **No new tests.** The task document and master testing plan state that existing key naming and partition key generation tests cover this path. Regression is verified by running the full target-gcs test suite.
- **TDD:** Not applicable—pure refactor; observable behaviour (key strings and caching) is unchanged; existing tests in `test_sinks.py` and `test_partition_key_generation.py` that assert on `key_name` or keys produced for non-hive config remain the regression gate.

## Implementation Order

1. Implement `_compute_non_hive_key(self) -> str` with the logic moved from the non-hive branch of `key_name`, using `self._apply_key_prefix_and_normalize(base)` for the final key. Add a Google-style docstring (purpose, Returns).
2. In `key_name`, replace the non-hive `if not self._key_name:` block with a call to `return self._compute_non_hive_key()` when `_key_name` is unset; keep `return self._key_name` for the case when it is already set.
3. Run the full target-gcs test suite to confirm no regressions.

## Validation Steps

1. **Tests:** From `loaders/target-gcs/`, run `uv run pytest`. All tests must pass.
2. **Linting/formatting:** Run `uv run ruff check target_gcs` and `uv run ruff format --check target_gcs`. Resolve any issues in modified files.
3. **Type check:** Run `uv run mypy target_gcs`; no new errors in `sinks.py`.
4. **Behaviour:** Tests that assert on `key_name` or on keys used for non-hive, single-file or chunked writes (e.g. default template, custom `key_naming_convention`, `key_prefix`, `date_format`, `max_records_per_file` with chunk_index) must still pass without change—confirm key strings and caching behaviour are unchanged.

## Documentation Updates

- **Code:** Add a Google-style docstring for `_compute_non_hive_key` only. No README or external docs change.
- **AI context:** No update required for this task; task 09 may refresh component docs.
