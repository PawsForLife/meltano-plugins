# Pipeline Scratchpad

## Feature: typing-312-standards

- **Output directory:** `_features/typing-312-standards/planning/`
- **Key findings:** Impact is confined to tap (restful-api-tap) and loader (target-gcs) Python modules and tests; heaviest in `streams.py` and `pagination.py`. No new systems; refactor only. target-gcs already uses `Callable[...] | None` in places.
- **Selected solution:** Use built-in types (`dict`, `list`, etc.) and pipe unions (`X | Y`, `X | None`); keep `typing` only for `Any`, `Callable`, `Iterator`, `Generator`, `Iterable`, `cast` (and reserve `TypedDict`, `Protocol`, `TypeVar`). No external library. **Ruff/mypy:** Enable Ruff UP006, UP007, UP045 in each plugin (and scripts if applicable); set mypy `python_version = "3.12"` everywhere.
- **Pipeline State:** Phase 3 Complete; Phase 4 Complete (all task plans created)
- **Plan location:** `_features/typing-312-standards/plans/master/` (overview, architecture, interfaces, implementation, testing, dependencies, documentation).
- **Key decisions:** (1) Refactor order: config first (Phase 0), then tap, loader, scripts. (2) No `from __future__ import annotations` unless needed; scripts that already use it keep it. (3) Keep `typing` only for Any, Callable, Iterator, Generator, Iterable, cast; reserve TypedDict, Protocol, TypeVar. (4) Ruff: enable UP006, UP007, UP045 (or UP group); mypy: python_version 3.12 everywhere.
- **Tasks directory:** `_features/typing-312-standards/tasks/`
- **Task list file:** `_features/typing-312-standards/typing-312-standards-task-list.md`
- **Task count:** 10
- **Task Completion Status:** Task 01-configure-ruff-mypy completed, tests passing. Task 02-refactor-tap-streams completed, tests passing. Task 04-refactor-tap-client completed, tests passing. Task 03-refactor-tap-pagination completed, tests passing. Task 06 completed. Task 05 completed.
- **Execution Order:** 01-configure-ruff-mypy.md, 02-refactor-tap-streams.md, 03-refactor-tap-pagination.md, 04-refactor-tap-client.md, 05-refactor-tap-tap.md, 06-refactor-tap-utils.md, 07-refactor-tap-tests.md, 08-refactor-target-gcs-tests.md, 09-refactor-scripts.md, 10-update-changelogs.md
- **Task plan created:** 03-refactor-tap-pagination at plans/tasks/03-refactor-tap-pagination.md
- Task plan created: 02-refactor-tap-streams at plans/tasks/02-refactor-tap-streams.md
- Task plan created: 01-configure-ruff-mypy at plans/tasks/01-configure-ruff-mypy.md
- **Task plan created:** 04-refactor-tap-client at plans/tasks/04-refactor-tap-client.md
- Task plan created: 05-refactor-tap-tap at plans/tasks/05-refactor-tap-tap.md
- Task plan created: 06-refactor-tap-utils at plans/tasks/06-refactor-tap-utils.md
- Task plan created: 07-refactor-tap-tests at plans/tasks/07-refactor-tap-tests.md
- Task plan created: 08-refactor-target-gcs-tests at plans/tasks/08-refactor-target-gcs-tests.md
- Task plan created: 09-refactor-scripts at plans/tasks/09-refactor-scripts.md
- Task plan created: 10-update-changelogs at plans/tasks/10-update-changelogs.md
