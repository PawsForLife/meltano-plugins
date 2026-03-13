# Pipeline Scratchpad

## Feature: target-gcs-extraction-patterns

**Pipeline State:** Phase 3–4 Complete. Phase 5 In progress. Phase 6 Not started. Task Completion Status: 01-create-base-pattern, 02-base-rotation-and-write, 03-implement-simple-sink, 04-implement-dated-sink, 05-implement-partitioned-sink completed. Execution Order: see below.

### Phase 1 (Research) summary:

- **Feature name:** target-gcs-extraction-patterns
- **Output directory:** `_features/target-gcs-extraction-patterns/planning/`
- **Key findings:**
  - **Impacted:** `target_gcs/sinks.py` (GCSSink) refactors to delegate to a chosen path pattern; `paths/simple.py`, `dated.py`, `partitioned.py` are implemented; shared plumbing (key prefix, serialization, rotation, `-{idx}`) in `paths/base.py` (BasePathPattern). Helpers `partition_path.py` and others unchanged; `target.py` unchanged. Tests extended for pattern-level behaviour; existing tests remain regression gate.
  - **New systems:** Path pattern interface (BasePathPattern); shared plumbing in paths/base; SimplePath, DatedPath, PartitionedPath implementations; pattern selection in GCSSink from config + schema (no new config); GCSSink as delegator.
  - **External vs internal:** No library provides Singer target GCS extraction patterns or our key template + partition semantics (PyArrow HivePartitioning is for reading; gcspathlib is path manipulation only). Internal solution chosen.
- **Selected solution:** Internal implementation. Base class in `paths/base.py` (BasePathPattern) for key prefix, effective template, JSONL write, rotation at limit, and `-{idx}`. SimplePath (single path, one handle), DatedPath (extraction-date partition), PartitionedPath (schema x-partition-fields, validation at init, handle on partition change). GCSSink selects pattern by: `hive_partitioned` false/unset → SimplePath; true + non-empty `x-partition-fields` → PartitionedPath; true + no/empty → DatedPath. Same config and key shapes; backward compatible.

### Phase 2 (Plan) summary:

- **Plan location:** `_features/target-gcs-extraction-patterns/plans/master/`
- **Plan documents:** overview.md, architecture.md, interfaces.md, implementation.md, testing.md, dependencies.md, documentation.md
- **Key decisions:**
  - **Base class (not protocol):** Use an abstract base class in `paths/base.py` (BasePathPattern) to hold shared key prefix, template, JSONL write, rotation, and flush/close. Subclasses implement key building and handle lifecycle. This avoids duplication and keeps key/rotation behaviour consistent; GCSSink holds the base type and delegates.
  - **File layout:** Base and pattern classes in `paths/base.py`, `paths/simple.py`, `paths/dated.py`, `paths/partitioned.py`. GCSSink remains in `sinks.py` and imports path pattern classes from `target_gcs.paths`.
  - **Selection in GCSSink.__init__:** Pattern chosen once in constructor from config + schema; no factory function required unless later preferred. Same injectables (time_fn, date_fn, storage_client) passed from GCSSink into pattern constructors.
  - **key_name:** Retain for tests; delegate to pattern’s “current key” so existing tests that assert on key_name continue to work.
- **Prerequisites for next step:** Task decomposition (Phase 3) can use the implementation order in implementation.md and the test strategy in testing.md to produce prioritized tasks.

### Phase 3 (Task List) summary:

- **Tasks directory:** `_features/target-gcs-extraction-patterns/tasks/`
- **Task count:** 8
- **Task list file:** `_features/target-gcs-extraction-patterns/target-gcs-extraction-patterns-task-list.md`
- **Execution order (for Phase 5 implement-feature):**
  1. `01-create-base-pattern.md`
  2. `02-base-rotation-and-write.md`
  3. `03-implement-simple-sink.md`
  4. `04-implement-dated-sink.md`
  5. `05-implement-partitioned-sink.md`
  6. `06-gcssink-refactor-delegate.md`
  7. `07-wire-exports.md`
  8. `08-regression-and-documentation.md`

- Task plan created: 02-base-rotation-and-write at plans/tasks/02-base-rotation-and-write.md

- Task plan created: 01-create-base-pattern at plans/tasks/01-create-base-pattern.md
- Task plan created: 03-implement-simple-sink at plans/tasks/03-implement-simple-sink.md
- Task plan created: 04-implement-dated-sink at plans/tasks/04-implement-dated-sink.md
- Task plan created: 05-implement-partitioned-sink at plans/tasks/05-implement-partitioned-sink.md
- Task plan created: 06-gcssink-refactor-delegate at plans/tasks/06-gcssink-refactor-delegate.md
- Task plan created: 07-wire-exports at plans/tasks/07-wire-exports.md
- Task plan created: 08-regression-and-documentation at plans/tasks/08-regression-and-documentation.md

- Task 01-create-base-pattern completed, tests passing.
- Task 02-base-rotation-and-write completed, tests passing.
- Task 03-implement-simple-sink completed, tests passing.
- Task 04-implement-dated-sink completed, tests passing.
- Task 05-implement-partitioned-sink completed, tests passing.
- Task 06-gcssink-refactor-delegate completed, tests passing.

---

## Redundant tests in target-gcs (2025-03-13)

**Scope:** loaders/target-gcs tests only. No feature file; direct analysis.

**Findings:**

1. **Duplicate "valid hive schema constructs" (test_sinks.py)**
   - `test_sink_init_hive_partitioned_valid_x_partition_fields_succeeds` and `test_hive_partitioned_valid_schema_constructs_successfully` both: build_sink with hive_partitioned true and valid x-partition-fields (field in properties + required), assert sink constructs (e.g. stream_name).
   - **Action:** Remove one (e.g. the first); keep `test_hive_partitioned_valid_schema_constructs_successfully`.

2. **Duplicate "fallback date in key when no x-partition-fields" (test_sinks vs test_partition_key_generation)**
   - `test_sinks.test_hive_partitioned_true_no_x_partition_fields_key_contains_fallback_date` and `test_partition_key_generation.test_hive_partitioned_true_without_x_partition_fields_key_contains_fallback_date` both: hive_partitioned true, schema with no x-partition-fields, date_fn, assert key contains year=2024/month=03/day=11.
   - **Action:** Remove the one in test_partition_key_generation; keep the integration test in test_sinks.

**Not redundant (keep):**
- Unit tests in `test_partition_schema.py` vs sink-init validation in `test_sinks.py`: different levels (unit vs integration); both useful.
- Decimal/JSON: helper tests in `test_json_parsing.py` vs sink tests in `test_sinks.py`: unit vs integration.
- Duplicate helpers `build_sink` / `_key_from_open_call` in test_sinks and test_partition_key_generation: duplication of helpers, not of test cases; consolidation could be a separate refactor.
