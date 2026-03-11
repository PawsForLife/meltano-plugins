# Task 06: Update is_sorted documentation

## Background

Per the master plan (documentation.md), the feature must be documented so users know the option, when to set it, and its effect. This task depends on all code changes (tasks 01–05) being complete so documentation reflects actual behaviour. Per project rules: update documentation to reflect the code; never update code to match documentation.

## This Task

- **Files to update:**
  1. **README.md** (`taps/restful-api-tap/README.md`): Add a short subsection (e.g. under stream configuration or incremental replication) describing:
     - Option: `is_sorted` (stream-level, boolean, default `False`).
     - When to set: when the source API returns records ordered by the replication key (e.g. `sequence_id`, `created_at`).
     - Effect: when `true`, the stream is declared sorted so interrupted syncs are resumable; the source API must actually return records ordered by the replication key.
     - Placement: near other stream-level options (e.g. `replication_key`, `source_search_field`, `source_search_query`). Keep concise; optional link to SDK incremental replication docs.
  2. **streams.py:** Already updated in task 04 with `is_sorted` in `DynamicStream.__init__` Args in the docstring; no further change required unless the docstring was missed.
  3. **tap.py:** The `th.Property("is_sorted", ...)` description is sufficient. Optionally add one line to `discover_streams()` docstring: “Resolves stream-level `is_sorted` (default False) and passes to DynamicStream.”
- **What not to do:** Do not duplicate SDK incremental replication docs; one sentence on resumable state is enough. Do not add comments that restate the SDK docs.

## Testing Needed

- No new automated tests. Verify README and docstrings match the implemented behaviour (manual or doc build if present). Lint and existing test suite must still pass.
