# Testing: target-gcs-dedup-split-logic

## Strategy

- **Regression:** Full target-gcs test suite must pass after each change. No behaviour change; existing tests are the regression gate.
- **TDD:** For new surface (e.g. `_apply_key_prefix_and_normalize` edge cases, `_assert_field_required_and_non_null_type`), write failing tests first, then implement until they pass.
- **Black-box:** Assert on observable behaviour (returned keys, written payloads, raised exceptions). Do not assert on call counts, “called_once”, or log output (per `development_practices.mdc`).

## Tests to Run

- From `loaders/target-gcs/`: `uv run pytest` (or project script). All tests must pass except explicitly marked xfail.

## New or Updated Tests

Add or extend tests only where new helpers are not fully covered by existing tests:

1. **`_apply_key_prefix_and_normalize`:** If existing tests (e.g. key naming in `test_sinks.py`, `test_partition_key_generation.py`) already assert on final key strings for various `key_prefix` and base values, no new test may be needed. If edge cases (empty prefix, double slash, leading slash) are not covered, add unit tests that build a sink and assert on the resulting key (e.g. via `key_name` or `_build_key_for_record`) for those inputs; prefer testing via public behaviour rather than calling the private method directly unless the team prefers direct unit tests for pure helpers.
2. **`_assert_field_required_and_non_null_type`:** Existing `test_partition_schema.py` (and sink-init tests in `test_sinks.py`) already validate schema validation behaviour. Refactor validators to call the new helper; re-run existing tests. If the helper is module-private and all branches are exercised by existing validator tests, no new test file is required. If a branch (e.g. “required is not a list”) is not covered, add a test that expects `ValueError` with appropriate message (e.g. `pytest.raises(ValueError)` and assert on message content or stream/field name).

## Integration

- Chunking, hive partitioning, and record write behaviour are already covered by `test_sinks.py` and `test_partition_key_generation.py`. After refactor, same assertions (key format, written lines, rotation) must still pass.
- No new integration tests are required unless a new code path is introduced that is not exercised by existing tests.

## Validation Steps

1. Run `uv run pytest` in `loaders/target-gcs/`; all tests pass.
2. Run `uv run ruff check .` and `uv run ruff format --check` and `uv run mypy target_gcs`; no new issues.
3. Optionally run full repo checks via `./scripts/run_plugin_checks.sh` from repo root.
