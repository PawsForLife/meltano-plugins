# Task: Refactor tap streams.py to Python 3.12 typing

## Background

`restful_api_tap/streams.py` has the heaviest typing impact. This task updates type hints to built-in generics and pipe-union syntax only in this file. Depends on task 01 (Ruff/mypy config) so the linter enforces the new style.

**Dependencies:** Task 01 (configure Ruff and mypy).

## This Task

- **File:** `taps/restful-api-tap/restful_api_tap/streams.py`
- Replace `Dict`, `List`, `Optional`, `Union` with `dict`, `list`, `X | None`, `X | Y` in all annotations (parameters, return types, locals where applicable).
- Keep `Any`, `Generator`, `Iterable`, `cast` from `typing`; remove unused imports (`Union`, `Optional`, `Dict`, `List`, etc.).
- Do not change `singer_sdk.typing` usage (e.g. `th.Property`, schema definitions).
- Run from `taps/restful-api-tap/`: `uv run ruff check .`, `uv run mypy restful_api_tap`, `uv run pytest` (or at least tests that cover streams).

**Acceptance criteria:** No remaining `typing.Dict`/`List`/`Optional`/`Union` in streams.py; Ruff and mypy pass for the tap; existing tests pass.

## Testing Needed

- Run existing test suite from `taps/restful-api-tap/`: `uv run pytest`. Behaviour must be unchanged; no new tests required (refactor-only).
- Run `uv run ruff check .` and `uv run mypy restful_api_tap` to confirm style and type compliance.
