# Task 07: Add _init_hive_partitioning and refactor __init__ hive branch

## Background

The hive-partitioned branch in `GCSSink.__init__` sets `_current_partition_path = None`, reads `x_partition_fields`, and validates schema when the list is non-empty. This task moves that logic into `_init_hive_partitioning` and refactors `__init__` so the hive branch only calls `self._init_hive_partitioning()`. No dependency on tasks 04–06 for this method; can follow task 06 in execution order.

## This Task

- In `loaders/target-gcs/target_gcs/sinks.py`:
  - Implement `_init_hive_partitioning(self) -> None`: set `self._current_partition_path = None`; get `x_partition_fields` from config (or schema metadata as today); if it is a list and non-empty, call `validate_partition_fields_schema(self.stream_name, self.schema, x_partition_fields)`. Only call this method when `hive_partitioned` is true (caller responsibility in `__init__`).
  - Refactor `__init__`: in the hive_partitioned branch, replace the inline block with a single call to `self._init_hive_partitioning()`.
- Add a Google-style docstring for `_init_hive_partitioning` (purpose, no Args/Returns; note that it assumes hive_partitioned is true).

**Acceptance criteria:** Hive init logic lives in `_init_hive_partitioning`; `__init__` hive branch is a single method call; sink construction and schema validation behaviour unchanged.

## Testing Needed

- No new tests; existing sink-init and hive schema validation tests cover this. Run full target-gcs test suite to confirm regression gate passes.
