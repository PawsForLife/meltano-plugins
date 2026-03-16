# Archive: typing-312-standards

Summary of the Python 3.12 typing standards feature (refactor-only). Paths: `_features/typing-312-standards*` (request, planning, plans, tasks); output: this file.

---

## The request

**Goal:** Align the codebase with Python 3.12 typing conventions: use built-in generics (`dict`, `list`, `set`, `tuple`) and pipe-union syntax (`X | Y`, `X | None`) instead of `typing.Union`, `typing.Optional`, and `typing.Dict`/`List`/`Set`/`Tuple`. No new behaviour, APIs, or config.

**Background:** The repo used older typing styles. Python 3.12 supports built-in generics and `X | Y` unions natively; aligning improves readability and matches current practice.

**Scope:** Tap (restful-api-tap), loader (target-gcs), and repo-root scripts. Replacements: `Union[X, Y]` → `X | Y`; `Optional[X]` → `X | None`; `Dict`/`List`/`Set`/`Tuple` → `dict`/`list`/`set`/`tuple`. Keep `typing` only for symbols with no built-in equivalent (e.g. `Any`, `Callable`, `Iterator`, `Generator`, `Iterable`, `cast`). Optionally add `from __future__ import annotations` only where needed (e.g. forward refs). Apply consistently and configure Ruff (UP006, UP007, UP045) and mypy (`python_version = "3.12"`) to enforce the style.

**Testing:** Existing test suite must pass (no behaviour change). Ruff and mypy must pass after changes; fix any new issues from the typing updates. No new behaviour-level tests; optional static type-check step if the project uses one.

---

## Planned approach

**Chosen solution:** Internal refactor using Python 3.12 stdlib only; no new dependencies. Hybrid rule: remove redundant `typing` imports; keep only the reserved symbols above.

**Architecture:** No system or API changes. Updates are type annotations and imports only within existing modules. Component boundaries, data flow, and entry points (tap CLI, target CLI, scripts) unchanged. Singer/Meltano interfaces (config file, state file, catalog, streams) unchanged.

**Task breakdown (execution order):**

1. **01-configure-ruff-mypy** — Add Ruff UP006, UP007, UP045 and mypy `python_version = "3.12"` for restful-api-tap; confirm target-gcs already has UP and 3.12; no repo-root config. Fix or scope any new violations so CI passes.
2. **02-refactor-tap-streams** — `restful_api_tap/streams.py`: Dict/List/Optional/Union → built-ins and `|`; keep Any, Generator, Iterable, cast.
3. **03-refactor-tap-pagination** — `restful_api_tap/pagination.py`: List/Optional → list, `| None`; keep Any, cast.
4. **04-refactor-tap-client** — `restful_api_tap/client.py`: Optional → `| None`; keep Any, Iterator.
5. **05-refactor-tap-tap** — `restful_api_tap/tap.py`: List/Optional → list, `| None`; keep Any; leave `singer_sdk.typing as th` unchanged.
6. **06-refactor-tap-utils** — `restful_api_tap/utils.py`: Optional → `| None`; keep Any.
7. **07-refactor-tap-tests** — Tap tests: same replacement rules; e.g. `test_streams.py` optional params → `dict | None`, `Any | None`.
8. **08-refactor-target-gcs-tests** — target-gcs tests only (runtime code unchanged); audit and convert any old-style hints.
9. **09-refactor-scripts** — `scripts/list_packages.py` and `scripts/tests/test_list_packages.py`; keep `from __future__ import annotations`; convert any remaining typing generics.
10. **10-update-changelogs** — Root and plugin changelogs: one “Changed” entry each for the type-hint refactor.

**Validation:** After each task, run the relevant pytest, `ruff check`, and mypy. Regression gate: any failing test not marked as expected failure must be fixed before completion.

---

## What was implemented

- **Task 01 (configure Ruff and mypy):** restful-api-tap `pyproject.toml` updated with `extend-select = ["UP006", "UP007", "UP045"]` and `target-version = "py312"`; `mypy.ini` set to `python_version = "3.12"`. target-gcs confirmed with existing UP and 3.12; no repo-root Ruff/mypy for scripts. Per-file or scoped handling used where needed so ruff/mypy pass before or during refactors.
- **Tasks 02–06 (tap source):** `streams.py`, `pagination.py`, `client.py`, `tap.py`, and `utils.py` refactored to 3.12-style hints; `typing` imports reduced to reserved symbols; no changes to `singer_sdk.typing` usage or behaviour.
- **Task 07 (tap tests):** Tap test modules (including `test_streams.py`) updated so optional parameters and annotations use `dict | None`, `Any | None`, and built-in generics; Ruff and pytest pass.
- **Task 08 (target-gcs tests):** target-gcs test files audited and any old-style hints converted; runtime code (`target.py`, `sinks.py`) left unchanged per plan.
- **Task 09 (scripts):** `scripts/list_packages.py` and `scripts/tests/test_list_packages.py` audited and aligned to 3.12 style; `from __future__ import annotations` retained; script tests pass.
- **Task 10 (changelogs):** Root `CHANGELOG.md` and plugin changelogs (`taps/restful-api-tap/CHANGELOG.md`, `loaders/target-gcs/CHANGELOG.md`) updated with “Changed” entries describing the type-hint refactor (3.12 style, built-in generics, pipe unions).

**Outcomes:** Type hints across the tap, target tests, and scripts use Python 3.12 conventions. Ruff and mypy configuration enforce the style. Existing tests pass with no behaviour change. Changelog entries document the refactor at root and per plugin.
