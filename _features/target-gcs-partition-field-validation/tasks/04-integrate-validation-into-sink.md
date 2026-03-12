# Background

The validation helper is implemented and tested. The sink must invoke it during initialization when `partition_date_field` is set, so that misconfiguration is caught before any records are processed.

**Dependencies:** Task 02 (validation helper implemented and exported), Task 03 (sink integration tests added). This task wires the helper into `GCSSink.__init__` so that the integration tests pass.

# This Task

- **File:** `loaders/target-gcs/target_gcs/sinks.py`.
- **Import:** Add import for `validate_partition_date_field_schema` from `target_gcs.helpers` (or `.helpers.partition_schema` depending on where it was exported in task 02).
- **Call site:** In `GCSSink.__init__`, after `super().__init__(...)` and after the block that sets `_current_partition_path` when `partition_date_field` is set (i.e. after the `if self.config.get("partition_date_field"): self._current_partition_path = None` block), add:
  - If `self.config.get("partition_date_field")`: call `validate_partition_date_field_schema(self.stream_name, self.config["partition_date_field"], self.schema)`.
- Add a short comment at the call site: e.g. "Validate partition_date_field against stream schema when set; raises ValueError if missing or not date-parseable."
- **No other changes:** Do not modify `process_record`, `_build_key_for_record`, or other methods; only add the validation call in `__init__`.

**Acceptance criteria:** All tests in `tests/helpers/test_partition_schema.py` and the new tests in `tests/test_sinks.py` pass. Existing tests in `tests/test_sinks.py` and elsewhere continue to pass (no regression). Ruff and mypy pass.

# Testing Needed

- Run `uv run pytest tests/helpers/test_partition_schema.py tests/test_sinks.py -v` — all tests pass.
- Run full target-gcs suite: `uv run pytest` from `loaders/target-gcs/` — no new failures (excluding explicitly xfail).
- Run `uv run ruff check .`, `uv run ruff format --check`, `uv run mypy target_gcs`.
