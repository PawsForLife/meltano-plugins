# Task Plan: 06 — Update is_sorted documentation

**Feature:** restful-api-tap-is-sorted-stream-config  
**Task:** 06-update-is-sorted-documentation  
**Depends on:** Tasks 01–05 (code changes) complete so documentation reflects actual behaviour.

---

## Overview

This task updates user-facing and code documentation for the stream-level `is_sorted` option. It does not change behaviour; it ensures README, docstrings, and (if present) Meltano settings list describe the option, when to set it, and its effect. Per project rules: update documentation to reflect the code; never update code to match documentation.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `taps/restful-api-tap/README.md` | **Modify.** Add a short subsection for `is_sorted` under stream-level or incremental replication. |
| `taps/restful-api-tap/restful_api_tap/streams.py` | **Verify only.** Confirm `DynamicStream.__init__` Args docstring includes `is_sorted` (added in task 04). If missing, add it. |
| `taps/restful-api-tap/restful_api_tap/tap.py` | **Optional.** Add one line to `discover_streams()` docstring: “Resolves stream-level `is_sorted` (default False) and passes to DynamicStream.” |

No new files. No changes to `meltano.yml` beyond what task 02 already adds (the setting entry is self-explanatory).

---

## README.md — Specific Changes

**Location:** `taps/restful-api-tap/README.md`  
**Placement:** Under **Stream level config options** (after `source_search_query` and before **Top-Level Authentication**), or in a short “Incremental replication and resumability” subsection if that fits the existing structure.

**Content to add (concise):**

- **Option:** `is_sorted` — stream-level, boolean, default `False`.
- **When to set:** When the source API returns records ordered by the replication key (e.g. `sequence_id`, `created_at`).
- **Effect:** When `true`, the stream is declared sorted so interrupted syncs are resumable; the source API must actually return records ordered by the replication key.
- **Optional:** One sentence or link to SDK incremental replication docs (e.g. [Meltano Singer SDK – Incremental replication](https://sdk.meltano.com/en/latest/incremental_replication.html)). Do not duplicate SDK prose.

**Constraints (from master plan):** Do not duplicate SDK incremental replication docs; one sentence on resumable state is enough. Keep the subsection short.

---

## streams.py — Verification

- **Location:** `DynamicStream.__init__` docstring, Args section.
- **Check:** Presence of an Args entry for `is_sorted` describing purpose and default (e.g. “when True, stream is declared sorted by replication_key for resumable state. Default False.”).
- **If missing:** Add the Args line as specified in the master implementation plan (task 04). No code logic changes in this task.

---

## tap.py — Optional Docstring

- **Location:** `discover_streams()` docstring in `tap.py`.
- **Change (optional):** Add one line: “Resolves stream-level `is_sorted` (default False) and passes to DynamicStream.”
- **Note:** The `th.Property("is_sorted", ...)` description is sufficient for the schema; this line is for discoverability in the function docstring.

---

## Test Strategy

- **No new automated tests.** This task is documentation-only.
- **Manual / checklist:** Verify README subsection exists, is in the right place, and matches implemented behaviour (option name, default, when to use, effect).
- **Regression:** Run existing test suite and linters from `taps/restful-api-tap/`; all must pass. No assertions on doc content in code.

---

## Implementation Order

1. **Prerequisite:** Confirm tasks 01–05 are complete (schema, common_properties, discover_streams resolution, DynamicStream parameter and `self.is_sorted`, tests passing).
2. **README:** Add the `is_sorted` subsection under stream-level config (or incremental replication), using the content above. Keep under the 500-line doc limit (content_length.mdc).
3. **streams.py:** Open `DynamicStream.__init__` docstring; if `is_sorted` is not in Args, add it.
4. **tap.py (optional):** If adding a discover_streams() docstring line, insert the one-line description.
5. **Validation:** Run lint, typecheck, and full test suite; fix any regressions (none expected from doc-only edits).

---

## Validation Steps

1. **README:** Read the new subsection; confirm it describes `is_sorted`, default `False`, when to set (API ordered by replication key), and effect (resumable interrupted syncs). Confirm placement is near other stream-level options.
2. **streams.py:** Grep or read the `__init__` docstring; confirm `is_sorted` is documented in Args.
3. **Lint and tests:** From `taps/restful-api-tap/`: `uv run ruff check .`, `uv run ruff format --check`, `uv run mypy restful_api_tap`, `uv run pytest`. All pass.
4. **No SDK duplication:** Ensure no long copy-paste from SDK incremental replication docs; one sentence on resumability is enough.

---

## Documentation Updates (Summary)

| Document | Action |
|----------|--------|
| README.md | Add stream-level `is_sorted` subsection (required). |
| streams.py | Verify/add `is_sorted` in `DynamicStream.__init__` Args (verify first, add if missed in task 04). |
| tap.py | Optionally add one line to `discover_streams()` docstring. |
| meltano.yml | No further doc change (task 02 adds the setting). |

---

## References

- Master plan: `_features/restful-api-tap-is-sorted-stream-config/plans/master/` (overview.md, implementation.md, documentation.md)
- Task doc: `_features/restful-api-tap-is-sorted-stream-config/tasks/06-update-is-sorted-documentation.md`
- SDK: [Meltano Singer SDK – Incremental replication](https://sdk.meltano.com/en/latest/incremental_replication.html)
