# Documentation: Python 3.12 Typing Standards

## Documentation to Create

**None.** This is a refactor of type hints only; no new user-facing features, APIs, or config. No new docs are required.

## Documentation to Update

- **Changelog**: Add an entry under the appropriate date (or “Unreleased”) in:
  - **Root** `CHANGELOG.md`: One line under `### Changed` (e.g. “Updated Python type hints to 3.12 style (built-in generics and pipe unions) across tap, target, and scripts.”).
  - **Tap** `taps/restful-api-tap/CHANGELOG.md`: If the plugin maintains a changelog, add a brief “Changed” entry for type-hint updates in that plugin.
  - **Target** `loaders/target-gcs/CHANGELOG.md`: Same as tap, if the plugin maintains a changelog.
- Follow `.cursor/CONVENTIONS.md` for changelog format: one heading per type per section; date-based for root, version or date for plugins.

## Code Documentation (Docstrings and Comments)

- **Docstrings**: No requirement to change docstrings. If a docstring documents a parameter or return type in prose (e.g. “Returns a list of …”), it can remain as-is unless the team prefers to align wording with the new type names (e.g. “list” instead of “List”).
- **Comments**: No new comments required for “we use 3.12 typing”; the code itself is the standard. Remove any comments that referred to “Optional” or “Union” in a way that is now misleading.

## User-Facing Documentation

- **README, Meltano usage, config samples**: No updates required. Config file, state file, and stream behaviour are unchanged.
- **docs/AI_CONTEXT/**: After the refactor, if AI context docs mention “typing” or “Optional/Union” in examples, consider a brief pass to use 3.12 style in code snippets for consistency. Not mandatory for this feature; can be a follow-up.

## Developer Documentation

- **Contributing / code style**: If the project has a style guide or CONTRIBUTING that mentions type hints, add a line that 3.12-style hints are used (built-in generics and `|` for unions). If no such doc exists, no change required.
- **AI context**: `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` already says “Optional and generic types from typing are used where appropriate.” After the refactor, that can be updated to “Type hints use Python 3.12 style: built-in generics (dict, list, …) and pipe unions (X | Y, X | None); typing is used only for Any, Callable, Iterator, Generator, Iterable, cast.” Optional, for consistency.

## Summary

- **Must**: Changelog entry(ies) for the refactor (root and optionally per-plugin).
- **Optional**: Short update to CONTRIBUTING or AI_CONTEXT_PATTERNS if they mention typing style; optional pass on AI context code examples.
- **No**: New docs, user guides, or API docs beyond changelog and any brief style note.
