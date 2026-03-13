# Pipeline Scratchpad

## Feature: split-path-filename

**Pipeline State:**
- Phase 1: Research — Complete
- Phase 2: Plan — Complete
- Phase 3: Complete
- Phase 4: Complete
- Phase 5: Not started
- Phase 6: Not started

**Task Completion Status:** Phase 1 (Research) complete. Phase 2 (Plan) complete. Phase 3 (Task List) complete.

**Output Directory:** `_features/split-path-filename/planning/`

**Plan Location:** `_features/split-path-filename/plans/master/`

**Tasks Directory:** `_features/split-path-filename/tasks/`

**Task Count:** 10

**Task plan created:** 01-update-constants at plans/tasks/01-update-constants.md

**Task plan created:** 02-fix-date-as-partition at plans/tasks/02-fix-date-as-partition.md

**Execution Order:** `01-update-constants.md`, `02-fix-date-as-partition.md`, `03-remove-key-naming-config.md`, `04-basepathpattern-add-methods.md`, `05-simplepath.md`, `06-datedpath.md`, `07-partitionedpath.md`, `08-sinks-config-wiring.md`, `09-helpers-cleanup.md`, `10-documentation.md`

Task plan created: 03-remove-key-naming-config at plans/tasks/03-remove-key-naming-config.md

### Key Findings

- **Impacted systems:** `constants.py`, `target.py`, `paths/base.py`, `paths/simple.py`, `paths/dated.py`, `paths/partitioned.py`, `paths/__init__.py`, `helpers/partition_path.py`; config schema; `meltano.yml`, README, AI context docs; all path and sink unit tests.
- **New systems:** Constants `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`; `BasePathPattern.filename_for_current_file()`, `full_key(path, filename)`; timestamp-only chunking (no `chunk_index`).
- **External libraries:** Researched `google.api_core.path_template`, PyArrow HivePartitioning, Jinja2. None suitable; internal `str.format()` solution selected.
- **Selected solution:** Internal refactor using path + filename constants; `str.format()` for token expansion; `hive_path(record)` for PartitionedPath; `get_partition_path_from_schema_and_record` replaced by `hive_path(record)` for key building. Verify `_partitioned.date_as_partition` returns value (current code may have missing return).

### Key Decisions (Phase 2)

- **Constants:** Path and filename split in `constants.py`; `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`; remove `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`.
- **BasePathPattern:** Add `filename_for_current_file()`, `full_key(path, filename)`; remove `key_template`, `get_chunk_format_map`, `_chunk_index`; chunking uses timestamp only.
- **PartitionedPath:** Use `path_for_record(record)` with `hive_path(record)` from `_partitioned`; partition change = compare path outputs; remove `get_partition_path_from_schema_and_record` for key building.
- **Pre-existing bug:** Fix `date_as_partition` in `_partitioned` to return formatted string.
- **Implementation order:** Constants → fix date_as_partition → remove config → BasePathPattern → SimplePath → DatedPath → PartitionedPath → sinks/config → helpers cleanup.
- **TDD:** Tests before implementation per step; black-box style; test path mirrors source under `tests/unit/`.

Task plan created: 04-basepathpattern-add-methods at plans/tasks/04-basepathpattern-add-methods.md

Task plan created: 07-partitionedpath at plans/tasks/07-partitionedpath.md

Task plan created: 08-sinks-config-wiring at plans/tasks/08-sinks-config-wiring.md

Task plan created: 06-datedpath at plans/tasks/06-datedpath.md

Task plan created: 05-simplepath at plans/tasks/05-simplepath.md

Task plan created: 09-helpers-cleanup at plans/tasks/09-helpers-cleanup.md

Task plan created: 10-documentation at plans/tasks/10-documentation.md

Task 01-update-constants completed, tests passing

Task 02-fix-date-as-partition completed, tests passing

Task 03-remove-key-naming-config completed, tests passing

Task 04-basepathpattern-add-methods completed, tests passing
