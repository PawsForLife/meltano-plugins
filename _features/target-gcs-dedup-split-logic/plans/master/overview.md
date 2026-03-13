# Plan Overview: target-gcs-dedup-split-logic

## Purpose

Refactor the target-gcs loader to reduce duplication and clarify branching by:
- **Unifying** repeated logic into shared sink-private methods and a single constant.
- **Splitting** switch logic (hive vs non-hive key, hive init) into named functions called from thin dispatchers.

Behaviour is preserved; all existing tests remain the regression gate.

## Objectives and Success Criteria

- **Objectives:** Single implementation for flush/close, key prefix+normalize, record write, rotate-at-limit; one source of truth for `DEFAULT_PARTITION_DATE_FORMAT`; shared “field required and non-null” validation; named functions for non-hive key computation and hive init.
- **Success:** No behaviour change; full target-gcs test suite passes; code is easier to maintain and test; new helpers have unit coverage where not already covered by existing black-box tests.

## Key Requirements and Constraints

- **Scope:** `loaders/target-gcs/target_gcs/` and `target_gcs/helpers/` only. No new packages or external libraries.
- **Constraints:** Preserve existing public behaviour and config; follow TDD (tests first for new surface); use dependency injection where non-deterministic (time/date already injected in sink); black-box tests only (no asserting on call counts or log lines).
- **References:** See [architecture.md](architecture.md), [interfaces.md](interfaces.md), [implementation.md](implementation.md).

## Relationship to Existing Systems

- **target-gcs:** Refactor only. `GCSSink` and helpers remain the single sink implementation; config schema and CLI unchanged. Tap and target communication (Singer JSONL) unchanged.
- **Meltano / Singer:** No change to config file, state file, or Catalog usage; see `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md`.
