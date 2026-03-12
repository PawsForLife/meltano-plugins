# Task Plan: 07 — Integration tests (partition key)

## Overview

This task adds **sink-level integration tests** in `test_partition_key_generation.py` to verify that the partition path resolved by the helper (using dateutil from Task 05) is correctly used when building the GCS key, and that unparseable partition field behaviour is observable at the sink. Tests use the existing `build_sink` helper and GCS mocks; assertions are black-box (key passed to `smart_open.open` or raised exception), not internal call counts or log lines.

**Scope:** Only test code in `loaders/target-gcs/tests/test_partition_key_generation.py`. No production code changes. Depends on Task 05 (partition_path uses dateutil); behaviour of the unparseable test depends on Task 06 (sink exception handling) if the helper raises.

---

## Files to Create/Modify

| File | Action | Changes |
|------|--------|--------|
| `loaders/target-gcs/tests/test_partition_key_generation.py` | Modify | Add one or more integration tests: (1) record with dateutil-parsable non-ISO partition field → key contains expected partition path segment; (2) if helper raises on unparseable: record with unparseable partition field → exception propagates or record not written. Use existing `build_sink`, `_key_from_open_call`, and `patch("target_gcs.sinks.Client")` / `patch("target_gcs.sinks.smart_open.open")`. Add clear docstrings (WHAT/WHY). |

No new files. No changes to `sinks.py`, `partition_path.py`, or docs in this task.

---

## Test Strategy

### Tests to add (TDD: tests are written for behaviour already implemented in Task 05 / 06)

1. **Dateutil-parsable non-ISO format → key contains partition path**
   - **What:** Build a sink with `partition_date_field` and a deterministic `date_fn`; feed a single record whose partition field is a **dateutil-parsable non-ISO string** (e.g. `"2024/03/11"` or `"11 Mar 2024"`). Call the code path that resolves the partition path and opens the handle (i.e. `process_record` with GCS mocks). Assert that the key passed to `smart_open.open` (via `_key_from_open_call(mock_open.call_args)`) contains the expected partition path segment (e.g. `year=2024/month=03/day=11`).
   - **Why:** Integration guarantee that the sink uses the helper output correctly for dateutil-only formats.
   - **Determinism:** Use fixed `time_fn` and `date_fn` (e.g. `FALLBACK_DATE`) and a convention that includes `{partition_date}` so the key is predictable. Use `key_naming_convention` that embeds `{partition_date}` (e.g. `"{partition_date}/{stream}_{timestamp}.jsonl"`).
   - **Valid test:** If the implementation did not parse the non-ISO string correctly, the key would contain the fallback date or wrong path → assertion fails.

2. **Unparseable partition field (conditional on Task 06 / product choice)**
   - **If** the helper raises on unparseable (e.g. `ParserError` or wrapper): add a test that feeds a record with an unparseable partition field (e.g. `"not-a-date"`) and assert that an exception propagates from the sink (e.g. `pytest.raises(...)` around `process_record`), **or** that the record is not written (e.g. only one record written before the bad one, then assert no additional `smart_open.open` call for the bad record, or assert exception). Prefer exception assertion for clarity; avoid asserting on internal call counts per black-box rules—prefer “exception raised” as the observable outcome.
   - **If** the product choice is “warning + fallback” and the helper never raises: omit this test or document in the test file that unparseable is covered at the helper level (Task 03); no sink-level “record not written” test required for this task.
   - **What:** Observable outcome is “exception” or “record not written”; no assertions on “called_once” or log content.
   - **Why:** Integration guarantee that unparseable input is visible (fail or skip), not silently written with wrong path.

### Test style (from master testing.md and development_practices)

- Black-box: assert on key string or raised exception only.
- Each test must be able to fail (wrong partition path or missing exception would fail).
- Use existing helpers: `build_sink`, `_key_from_open_call`, `FALLBACK_DATE`, `DEFAULT_HIVE_FORMAT` as needed.
- Docstrings: state WHAT (sink key contains partition from dateutil format; unparseable → exception or record not written) and WHY (integration guarantee).

---

## Implementation Order

1. **Add integration test: dateutil-parsable non-ISO → key contains partition path**
   - In `test_partition_key_generation.py`, add a test function (e.g. `test_sink_key_contains_partition_path_from_dateutil_parsable_format`).
   - Use `build_sink(config={"partition_date_field": "created_at", "partition_date_format": DEFAULT_HIVE_FORMAT, "key_naming_convention": ...}, time_fn=..., date_fn=lambda: FALLBACK_DATE)`.
   - Record: partition field = dateutil-parsable non-ISO string (e.g. `"2024/03/11"` or `"11 Mar 2024"`); include enough keys for stream if schema requires.
   - Patch `Client` and `smart_open.open`; call `sink.process_record(record, {})`.
   - Get key from first (or only) `smart_open.open` call via `_key_from_open_call(mock_open.call_args)` (or from `call_args_list[0]`).
   - Assert that the expected partition path segment (e.g. `year=2024/month=03/day=11`) is contained in the key.
   - Add docstring: WHAT/WHY as above.

2. **Add integration test: unparseable partition field (if applicable)**
   - If Task 06 implements “raise on unparseable”: add test (e.g. `test_sink_raises_or_skips_record_when_partition_field_unparseable`) that builds sink with `partition_date_field`, feeds record with unparseable value (e.g. `"not-a-date"`), and uses `pytest.raises(ExpectedException)` around `process_record`, or asserts that no write occurred for that record (observable: exception or number of open calls). Prefer exception test.
   - If “warning + fallback”: skip this test; optionally add a short comment in the file that unparseable is covered in helper tests (Task 03).

3. **Run tests and regression gate**
   - Run `uv run pytest loaders/target-gcs/tests/test_partition_key_generation.py` from the target-gcs directory (with venv active). All existing tests must still pass; new tests must pass with Task 05 (and 06) implementation.

---

## Validation Steps

- [ ] New test(s) exist in `test_partition_key_generation.py` with clear WHAT/WHY docstrings.
- [ ] Test for dateutil-parsable non-ISO: uses `process_record` (or equivalent code path that builds key via helper); asserts key from `smart_open.open` contains expected partition path segment (e.g. `year=2024/month=03/day=11`); uses deterministic `date_fn`/`time_fn` and config.
- [ ] If “raise on unparseable”: test for unparseable partition field asserts exception or observable “record not written”; no assertions on internal call counts or log lines.
- [ ] Full test suite for target-gcs passes: `uv run pytest` in `loaders/target-gcs/` (no regressions).
- [ ] Lint/format: `uv run ruff check .` and `uv run ruff format --check` pass in `loaders/target-gcs/`.

---

## Documentation Updates

- **None** for this task. Docstrings in the new tests are the only documentation added; no changes to `docs/AI_CONTEXT/` or README in Task 07 (documentation is Task 08).

---

## Dependencies

- **Task 05 (implement partition_path dateutil):** Must be complete so that a non-ISO dateutil-parsable string is actually parsed and the correct partition path is returned; otherwise the new integration test would fail for the wrong reason or pass only by fallback.
- **Task 06 (sink exception handling):** Determines whether the “unparseable” integration test is added (raise) or skipped (warning + fallback). If Task 06 is not yet implemented, implementer may add the unparseable test conditioned on “if helper raises” (e.g. document in plan or test that the test is valid once Task 06 is done).

---

## References

- Task doc: `_features/dateutils-partition-timestamps/tasks/07-integration-tests-partition-key.md`
- Master plan: `_features/dateutils-partition-timestamps/plans/master/implementation.md` (Step 5), `testing.md` (sink integration cases)
- Existing tests: `loaders/target-gcs/tests/test_partition_key_generation.py` — `test_partition_change_then_return_creates_three_distinct_keys`, `test_chunking_with_partition_rotation_within_partition`, `_key_from_open_call`, `build_sink`
