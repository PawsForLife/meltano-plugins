# Task Plan: 05-key-building-with-partition-date

**Feature:** target-gcs-hive-partitioning-by-field
**Task:** Add `_build_key_for_record` and adjust `key_name` when `partition_date_field` is set; keys are built per record with `{partition_date}` token.
**Master plan:** [../master/overview.md](../master/overview.md), [../master/implementation.md](../master/implementation.md), [../master/interfaces.md](../master/interfaces.md), [../master/testing.md](../master/testing.md)

---

## 1. Overview

When `partition_date_field` is set, the object key must be built per record using the partition path from `get_partition_path_from_record` (or the path passed in), plus stream, timestamp, and chunk_index. The new token `{partition_date}` is replaced with that partition path. This task adds the internal method `_build_key_for_record(self, record: dict, partition_path: str) -> str` and updates the `key_name` property so that when partition-by-field is on, callers that need a key per record use `_build_key_for_record`; when unset, behaviour is unchanged (run-date, single key). Handle lifecycle and `process_record` wiring are **not** in this task (task 06).

**Scope:** Key building only. No changes to `process_record`, handle open/close, or rotation logic.

**Dependencies:** Tasks 01 (config schema), 03 (partition resolution), 04 (date_fn and partition state). The sink already has `_date_fn`, `_current_partition_path`, and config keys; `get_partition_path_from_record` exists in `sinks.py`.

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `loaders/target-gcs/gcs_target/sinks.py` | Modify | Add `_build_key_for_record(self, record: dict, partition_path: str) -> str`. Build from `key_prefix` + `key_naming_convention` with format_map: `stream`, `partition_date` (= partition_path), `timestamp` (from `_time_fn` or `time.time`), `chunk_index` (if chunking). Use same normalization as existing key logic: `replace("//", "/").lstrip("/")`. Only used when `partition_date_field` is set. Update `key_name` property: when `partition_date_field` is set, return current key if `_key_name` is non-empty (e.g. after a write), otherwise return a stable placeholder or empty string so callers use `_build_key_for_record` for per-record keys; when unset, keep existing logic unchanged. |
| `loaders/target-gcs/tests/test_sinks.py` | Modify | Extend `build_sink` to pass `date_fn` and `time_fn` where tests need deterministic keys. Add tests: key differs by partition value; key includes Hive-style segment; fallback when field missing; unset `partition_date_field` leaves key behaviour unchanged (existing key_name tests still pass). |

No new files.

---

## 3. Test Strategy

TDD: write tests first, then implement `_build_key_for_record` and `key_name` behaviour. Assert on key strings (observable outcome); do not assert on call counts or internal method invocations.

**Location:** `loaders/target-gcs/tests/test_sinks.py`.

| Test | What | Why |
|------|------|-----|
| **Key differs by partition value** | Sink with `partition_date_field`, `key_naming_convention` containing `{partition_date}`; call `_build_key_for_record(record_a, path_a)` and `_build_key_for_record(record_b, path_b)` with two different partition paths; assert the two returned keys differ. Use fixed `time_fn` and `date_fn` so keys are deterministic. | Core partition-by-field behaviour: different partition values yield different keys. |
| **Key includes Hive-style partition path** | One record, known partition path (e.g. `year=2024/month=03/day=11`); assert key contains that substring. | Key format is Hive-compatible for BigQuery/Spark discovery. |
| **Fallback used when field missing** | Sink with `partition_date_field`; call `_build_key_for_record` with a partition_path that came from fallback (e.g. from `get_partition_path_from_record(record_without_field, ..., date_fn())`); assert key contains fallback date segment. | Missing field does not crash; path uses fallback. |
| **Unset partition_date_field: key unchanged** | Sink without `partition_date_field`; assert `key_name` uses run date and single-key semantics (e.g. same as `test_key_name_includes_default_date_format_if_date_token_used`). No use of `_build_key_for_record` when option unset. | Backward compatibility. |

**Helper:** Use `build_sink(..., date_fn=..., time_fn=...)` for deterministic assertions. When testing `_build_key_for_record`, pass partition_path explicitly (partition resolution is tested in task 02).

---

## 4. Implementation Order

1. **Add tests** in `test_sinks.py`:
   - `test_build_key_for_record_differs_by_partition_path` — build sink with `partition_date_field`, `key_naming_convention` with `{partition_date}`; fixed `time_fn`/`date_fn`; assert `_build_key_for_record(record, "year=2024/month=01/day=01")` != `_build_key_for_record(record, "year=2024/month=02/day=01")`.
   - `test_build_key_for_record_includes_hive_style_partition_path` — one partition path `year=2024/month=03/day=11`; assert returned key contains that string.
   - `test_build_key_for_record_uses_fallback_when_partition_path_from_fallback` — sink with partition_date_field; partition_path from fallback (e.g. formatted from fixed date_fn); assert key contains the fallback date segment.
   - `test_key_name_unchanged_when_partition_date_field_unset` — same assertion as existing `test_key_name_includes_default_date_format_if_date_token_used` (sink without partition_date_field); confirm no regression.
2. **Run tests** — expect failures (no `_build_key_for_record` yet; key_name branch not added).
3. **Implement `_build_key_for_record`** in `sinks.py`:
   - Signature: `def _build_key_for_record(self, record: dict, partition_path: str) -> str`.
   - Use `key_prefix` and `key_naming_convention` (or default template); build format_map with `stream`, `partition_date`=partition_path, `timestamp` from `_time_fn` or `time.time`, `chunk_index` if `max_records_per_file` > 0. Apply same prefix/normalization as current `key_name`: `(key_prefix + "/" + base).replace("//", "/").lstrip("/")`.
   - Document: only used when partition_date_field is set; partition_path is pre-resolved (e.g. from get_partition_path_from_record).
4. **Update `key_name` property** in `sinks.py`:
   - When `config.get("partition_date_field")` is set: return `self._key_name` if non-empty (current key after a write), otherwise return a placeholder such as `""` or a convention so callers do not rely on a single key; when partition-by-field is on, write path uses `_build_key_for_record` in process_record (task 06).
   - When unset: keep existing block (recompute _key_name from stream, date, timestamp, chunk_index as today).
5. **Run tests** — all new and existing tests pass.
6. **Lint/format** per project rules (Ruff, mypy).

---

## 5. Validation Steps

- [ ] `test_build_key_for_record_differs_by_partition_path` passes.
- [ ] `test_build_key_for_record_includes_hive_style_partition_path` passes.
- [ ] `test_build_key_for_record_uses_fallback_when_partition_path_from_fallback` passes.
- [ ] `test_key_name_unchanged_when_partition_date_field_unset` (or equivalent) passes; all existing key_name tests pass without modification.
- [ ] Full test suite for `loaders/target-gcs` passes.
- [ ] Linter and type checker pass for `sinks.py` and `test_sinks.py`.

---

## 6. Documentation Updates

**This task:** Docstrings only. Add a short Google-style docstring for `_build_key_for_record` (builds key from key_prefix and key_naming_convention with stream, partition_date, timestamp, chunk_index; same normalization as key_name; used when partition_date_field is set). Update `key_name` property docstring to state that when partition_date_field is set, it returns the current key when available and callers needing per-record keys use `_build_key_for_record`. No README, AI context, or sample config changes in this task (task 08).
