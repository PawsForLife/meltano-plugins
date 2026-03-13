# Task List — Schema-driven Hive Partitioning

Feature: **target-gcs-schema-hive-partitioning**  
Plan: `_features/target-gcs-schema-hive-partitioning/plans/master/`

## Execution Order

Tasks are ordered by dependency. Follow TDD: write tests first, then implement until tests pass.

| # | Task | Dependencies |
|---|------|--------------|
| 01 | [Validator tests and implementation](tasks/01-validator-tests-and-impl.md) | None |
| 02 | [Path builder tests and implementation](tasks/02-path-builder-tests-and-impl.md) | None |
| 03 | [Helper exports](tasks/03-helper-exports.md) | 01, 02 |
| 04 | [Config schema (target)](tasks/04-config-schema.md) | None |
| 05 | [Sink init and validation](tasks/05-sink-init-validation.md) | 01, 03, 04 |
| 06 | [Sink record processing](tasks/06-sink-record-processing.md) | 02, 03, 05 |
| 07 | [Sink process_record dispatch](tasks/07-sink-process-record-dispatch.md) | 06 |
| 08 | [Sink and key generation tests](tasks/08-sink-and-key-tests.md) | 07 |
| 09 | [Meltano and README](tasks/09-meltano-and-readme.md) | 04, 07 |

## Summary

- **Task count:** 9
- **Phase 1–2 (helpers):** 01, 02 — validator and path builder (TDD per component).
- **Phase 3 (wiring):** 03, 04 — exports and config.
- **Phase 4 (sink):** 05, 06, 07 — init validation, record processing, dispatch.
- **Phase 5 (tests & docs):** 08 — sink/key tests; 09 — Meltano and README.

## Conventions

- Adhere to `@.cursor/rules/development_practices.mdc`: TDD, black-box tests, no "called_once" or log assertions.
- Each task document: Background, This Task, Testing Needed (tests before implementation where applicable).
