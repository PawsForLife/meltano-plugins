# Task Plan: 10-update-changelogs

## Overview

This task adds changelog entries for the Python 3.12 typing refactor (typing-312-standards). It runs **after** all code and config changes (tasks 01–09) so entries accurately describe the full scope. No code or config is modified; only changelog files are updated. Conventions: root uses date-based headings; plugin changelogs use version blocks with `[Unreleased]` where applicable; one heading per type per section (single `### Changed` per section, with bullets).

## Files to Create/Modify

| File | Action |
|------|--------|
| `CHANGELOG.md` (repo root) | **Modify.** Add one bullet under `### Changed` for the commit date. If a section for that date already exists and already has `### Changed`, append the new bullet there; otherwise add `## YYYY-MM-DD` at the top (commit date) with `### Changed` and the bullet. Entry text: "Updated Python type hints to 3.12 style (built-in generics and pipe unions) across tap, target, and scripts." |
| `taps/restful-api-tap/CHANGELOG.md` | **Modify.** Under `## [Unreleased]`, add `### Changed` (if not present) and one bullet: e.g. "Updated type hints to Python 3.12 style (built-in generics and pipe unions)." |
| `loaders/target-gcs/CHANGELOG.md` | **Modify.** Under `## [Unreleased]`, add `### Changed` (if not present) and one bullet: e.g. "Updated type hints to Python 3.12 style (built-in generics and pipe unions)." |

No new files. No code or config changes.

## Test Strategy

- **No automated tests** for changelog content per task spec.
- **Manual review**: Confirm entries are concise, accurate, and follow project conventions (one heading per type per section; date-based at root, version/Unreleased for plugins).
- **Optional**: If the project has tooling that parses CHANGELOG (e.g. release automation), run it to ensure it still works; not required for task completion.

## Implementation Order

1. **Root `CHANGELOG.md`**
   - Open `CHANGELOG.md`. Determine commit date (or use current date for the plan).
   - If `## YYYY-MM-DD` for that date exists and has `### Changed`, append the new bullet.
   - If that date section does not exist, insert at the top: `## YYYY-MM-DD`, then `### Changed`, then the bullet.
   - Ensure only one `### Changed` block per date; add the bullet to it.

2. **Tap `taps/restful-api-tap/CHANGELOG.md`**
   - Under `## [Unreleased]`, add or reuse `### Changed` and one bullet describing type-hint updates for the tap.

3. **Target `loaders/target-gcs/CHANGELOG.md`**
   - Under `## [Unreleased]`, add or reuse `### Changed` and one bullet describing type-hint updates for the target.

4. **Review**
   - Re-read each modified changelog; verify format matches `.cursor/CONVENTIONS.md` (date-based root; one heading per type per section; plugin format consistent with existing entries).

## Validation Steps

1. **Format**: Root changelog uses `## YYYY-MM-DD`; under each date there is at most one `### Changed` (with one or more bullets). Plugin changelogs have at most one `### Changed` under `[Unreleased]`.
2. **Content**: Wording clearly describes the refactor (3.12 style, built-in generics, pipe unions) without implying behaviour or API changes.
3. **Scope**: Root entry mentions tap, target, and scripts; tap entry is tap-only; target entry is target-only.
4. **No regressions**: No code, config, or test files modified; only markdown changelog files changed.

## Documentation Updates

- **Changelogs**: This task *is* the documentation update (changelog entries). No other docs require changes as part of this task.
- **Optional (out of scope for this task)**: Master documentation plan mentions optional updates to CONTRIBUTING or AI_CONTEXT_PATTERNS for typing style; those are separate follow-ups, not part of task 10.
