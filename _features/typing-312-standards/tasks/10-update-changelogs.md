# Task: Update changelogs for Python 3.12 typing refactor

## Background

The documentation plan requires changelog entries for the refactor. This task is done after all code and config changes (tasks 01–09) so the entry accurately describes the scope.

**Dependencies:** Tasks 01–09 (all refactor and config work complete).

## This Task

- **Root** `CHANGELOG.md`: Add one line under `### Changed` (or "Unreleased" as per project convention), e.g. "Updated Python type hints to 3.12 style (built-in generics and pipe unions) across tap, target, and scripts."
- **Tap** `taps/restful-api-tap/CHANGELOG.md`: If the plugin maintains a changelog, add a brief "Changed" entry for type-hint updates in that plugin.
- **Target** `loaders/target-gcs/CHANGELOG.md`: If the plugin maintains a changelog, add a brief "Changed" entry for type-hint updates.
- Follow project conventions (e.g. `.cursor/CONVENTIONS.md` or existing changelog format): one heading per type per section; date-based or version-based as used elsewhere.

**Acceptance criteria:** Changelog(s) updated; no code or config changes in this task.

## Testing Needed

- No automated tests for changelog content. Manual review that entries are concise and accurate. Optional: ensure any tool that parses CHANGELOG (e.g. release automation) still works.
