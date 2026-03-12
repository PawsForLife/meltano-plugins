# Plan Overview: Python 3.12 Typing Standards

## Purpose

Align the codebase with Python 3.12 typing conventions: use built-in generics (`dict`, `list`, `set`, `tuple`) and pipe-union syntax (`X | Y`, `X | None`) instead of `typing.Union`, `typing.Optional`, and `typing.Dict`/`List`/`Set`/`Tuple`. This is a **refactor-only** change with no new behaviour, APIs, or config.

## High-Level Objectives

- Replace `Union[X, Y]` with `X | Y` and `Optional[X]` with `X | None` across affected Python modules and tests.
- Replace `typing.Dict`, `typing.List`, `typing.Set`, `typing.Tuple` with built-in `dict`, `list`, `set`, `tuple` where used as type hints.
- Retain `typing` imports only for symbols with no built-in equivalent: `Any`, `Callable`, `Iterator`, `Generator`, `Iterable`, `cast`; reserve `TypedDict`, `Protocol`, `TypeVar` for future use.
- Do not add `from __future__ import annotations` unless required (e.g. existing scripts that already use it).
- Ensure the existing test suite passes and, if the project runs a static type checker (e.g. mypy), fix any new issues introduced by the typing updates.

## Success Criteria

- All impacted modules and tests use 3.12-style type hints as specified.
- No runtime behaviour change; all existing tests pass.
- **Ruff and mypy** are configured to require 3.12 typing style: Ruff enables UP006 (PEP 585 built-in generics), UP007 (PEP 604 union), UP045 (Optional → X | None) in each plugin (and root scripts if applicable); mypy remains the type-correctness gate (no style-only options; Ruff enforces style).
- Linters (Ruff) and type checker (mypy) pass in each plugin and at repo root where applicable.
- No new external dependencies; no changes to Singer/Meltano tap or target interfaces (config file, state file, Catalog, streams).

## Key Requirements and Constraints

- **Scope**: Tap (restful-api-tap), loader (target-gcs), and repo-root scripts only. No shared library; each plugin is independent.
- **Python version**: Both plugins require Python ≥3.12; built-in generics and `|` unions are native.
- **Singer SDK**: Use of `singer_sdk.typing` (e.g. `th.Property`, `th.StringType`) is unchanged; this plan applies to application code type hints, not SDK schema definitions.
- **Validation**: Existing tests and CI (e.g. pytest, ruff, mypy) remain the gate; no new test behaviour, only type-hint updates.

## Relationship to Existing Systems

- **restful-api-tap**: Heaviest impact in `streams.py` and `pagination.py`; lighter impact in `client.py`, `tap.py`, `utils.py`; minimal in `auth.py` and some tests.
- **target-gcs**: Most runtime code already uses 3.12-style (e.g. `Callable[...] | None`); minor updates in tests (e.g. `test_core.py` for `Any`, `cast`).
- **scripts**: `scripts/list_packages.py` and its tests use `from __future__ import annotations`; review for any remaining `typing` generics to convert.
- No new systems or modules; no changes to config file, state file, or Catalog contracts.

## Plan Location

This plan lives under `_features/typing-312-standards/plans/master/`. Related planning artifacts are in `_features/typing-312-standards/planning/` (impacted-systems, new-systems, possible-solutions, selected-solution). Feature brief: `_features/typing-312-standards.md`.
