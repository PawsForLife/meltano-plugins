# Task Plan: 04-documentation

## Overview

This task updates all user- and AI-facing documentation so they reflect the Hive partition literal-segment behaviour: literal (non-date) segments are emitted as `field_name=value` (e.g. `region=eu`, `country=UK`) instead of value-only. It depends on task 03 (code and tests complete). No code or automated tests are written; verification is by manual review of updated sections against the implementation and `_features/hive-partition-key-value-paths/plans/master/documentation.md`.

## Files to Create/Modify

| File | Action |
|------|--------|
| `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` | Modify: Public Interfaces (`get_partition_path_from_schema_and_record`) and Hive partitioning behaviour — state literal segments are `field_name=value`; add example path e.g. `region=eu/year=2024/month=03/day=11`. |
| `loaders/target-gcs/CHANGELOG.md` | Modify: Add entry under **### Changed** (Unreleased): literal partition path segments now Hive-standard `key=value`; compatibility and migration note (existing value-only keys not migrated). |
| `loaders/target-gcs/README.md` | Optional: If the Hive partitioning section does not explicitly state that literal segments are always `key=value`, add one sentence to that effect. |

**Not modified:** Root `CHANGELOG.md`, `GLOSSARY_MELTANO_SINGER.md`, `AI_CONTEXT_QUICK_REFERENCE.md`, `AI_CONTEXT_REPOSITORY.md`, `AI_CONTEXT_PATTERNS.md` (per master documentation.md).

## Test Strategy

- **No automated tests** for documentation. No TDD step.
- **Verification:** Read updated sections and confirm:
  - Wording matches implementation (literal segments = `field_name=value`, path-safe value).
  - Examples use `region=eu/year=2024/month=03/day=11` (or equivalent).
  - CHANGELOG entry clearly describes the change and states that existing object keys with value-only literal segments are not migrated; new writes use key=value.

## Implementation Order

1. **AI context** — In `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`:
   - **Public Interfaces** (under `get_partition_path_from_schema_and_record`): Update description so literal segments are explicitly `field_name=value` (path-safe value); set example path to e.g. `region=eu/year=2024/month=03/day=11`.
   - **Hive partitioning behaviour**: State that literal segments are emitted as `field_name=value` (Hive standard); include example paths e.g. `region=eu/year=2024/month=03/day=11`.

2. **CHANGELOG** — In `loaders/target-gcs/CHANGELOG.md`:
   - Under **## [Unreleased]** → **### Changed**, add one bullet:
     - Literal partition path segments are now Hive-standard `key=value` (e.g. `region=eu`, `country=UK`) instead of value-only. Improves compatibility with Athena, Glue, BigQuery external tables, and Spark. Existing object keys that used value-only literal segments are not migrated; new writes use key=value segments.
   - Follow existing CHANGELOG style (concise bullets; no new headings).

3. **README (optional)** — In `loaders/target-gcs/README.md`:
   - In the "Hive partitioning (schema-driven)" section: If it does not already state that literal segments are always `key=value`, add one sentence (e.g. literal segments are always emitted as `field_name=value`, e.g. `region=eu`).

## Validation Steps

1. Read the updated **Public Interfaces** and **Hive partitioning behaviour** in `AI_CONTEXT_target-gcs.md` and confirm they describe literal segments as `field_name=value` with the given example.
2. Read the new CHANGELOG entry and confirm it describes the behaviour change and the migration note (no migration of existing value-only keys).
3. If README was updated, confirm the Hive section explicitly states literal segments are `key=value`.
4. Cross-check wording against `_features/hive-partition-key-value-paths/plans/master/documentation.md` for consistency.

## Documentation Updates

This task *is* the documentation update. No further doc changes are required. After completion, the feature’s docs (AI context, CHANGELOG, optionally README) will match the implementation from tasks 01–03.
