# Task List — split-path-filename

## Overview

Split path and filename logic for target-gcs: replace config-driven `key_naming_convention` with fixed constants. TDD throughout; models and interfaces first.

## Execution Order

| # | Task | Dependencies |
|---|------|--------------|
| 01 | [01-update-constants.md](split-path-filename/tasks/01-update-constants.md) | — |
| 02 | [02-fix-date-as-partition.md](split-path-filename/tasks/02-fix-date-as-partition.md) | 01 |
| 03 | [03-remove-key-naming-config.md](split-path-filename/tasks/03-remove-key-naming-config.md) | 01 |
| 04 | [04-basepathpattern-add-methods.md](split-path-filename/tasks/04-basepathpattern-add-methods.md) | 01, 03 |
| 05 | [05-simplepath.md](split-path-filename/tasks/05-simplepath.md) | 01, 04 |
| 06 | [06-datedpath.md](split-path-filename/tasks/06-datedpath.md) | 01, 02, 04 |
| 07 | [07-partitionedpath.md](split-path-filename/tasks/07-partitionedpath.md) | 01, 04 |
| 08 | [08-sinks-config-wiring.md](split-path-filename/tasks/08-sinks-config-wiring.md) | 03, 05, 06, 07 |
| 09 | [09-helpers-cleanup.md](split-path-filename/tasks/09-helpers-cleanup.md) | 07 |
| 10 | [10-documentation.md](split-path-filename/tasks/10-documentation.md) | 01–09 |

## Task File Names (Execution Order)

1. `01-update-constants.md`
2. `02-fix-date-as-partition.md`
3. `03-remove-key-naming-config.md`
4. `04-basepathpattern-add-methods.md`
5. `05-simplepath.md`
6. `06-datedpath.md`
7. `07-partitionedpath.md`
8. `08-sinks-config-wiring.md`
9. `09-helpers-cleanup.md`
10. `10-documentation.md`

## Blocking Dependencies

- Tasks 05, 06, 07 depend on 04 (BasePathPattern).
- Task 08 depends on 05, 06, 07 (all patterns migrated).
- Task 10 depends on all implementation tasks.
