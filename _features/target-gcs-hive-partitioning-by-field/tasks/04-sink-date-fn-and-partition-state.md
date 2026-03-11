# Background

The sink must support an injectable run-date (and already has `time_fn` for timestamp). Adding `date_fn` and `_current_partition_path` enables deterministic tests and the handle lifecycle: on partition change the sink closes the handle and clears state; the next write builds a new key (optionally for the same partition value—new file). This task extends constructor and state only; key building and process_record logic follow in later tasks.

**Dependencies:** Task 01 (config schema), Task 03 (partition resolution). Partition state is only relevant when `partition_date_field` is set.

**Plan reference:** `plans/master/interfaces.md` (GCSSink constructor and state), `plans/master/architecture.md` (Sink state).

---

# This Task

- **File:** `loaders/target-gcs/gcs_target/sinks.py`
- **Constructor:** Add optional `date_fn: Optional[Callable[[], datetime]] = None` to `GCSSink.__init__`. Store as `self._date_fn`. When not provided, callers will use `datetime.today` where run date is needed (e.g. partition fallback and run-date token when partition-by-field is off).
- **State when partition-by-field is on:** When `config.get("partition_date_field")` is truthy, initialise `_current_partition_path: Optional[str] = None`. When option is unset, this attribute need not exist or may remain None; ensure no code path assumes it exists when option is unset.
- **File:** `loaders/target-gcs/tests/test_sinks.py`
- Extend `build_sink` to accept `date_fn: Optional[Callable[[], datetime]] = None` and pass it to `GCSSink`.
- **Acceptance criteria:** Sink instantiates with `date_fn`; when config includes `partition_date_field`, sink has `_current_partition_path` (None initially). Existing tests that use `build_sink` still pass (backward compatible).

---

# Testing Needed

- **build_sink accepts date_fn:** Build sink with `date_fn=lambda: datetime(2024, 3, 11)`; assert sink has `_date_fn` and calling it returns the fixed date. **WHAT:** date_fn is injectable. **WHY:** Deterministic tests for fallback and key names.
- **Sink has _current_partition_path when partition_date_field set:** Build sink with config containing `partition_date_field` (e.g. `"created_at"`); assert `_current_partition_path` is present and None. **WHAT:** Partition state exists when feature enabled. **WHY:** Handle lifecycle relies on this state.
- **Existing tests still pass:** All current tests in test_sinks.py that do not set `partition_date_field` continue to pass. **WHAT:** No regression. **WHY:** Regression gate.
