# Task Plan: 03-sink-integration-tests

## Overview

This task adds **sink-level integration tests** for partition-date-field schema validation. Tests construct `GCSSink` with config (including optional `partition_date_field`) and a given stream schema; they assert that constructing the sink raises `ValueError` when the partition field is invalid (missing, null-only, or non–date-parseable type) and does not raise when valid or when `partition_date_field` is unset. The validation logic is **not** implemented in this task; it is wired in task 04. Per TDD, these tests are written first and will fail (no exception where `ValueError` is expected) until task 04 integrates the helper into the sink.

**Scope:** Tests and test helper only. No production code in `target_gcs/` is modified. Depends on task 02 (validation helper implemented and importable).

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/test_sinks.py` | **Modify.** Extend `build_sink` to accept optional `schema` and `stream_name`; add five (or six) new test functions for partition-date-field validation at sink construction. |

**No other files** are created or modified. Sink integration (calling the helper in `GCSSink.__init__`) is done in task 04.

---

## Test Strategy

### Test helper extension

- **Current:** `build_sink(config=None, time_fn=None, date_fn=None, storage_client=None)` builds `GCSSink(GCSTarget(config=...), "my_stream", {"properties": {}}, key_properties=config, **kwargs)`.
- **Extended:** Add optional parameters `schema=None` and `stream_name=None`. When `schema` is `None`, use `{"properties": {}}`. When `stream_name` is `None`, use `"my_stream"`. Preserve existing behaviour for all current call sites (defaults keep current defaults). This allows tests to pass arbitrary schemas and stream names without changing existing tests.

### Test cases (from master testing.md and task doc)

| # | Scenario | Config | Schema | Expected |
|---|----------|--------|--------|----------|
| 1 | partition_date_field set, field missing | `partition_date_field: "dt"` | `{"properties": {"id": {}}}` | `ValueError` when constructing sink. |
| 2 | partition_date_field set, field null-only | `partition_date_field: "dt"` | `{"properties": {"dt": {"type": "null"}}}` | `ValueError` when constructing sink. |
| 3 | partition_date_field set, field integer | `partition_date_field: "dt"` | `{"properties": {"dt": {"type": "integer"}}}` | `ValueError` when constructing sink. |
| 4 | partition_date_field set, field string (valid) | `partition_date_field: "dt"` | `{"properties": {"dt": {"type": "string"}}}` | Sink constructs successfully (no exception). |
| 5 | partition_date_field not set | no `partition_date_field` | any schema (e.g. `{"properties": {"id": {}}}`) | Sink constructs successfully; no regression. |

**Optional (6):** One test that the raised `ValueError` message includes the stream name and the field name (e.g. parse message and assert substrings or use `match=` in `pytest.raises`).

### Assertion style

- **Failure cases (1–3):** Use `with pytest.raises(ValueError): build_sink(config=..., schema=...)`. Do **not** assert on log lines or call counts (black-box).
- **Success cases (4–5):** Call `build_sink(...)`; no exception. Optionally assert the returned sink has expected attributes (e.g. `subject.stream_name`) to ensure construction completed.
- **Optional message test:** `with pytest.raises(ValueError, match=...)` or assert that `str(exc_info.value)` contains stream name and field name.

### Documentation per test

- Each test has a brief docstring stating **what** is being tested and **why** (e.g. "partition_date_field set with field missing in schema must raise ValueError so users get a clear config error at init.")

---

## Implementation Order

1. **Extend `build_sink`**  
   In `loaders/target-gcs/tests/test_sinks.py`, add optional parameters `schema=None` and `stream_name=None` to `build_sink`. When `schema is None`, use `{"properties": {}}`. When `stream_name is None`, use `"my_stream"`. Merge into the `GCSSink(...)` call so existing call sites remain unchanged.

2. **Add test: partition_date_field set, field missing**  
   Test that `build_sink(config={"partition_date_field": "dt"}, schema={"properties": {"id": {}}})` raises `ValueError`. Docstring: what and why.

3. **Add test: partition_date_field set, field null-only**  
   Test that `build_sink(config={"partition_date_field": "dt"}, schema={"properties": {"dt": {"type": "null"}}})` raises `ValueError`.

4. **Add test: partition_date_field set, field integer**  
   Test that `build_sink(config={"partition_date_field": "dt"}, schema={"properties": {"dt": {"type": "integer"}}})` raises `ValueError`.

5. **Add test: partition_date_field set, field string (valid)**  
   Test that `build_sink(config={"partition_date_field": "dt"}, schema={"properties": {"dt": {"type": "string"}}})` does not raise; sink constructs successfully.

6. **Add test: partition_date_field not set**  
   Test that `build_sink(config={}, schema={"properties": {"id": {}}})` (or equivalent) does not raise; no regression when option is unset.

7. **Optional: Add test for ValueError message content**  
   One test that when `ValueError` is raised (e.g. field missing), the exception message includes the stream name and the field name (e.g. `"my_stream"` and `"dt"` if using default stream name, or use a distinct stream_name in build_sink for clarity).

8. **Run tests**  
   From `loaders/target-gcs/`: `uv run pytest tests/test_sinks.py -v`. Until task 04, tests 1–3 will fail (no ValueError raised). Tests 4–5 may pass or fail depending on current sink behaviour. After task 04, all must pass.

9. **Lint and format**  
   Run `uv run ruff check .` and `uv run ruff format --check` from `loaders/target-gcs/`; fix any issues.

---

## Validation Steps

- [ ] `build_sink` accepts optional `schema` and `stream_name` with the documented defaults; existing tests in `test_sinks.py` still pass without change.
- [ ] Five scenarios (field missing, null-only, integer, valid string, partition_date_field not set) each have a dedicated test.
- [ ] Failure tests (1–3) use `pytest.raises(ValueError)` and do not assert on log or call counts.
- [ ] Success tests (4–5) assert sink construction succeeds (no exception).
- [ ] Optional: One test asserts that the raised `ValueError` message includes stream name and field name.
- [ ] Each new test has a brief docstring stating what is tested and why.
- [ ] From `loaders/target-gcs/`, `uv run pytest tests/test_sinks.py -v` runs; after task 04, all new tests pass.
- [ ] `uv run ruff check .` and `uv run ruff format --check` pass.

**Acceptance:** Sink-level integration tests are in place and runnable. Tests that expect `ValueError` will fail until task 04 adds the validation call in the sink; the valid and no-config cases may pass or fail depending on current sink behaviour.

---

## Documentation Updates

- **None** for this task. No user-facing docs or AI context changes are required. Component docs will be updated in task 05 if needed.
