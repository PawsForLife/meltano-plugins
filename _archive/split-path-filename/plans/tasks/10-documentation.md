# Task Plan: 10 — Documentation Updates

## Overview

This task updates all user-facing and AI context documentation to reflect the split-path-filename feature: removal of `key_naming_convention`, fixed key format via constants (`PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`), and timestamp-only chunking (no `chunk_index`). It depends on tasks 01–09 being complete; no code changes.

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `loaders/target-gcs/README.md` | Remove `key_naming_convention` from config table; update Hive section with fixed path format `{stream}/{hive_path}/{timestamp}.jsonl`; add key format table (SimplePath, DatedPath, PartitionedPath); remove `{chunk_index}` from chunking section. |
| `loaders/target-gcs/meltano.yml` | Remove `key_naming_convention` from settings and config block (verify task 03 did not already remove; if present, remove). |
| `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` | Remove `key_naming_convention` from config schema; update key tokens to `{stream}`, `{date}`, `{hive_path}`, `{timestamp}` (no `{chunk_index}`); update path pattern descriptions to reference constants and `filename_for_current_file` / `full_key`; update PartitionedPath to use `hive_path(record)` and `path_for_record`; remove GCSSink key_naming_convention from constructor/config flow. |
| `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md` | Update Core Interfaces target-gcs config line: remove `key_naming_convention`. |
| `docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md` | Update target-gcs component responsibilities table: remove `key_naming_convention` from Config row. |
| `loaders/target-gcs/CHANGELOG.md` | Under `[Unreleased]`: add `### Removed` — `key_naming_convention`; add `### Changed` — Key format fixed via path/filename constants; chunking timestamp-only. |

---

## Test Strategy

Documentation tasks do not require TDD tests. Validation is via consistency checks:

1. **Grep verification**: After edits, run `rg -n "key_naming_convention|chunk_index" loaders/target-gcs docs/AI_CONTEXT` — expect no matches (or only in CHANGELOG/archive context).
2. **Schema alignment**: Confirm README config table and AI context config schema match `target.py` (no `key_naming_convention`).
3. **Key format alignment**: Confirm docs describe `{stream}/{date}`, `{stream}/{hive_path}`, `{timestamp}.jsonl` per SimplePath, DatedPath, PartitionedPath.

No new test files; existing tests (from tasks 01–09) validate implementation. Docs must reflect that implementation.

---

## Implementation Order

1. **README.md** — Config table, Hive section, key format table, chunking section.
2. **meltano.yml** — Remove `key_naming_convention` from settings and config.
3. **AI_CONTEXT_target-gcs.md** — Config schema, key tokens, path pattern descriptions, GCSSink, examples.
4. **AI_CONTEXT_QUICK_REFERENCE.md** — Core Interfaces target-gcs config line.
5. **AI_CONTEXT_REPOSITORY.md** — target-gcs Config row.
6. **CHANGELOG.md** — Removed and Changed entries under `[Unreleased]`.

---

## Validation Steps

1. **Grep**: `rg "key_naming_convention|chunk_index" loaders/target-gcs docs/AI_CONTEXT` — no matches except CHANGELOG Removed/Changed entries.
2. **Read-through**: README config table has no `key_naming_convention`; Hive section describes fixed format; key format table matches feature spec.
3. **AI context**: `AI_CONTEXT_target-gcs.md` config schema and key tokens match implementation; path patterns reference constants and new methods.
4. **Changelog**: `[Unreleased]` has Removed (`key_naming_convention`) and Changed (key format, chunking) entries.
5. **Lint**: `uv run ruff check .` and `uv run mypy target_gcs` from `loaders/target-gcs/` — no new issues (docs are markdown; no code changes).

---

## Documentation Updates

This task *is* the documentation update. The following content changes apply:

### README.md

- **Config table**: Remove `key_naming_convention` row; keep `bucket_name`, `date_format`, `key_prefix`, `max_records_per_file`, `hive_partitioned`.
- **Hive section**: Replace configurable key template with fixed format `{stream}/{hive_path}/{timestamp}.jsonl`; remove references to `key_naming_convention` and `{partition_date}` as user-configurable; document that path format is fixed.
- **Key format table**: Add table mapping pattern → path format:
  - SimplePath: `{stream}/{date}/{timestamp}.jsonl`
  - DatedPath: `{stream}/{hive_path}/{timestamp}.jsonl` (hive_path = extraction date)
  - PartitionedPath: `{stream}/{hive_path}/{timestamp}.jsonl` (hive_path from record)
- **Chunking section**: Remove `{chunk_index}`; state that chunking uses timestamp-only (new file per chunk gets new timestamp).

### meltano.yml

- Remove `- name: key_naming_convention` from settings.
- Remove `key_naming_convention: "{stream}/{partition_date}/{timestamp}.jsonl"` from config block and its comment.

### AI_CONTEXT_target-gcs.md

- **Config schema**: Remove `key_naming_convention`; document retained options.
- **Key tokens**: `{stream}`, `{date}`, `{hive_path}`, `{timestamp}`; no `{chunk_index}`.
- **Path patterns**: Update SimplePath, DatedPath, PartitionedPath to reference `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`; `filename_for_current_file()`, `full_key(path, filename)`; PartitionedPath uses `path_for_record(record)` and `hive_path(record)` for key building.
- **GCSSink**: Remove key_naming_convention from constructor/config flow.
- **Examples**: Remove `key_naming_convention` from config examples; update resulting key pattern descriptions.

### AI_CONTEXT_QUICK_REFERENCE.md

- Core Interfaces: change `config: bucket_name, key_prefix, key_naming_convention` to `config: bucket_name, key_prefix`.

### AI_CONTEXT_REPOSITORY.md

- target-gcs Config row: change `bucket_name (required), key_prefix, key_naming_convention, date_format` to `bucket_name (required), key_prefix, date_format`.

### CHANGELOG.md

- Under `[Unreleased]`:
  - **### Removed**: `key_naming_convention` config option.
  - **### Changed**: Key format now fixed via path and filename constants; chunking uses timestamp only (no `chunk_index`).
