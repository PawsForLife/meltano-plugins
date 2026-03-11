# Task Plan: 02 — Add is_sorted to plugin schema (meltano.yml)

**Feature:** restful-api-tap-is-sorted-stream-config  
**Task:** 02-add-is-sorted-plugin-schema  
**Plan location:** `_features/restful-api-tap-is-sorted-stream-config/plans/tasks/02-add-is-sorted-plugin-schema.md`

---

## 1. Overview

This task declares the stream-level **`is_sorted`** setting in the restful-api-tap plugin definition (`meltano.yml`) so Meltano projects can configure it under `config.streams[]`. It is schema declaration only: no Python code is changed and no runtime logic reads this file; the tap’s config schema and discovery logic are updated in later tasks (03–05). Success means the setting appears in the plugin’s settings list and is accepted by Meltano when present in stream config.

---

## 2. Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `taps/restful-api-tap/meltano.yml` | **Modify** | Add one stream-level setting entry for `is_sorted` (boolean). |

### Change in `taps/restful-api-tap/meltano.yml`

- **Where:** Under `plugins.extractors[].settings`, adjacent to other stream-level settings. Place after `source_search_query` (line 65) to keep stream-related options together.
- **What:** Append:

```yaml
        - name: is_sorted
          kind: boolean
```

- **Constraints:** No new env vars or CLI flags; no change to top-level config or to any other plugin. Do not add `value` or `default` in meltano.yml unless the project’s Meltano pattern requires it; the tap will default to `False` in code (task 03).

---

## 3. Test Strategy

- **No new automated tests** for this task. The task doc specifies verification by manual or Meltano config validation; the setting is consumed by the tap in tasks 03–05, where TDD tests will assert behaviour.
- **Existing quality gates:** After the edit, run the restful-api-tap test suite, lint, and typecheck from `taps/restful-api-tap/` to ensure no regressions (e.g. no YAML syntax errors). No assertions on logs or call counts.

---

## 4. Implementation Order

1. Open `taps/restful-api-tap/meltano.yml`.
2. Locate the `source_search_query` entry under `plugins.extractors[].settings`.
3. After it, insert the two-line block:
   - `- name: is_sorted`
   - `kind: boolean`
4. Save and run validation steps below.

---

## 5. Validation Steps

1. **YAML / structure:** Confirm the file is valid YAML and the new entry is under `plugins.extractors[].settings` with correct indentation.
2. **Plugin schema:** Manually verify that the plugin schema (e.g. via `meltano config restful-api-tap --list` or Meltano UI) shows `is_sorted` as a stream-level setting of kind boolean.
3. **Optional:** In a Meltano project that uses this tap, set `config.streams[].is_sorted: true` for a stream and confirm the project accepts it (no schema error).
4. **Regression:** From `taps/restful-api-tap/` run: `./install.sh` (or `uv run pytest`, `uv run ruff check .`, `uv run mypy restful_api_tap`). All tests and checks must pass.

---

## 6. Documentation Updates

- **This task:** No separate doc changes. The new setting name in `meltano.yml` is self-describing.
- **Later:** Task 06 (update-is-sorted-documentation) will document `is_sorted` in README and/or docs; do not add that in this task.

---

## References

- Task doc: `_features/restful-api-tap-is-sorted-stream-config/tasks/02-add-is-sorted-plugin-schema.md`
- Master plan: `_features/restful-api-tap-is-sorted-stream-config/plans/master/` (overview.md, implementation.md, testing.md)
- Next: Task 03 adds `is_sorted` to common_properties and discovery; Task 04 adds it to DynamicStream; Task 05 wires it in discover_streams.
