# Task Plan: 04-sink-date-fn-and-partition-state

**Feature:** target-gcs-hive-partitioning-by-field  
**Task:** Add injectable `date_fn` to GCSSink and partition state `_current_partition_path` when partition-by-field is enabled.  
**Master plan:** [../master/overview.md](../master/overview.md), [../master/implementation.md](../master/implementation.md), [../master/interfaces.md](../master/interfaces.md), [../master/architecture.md](../master/architecture.md), [../master/testing.md](../master/testing.md)

---

## 1. Overview

This task extends the sink constructor and internal state only: it adds an optional `date_fn` for deterministic run-date (e.g. partition fallback and tests) and initialises `_current_partition_path` when `partition_date_field` is set. Key building, handle lifecycle, and `process_record` logic are **not** changed in this task; they depend on task 03 (partition resolution) and are implemented in tasks 05 and 06. Success means: the sink accepts `date_fn`, stores it, and when config includes `partition_date_field` the sink has `_current_partition_path` set to `None`; the test helper `build_sink` accepts and passes `date_fn`; all existing tests still pass.

**Scope:** Constructor and state only. No `_build_key_for_record`, no changes to `process_record` or handle lifecycle.

**Dependencies:** Task 01 (config schema) and Task 03 (partition resolution) must be done so config has `partition_date_field` / `partition_date_format` and `get_partition_path_from_record` exists. This task does not call the partition-resolution function yet.

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `loaders/target-gcs/gcs_target/sinks.py` | Modify | Add optional `date_fn: Optional[Callable[[], datetime]] = None` to `GCSSink.__init__`; store as `self._date_fn`. When `config.get("partition_date_field")` is truthy, set `self._current_partition_path: Optional[str] = None`. When unset, do not set the attribute (or leave it unset) so no code assumes it exists when the option is off. Ensure `datetime` is in scope for the type hint (already imported). |
| `loaders/target-gcs/tests/test_sinks.py` | Modify | Extend `build_sink` to accept `date_fn: Optional[Callable[[], datetime]] = None` and pass it to `GCSSink` when provided. Add tests: sink stores and uses `date_fn`; sink has `_current_partition_path` when `partition_date_field` is set; existing tests still pass. |

No new files.

---

## 3. Test Strategy

TDD: add tests first, then implement constructor/state and `build_sink` so tests pass.

**Location:** `loaders/target-gcs/tests/test_sinks.py`.

| Test | What | Why |
|------|------|-----|
| **build_sink accepts date_fn** | Build sink with `date_fn=lambda: datetime(2024, 3, 11)`; assert sink has `_date_fn` and calling it returns that date. | Confirms date_fn is injectable for deterministic tests (fallback and key names in later tasks). |
| **Sink has _current_partition_path when partition_date_field set** | Build sink with config containing `partition_date_field` (e.g. `"created_at"`); assert `_current_partition_path` is present and is `None`. | Partition state exists when feature is enabled; handle lifecycle (later tasks) relies on it. |
| **Existing tests still pass** | Run full `test_sinks.py` suite without setting `partition_date_field` or `date_fn` in existing tests. | Regression gate; no behaviour change when option unset. |

Black box: assert on stored attributes and return value of `_date_fn()`, not on call counts or logs. Do not add tests that require key building or `process_record` partition logic (those are tasks 05/06).

---

## 4. Implementation Order

1. **Add tests** in `test_sinks.py`:
   - `test_sink_accepts_date_fn_and_stores_it` — `build_sink(date_fn=lambda: datetime(2024, 3, 11))`; assert `sink._date_fn` is not None and `sink._date_fn() == datetime(2024, 3, 11)`.
   - `test_sink_has_current_partition_path_when_partition_date_field_set` — `build_sink(config={"partition_date_field": "created_at"})`; assert `hasattr(sink, "_current_partition_path")` and `sink._current_partition_path is None`.
2. **Run tests** — expect failures (constructor and build_sink do not support date_fn / partition state yet).
3. **Implement in `sinks.py`:**
   - Add `date_fn: Optional[Callable[[], datetime]] = None` to `__init__` (after `time_fn`). Store as `self._date_fn = date_fn`.
   - After existing state initialisation, if `self.config.get("partition_date_field")`: set `self._current_partition_path: Optional[str] = None`. Otherwise do not set the attribute (so code that checks partition-by-field via config does not assume it exists).
4. **Extend `build_sink`** in `test_sinks.py`: add parameter `date_fn=None`; if `date_fn is not None`, pass `date_fn=date_fn` into `GCSSink(...)`.
5. **Run tests** — all new and existing tests pass.
6. **Lint/format** per project rules (e.g. Ruff).

---

## 5. Validation Steps

- [ ] `test_sink_accepts_date_fn_and_stores_it` and `test_sink_has_current_partition_path_when_partition_date_field_set` pass.
- [ ] All existing tests in `test_sinks.py` pass without modification (no regression).
- [ ] Full test suite for `loaders/target-gcs` passes.
- [ ] Linter/type checker passes for `sinks.py` and `test_sinks.py`.
- [ ] When `partition_date_field` is unset, sink does not require `_current_partition_path` to exist (no AttributeError in existing code paths).

---

## 6. Documentation Updates

**This task:** No README, AI context, or sample config changes. Docstrings: add a short line in `GCSSink.__init__` documenting `date_fn` (e.g. optional run-date callable for partition fallback and tests; default None → use `datetime.today` where needed). Optionally document `_current_partition_path` in a single line (current partition path when partition-by-field is on; None when cleared or not yet set). Keep docstrings concise per project rules.
