# Task Plan: 07-add-init-hive-partitioning

## Overview

This task moves the hive-partitioned initialization logic from `GCSSink.__init__` into a dedicated private method `_init_hive_partitioning(self) -> None` and refactors the `__init__` hive branch to a single call. Behaviour is unchanged: `_current_partition_path` is set to `None`, `x_partition_fields` is read from schema metadata, and when it is a non-empty list, `validate_partition_fields_schema` is invoked. The method is only called when `hive_partitioned` is true (caller responsibility in `__init__`).

**Feature context:** Part of target-gcs-dedup-split-logic (split switch logic into named functions). See [master implementation.md](../master/implementation.md) step 7 and [interfaces.md](../master/interfaces.md) (`_init_hive_partitioning`).

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/sinks.py` | Add `_init_hive_partitioning`; refactor `__init__` hive branch to call it. |

**No new files.** No changes to helpers, target.py, or test files (other than running the existing suite).

### sinks.py — Specific changes

1. **Add `_init_hive_partitioning`** (place after common `__init__` setup, before `_get_effective_key_template` or in a logical init/partitioning block):
   - Signature: `def _init_hive_partitioning(self) -> None`
   - Body: Set `self._current_partition_path = None`; get `x_partition_fields = self.schema.get("x-partition-fields")`; if `isinstance(x_partition_fields, list) and len(x_partition_fields) > 0`, call `validate_partition_fields_schema(self.stream_name, self.schema, x_partition_fields)`.
   - Docstring: Google-style; purpose (initialize hive partitioning state and validate partition fields schema when x-partition-fields is present). Note that the method assumes `hive_partitioned` is true; no Args/Returns.

2. **Refactor `__init__`**:
   - In the `if self.config.get("hive_partitioned"):` branch, replace the current inline block (assignment to `_current_partition_path`, read `x_partition_fields`, conditional `validate_partition_fields_schema` call) with a single call: `self._init_hive_partitioning()`.

## Test Strategy

- **No new tests.** The task document and master testing plan state that existing sink-init and hive schema validation tests cover this path. Regression is verified by running the full target-gcs test suite.
- **TDD:** Not applicable—pure refactor; observable behaviour (sink construction, schema validation on init) is unchanged; existing tests in `test_sinks.py` (and any partition-schema integration via sink init) remain the regression gate.

## Implementation Order

1. Implement `_init_hive_partitioning(self) -> None` with the logic moved from the hive branch of `__init__`: set `_current_partition_path = None`, read `x_partition_fields` from `self.schema.get("x-partition-fields")`, and when it is a list and non-empty, call `validate_partition_fields_schema(self.stream_name, self.schema, x_partition_fields)`. Add a Google-style docstring (purpose; note that caller must only invoke when `hive_partitioned` is true).
2. In `__init__`, replace the hive branch body with `self._init_hive_partitioning()`.
3. Run the full target-gcs test suite to confirm no regressions.

## Validation Steps

1. **Tests:** From `loaders/target-gcs/`, run `uv run pytest`. All tests must pass.
2. **Linting/formatting:** Run `uv run ruff check target_gcs` and `uv run ruff format --check target_gcs`. Resolve any issues in modified files.
3. **Type check:** Run `uv run mypy target_gcs`; no new errors in `sinks.py`.
4. **Behaviour:** Sink construction with `hive_partitioned=True` and valid or invalid `x-partition-fields` must behave as before (e.g. `test_hive_partitioned_valid_schema_constructs_successfully`, schema validation failures on init). Confirm no behaviour change.

## Documentation Updates

- **Code:** Add a Google-style docstring for `_init_hive_partitioning` only. No README or external docs change.
- **AI context:** No update required for this task; task 09 may refresh component docs.
