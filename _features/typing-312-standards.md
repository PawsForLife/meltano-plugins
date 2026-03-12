# Feature: Python 3.12 typing standards

## Background

The codebase uses older typing styles (e.g. `typing.Union`, `typing.Dict`, `typing.List`, `typing.Optional`). Python 3.12 allows built-in generics and `X | Y` union syntax. Aligning with 3.12 standards improves readability and matches current best practice.

## This Task

- Replace `Union[X, Y]` with `X | Y` (pipe union) across the repo.
- Replace `typing.Dict`, `typing.List`, `typing.Set`, `typing.Tuple` (and similar) with built-in `dict`, `list`, `set`, `tuple` where used as type hints.
- Replace `Optional[X]` with `X | None` where appropriate.
- Keep `typing` imports only for symbols that have no built-in equivalent (e.g. `TypedDict`, `Protocol`, `Callable`, `TypeVar`, etc.).
- Ensure no use of `from __future__ import annotations` is required for 3.12-style hints in the affected code (or add it if needed for forward references).
- Apply changes consistently across all Python code (taps, loaders, shared libs, tests).
- **Configure Ruff and mypy** to require these style rules where possible: enable Ruff pyupgrade rules (e.g. UP006, UP007, UP045) for PEP 585/604 style; document or set mypy so future code follows the same conventions.

## Testing Needed

- Existing test suite must pass after changes (no behaviour change).
- Optional: add or run a static type check (e.g. pyright/mypy) if the project uses one, and fix any new issues from the typing updates.
