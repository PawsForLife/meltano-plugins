# Task 02: Add is_sorted to plugin schema (meltano.yml)

## Background

The plugin definition in `meltano.yml` must declare `is_sorted` as a stream-level setting so Meltano projects can set it under `config.streams[]`. This task has no code dependencies; it can be done in parallel with task 01 or after. No runtime code reads meltano.yml; this is schema declaration only.

## This Task

- **File:** `taps/restful-api-tap/meltano.yml`
- **Where:** Under `plugins.extractors.settings`, with other stream-level settings (e.g. after `source_search_query`).
- **Change:** Add one entry:
  ```yaml
  - name: is_sorted
    kind: boolean
  ```
- **Acceptance criteria:** The setting appears in the plugin schema; no new env vars or CLI flags; no change to top-level config.

## Testing Needed

- No new automated tests in this task. Existing tests and lint/typecheck remain valid. Verification: manual or via Meltano config validation that `is_sorted` is accepted in stream config.
