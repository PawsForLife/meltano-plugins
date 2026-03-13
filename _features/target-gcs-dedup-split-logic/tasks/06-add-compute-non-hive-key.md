# Task 06: Add _compute_non_hive_key and refactor key_name

## Background

The non-hive branch of `key_name` contains the logic for template, timestamp, date, format_map, base key, and prefix+normalize. This task moves that body into a named method `_compute_non_hive_key` (which uses `_apply_key_prefix_and_normalize` from task 03) and refactors `key_name` so the non-hive branch calls it when `_key_name` is not set, then returns `_key_name`. Depends on task 03 so that `_apply_key_prefix_and_normalize` exists.

## This Task

- In `loaders/target-gcs/target_gcs/sinks.py`:
  - Implement `_compute_non_hive_key(self) -> str`: move the current `key_name` else-branch body (template resolution, timestamp, date, format_map with stream, date, timestamp, format, optional chunk_index), build base key, call `self._apply_key_prefix_and_normalize(base)`, assign result to `self._key_name`, return `self._key_name`.
  - Refactor `key_name`: in the non-hive branch, when `_key_name` is not set, call `return self._compute_non_hive_key()` (or set `_key_name` and return it); otherwise return `_key_name` as today. Keep the hive branch unchanged (it uses `_key_name` set elsewhere).
- Add a Google-style docstring for `_compute_non_hive_key` (purpose, Returns).

**Acceptance criteria:** Non-hive key computation lives in `_compute_non_hive_key`; `key_name` is a thin dispatcher for the non-hive path; key strings and caching behaviour unchanged.

## Testing Needed

- No new tests; existing key naming and partition key generation tests cover this path. Run full target-gcs test suite to confirm regression gate passes.
