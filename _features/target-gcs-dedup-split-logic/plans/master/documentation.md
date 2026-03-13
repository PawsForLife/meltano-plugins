# Documentation: target-gcs-dedup-split-logic

## Documentation to Create

- None. No new user-facing features; refactor only.

## Documentation to Update

- **Code docstrings:** Add or update Google-style docstrings for each new method/function:
  - `GCSSink._flush_and_close_handle`, `_apply_key_prefix_and_normalize`, `_write_record_as_jsonl`, `_maybe_rotate_if_at_limit`, `_compute_non_hive_key`, `_init_hive_partitioning` in `sinks.py`.
  - `_assert_field_required_and_non_null_type` in `partition_schema.py`.
- **AI context:** If refactor significantly changes structure of `GCSSink` or helpers, update `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` to describe the new private methods and the single constant location (partition_path). Do not update code to match docs; update docs to match code.

## Code Documentation

- Docstrings: Purpose (one line), then Args/Returns/Raises where relevant. Keep concise per `documentation.mdc`.
- Comments: Use only where logic is non-obvious (e.g. why double-slash replace or lstrip).

## User- and Developer-Facing

- No README or user-guide changes. Developer-facing context is in AI_CONTEXT and this plan set; no separate “refactor guide” required unless the team adds one.
