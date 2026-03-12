# Task Plan: 08-documentation-updates

## Overview

This task updates project AI context documentation so it accurately describes partition path resolution after the dateutils implementation (Task 05). No code or tests are added or changed. A reader of `AI_CONTEXT_target-gcs.md` will understand that string partition values are parsed with **dateutil** and that unparseable or unsupported-timezone cases are surfaced (warning or error), not silently ignored.

**Scope:** Documentation only. Prerequisite: Task 05 complete (implementation and docstring in `partition_path.py` are done).

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` | **Modify** — Update Public Interfaces and Partition-by-field sections. |
| `loaders/target-gcs/target_gcs/helpers/partition_path.py` | **Verify only** — Confirm the docstring (updated in Task 05) is consistent with the AI context; do not change code or docstring to match docs. |

### Specific edits in `AI_CONTEXT_target-gcs.md`

1. **Public Interfaces — `get_partition_path_from_record`** (approx. lines 28–32)
   - Replace the sentence that describes parsing as "ISO via `fromisoformat`, then `%Y-%m-%d`" with: string values are parsed with **dateutil** (`dateutil.parser.parse`); many formats are supported without a custom format list.
   - Replace "If missing or unparseable, returns `fallback_date`" with: When the field is missing or not a string, fallback date is used; when the string is unparseable (`ParserError`) or uses an unsupported timezone (`UnknownTimezoneWarning`), a warning or error is surfaced (and optionally fallback path is returned). Remove or reword any phrase that implies "missing or unparseable → fallback_date" without mentioning visibility of unparseable/unsupported-timezone.

2. **GCSSink — Record processing** (approx. line 62)
   - Align with the above: e.g. "partition path is resolved per record via `get_partition_path_from_record`; missing or non-string partition field uses run date as fallback; unparseable or unsupported-timezone strings surface a warning or error (and optionally fallback path)."

3. **Partition-by-field behaviour** (approx. line 79)
   - Align wording: state that resolution uses dateutil for string values and that unparseable or unsupported-timezone cases are visible (warning/error), not silent fallback; fallback remains for missing or non-string field.

---

## Test Strategy

- **No new automated tests.** This task is documentation-only.
- **Verification:** After editing the AI context file, read the docstring of `get_partition_path_from_record` in `partition_path.py` (as updated in Task 05) and confirm it is consistent with the AI context (same parsing mechanism and visibility behaviour). If the docstring and AI context disagree, update the AI context to match the implemented behaviour; do not change code to match documentation.

---

## Implementation Order

1. **Confirm Task 05 is complete**  
   Ensure `partition_path.py` uses dateutil and its docstring describes dateutil parsing and visibility of unparseable/unsupported-timezone.

2. **Update Public Interfaces**  
   In `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`, edit the `get_partition_path_from_record` bullet: dateutil parsing; fallback only for missing/non-string; unparseable and unsupported-timezone surfaced (warning/error, optionally fallback).

3. **Update GCSSink record processing**  
   In the same file, adjust the sentence about partition path resolution and fallback so it mentions visibility for unparseable/unsupported-timezone.

4. **Update Partition-by-field behaviour**  
   In the "Partition-by-field behaviour" section, state dateutil parsing and that unparseable/unsupported-timezone are visible; fallback for missing or non-string only.

5. **Consistency check**  
   Read `get_partition_path_from_record` docstring in `partition_path.py`; ensure the AI context matches it (and the code). Resolve any discrepancy by updating the AI context only.

6. **Optional: metadata**  
   If the project bumps "Last Updated" or version in the AI context metadata table, update it (e.g. date, version) per project convention.

---

## Validation Steps

- [ ] `AI_CONTEXT_target-gcs.md` states that string partition values are parsed with dateutil (`dateutil.parser.parse`), not `fromisoformat`/`strptime`.
- [ ] The same file states that unparseable (`ParserError`) and unsupported-timezone (`UnknownTimezoneWarning`) cases are surfaced via warning or error (and optionally fallback path); no wording implies silent fallback for those cases.
- [ ] Public Interfaces, GCSSink record processing, and Partition-by-field behaviour are aligned and consistent with the docstring in `partition_path.py`.
- [ ] No code or docstring in `partition_path.py` was changed in this task (verification only).

---

## Documentation Updates

This task *is* the documentation update for the feature’s AI context:

- **Updated:** `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` — Public Interfaces (`get_partition_path_from_record`), GCSSink record processing, and Partition-by-field behaviour.
- **Verified:** `partition_path.py` docstring (updated in Task 05) matches the AI context; discrepancies resolved by editing the AI context only.

No new docs, README, or user-facing docs are required unless the project normally documents partition field format support elsewhere; in that case add a short note that timestamps are parsed with dateutil and that unparseable or unsupported timezone values produce a visible warning or error.
