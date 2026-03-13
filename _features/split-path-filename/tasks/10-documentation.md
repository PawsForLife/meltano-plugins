# 10 — Documentation Updates

## Background

Documentation must reflect the removal of `key_naming_convention` and the new fixed key format. Depends on tasks 01–09 (implementation complete).

## This Task

**Files to modify:**
- `loaders/target-gcs/README.md`
- `loaders/target-gcs/meltano.yml` (if not fully done in task 03)
- `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`
- `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md`
- `docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md`
- `loaders/target-gcs/CHANGELOG.md`

**Implementation steps:**
1. **README.md**: Remove `key_naming_convention` from config table; update Hive partitioning section with fixed path format `{stream}/{hive_path}/{timestamp}.jsonl`; add key format table (SimplePath, DatedPath, PartitionedPath).
2. **meltano.yml**: Ensure `key_naming_convention` removed (task 03).
3. **AI_CONTEXT_target-gcs.md**: Remove `key_naming_convention` from config schema; update key tokens (`{stream}`, `{date}`, `{hive_path}`, `{timestamp}`; no `{chunk_index}`); update path pattern descriptions.
4. **AI_CONTEXT_QUICK_REFERENCE.md**: Update target-gcs config line — remove `key_naming_convention`.
5. **AI_CONTEXT_REPOSITORY.md**: Remove `key_naming_convention` from target-gcs component responsibilities.
6. **CHANGELOG.md**: Under `[Unreleased]` or next version: `### Removed` — `key_naming_convention`; `### Changed` — Key format fixed via constants; chunking timestamp-only.

**Acceptance criteria:**
- All docs consistent with implementation.
- No references to `key_naming_convention` or `chunk_index` in key format.
- Changelog updated.
