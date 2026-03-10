# Changelog

## [Unreleased]

### Fixed

- `post_process`: when `flatten_records` is false and `store_raw_json_message` is true, the non-flatten return path now adds `_sdc_raw_json` to the row (raw record copy) so the advertised field is emitted.

### Changed

- Workflow `5-plan-task-bug.md`: normalized `{task_file}` to mean filename without `.md`; paths use `{task_file}.md`; example and scratchpad text updated.
- Workflows and commands: applied same `{task_file}` convention across `5-plan-task-feature.md`, `implement-task-fix.md`, `implement-task-feature.md`, `bug-pipeline.md`, `feature-pipeline.md`, and `architect.md` (paths use `{task_file}.md`; examples and mv/changelog links use `.md`; "task file name without extension" in prerequisites and invocations).

## [1.5.0] - 2026-03-10

### Added

- **optional-flatten-config** — Details: [optional-flatten-config.md](_archive/optional-flatten-config/optional-flatten-config.md)
  - Config property `flatten_records` (boolean, default `false`) in tap and stream-level config schema
  - DynamicStream `flatten_records` parameter and post_process branch; sync tests for flatten and non-flatten paths
  - Parameter `flatten_records` on `get_schema()` and schema inference branch (flatten sample vs raw nested)
  - Discovery resolves `flatten_records` per stream and passes to `get_schema()` and `DynamicStream()`
  - Documentation and test alignment for default `flatten_records: false` (README, config.sample.json, AI_CONTEXT)
