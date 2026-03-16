# Archive: Python 3.12 Minimum

## The request

Align the repository so every plugin (taps and loaders) declares a minimum Python version of 3.12. The project standard is already Python 3.12; some plugins still allowed older versions (e.g. target-gcs used `>=3.8,<4.0`). The request was to update each such plugin’s `pyproject.toml` (`requires-python`, ruff `target-version`, mypy `python_version`), regenerate lockfiles, optionally modernise code for 3.12, remove or update conflicting standalone configs, and document the change in plugin and root changelogs. Validation: existing test suites and CI must pass on Python 3.12; no new tests required for the version bump.

## Planned approach

**Scope (from planning):** Only **target-gcs** needed changes; **restful-api-tap** already required 3.12. Impacted areas: target-gcs (pyproject, lockfile, optional code style, README, CHANGELOG), AI context docs (REPOSITORY, QUICK_REFERENCE), and root CHANGELOG. No new systems or runtime dependencies; optional follow-up: script or CI step to enforce `requires-python >= 3.12` for all plugins.

**Selected solution:** Tool-assisted internal updates. For target-gcs: set `requires-python = ">=3.12"` (or `">=3.12,<4.0"`), ruff `target-version = "py312"`, mypy `python_version = "3.12"`; regenerate `uv.lock`; run `ruff check --fix` and `ruff format`; optionally run `pyupgrade --py312-plus`. No new runtime deps; optional style modernisation (e.g. `T | None`) not mandatory for compliance. Validation script/CI left as optional follow-up.

**Implementation order (master plan and task list):**  
(1) Update target-gcs `pyproject.toml`.  
(2) Regenerate target-gcs `uv.lock`, sync venv (Python 3.12), run pytest, ruff, mypy—all must pass.  
(3) Optional: ruff check/format and optionally pyupgrade in target-gcs; re-run tests and linters.  
(4) Update docs (AI_CONTEXT_REPOSITORY, AI_CONTEXT_QUICK_REFERENCE, target-gcs README) and changelogs (target-gcs CHANGELOG, root CHANGELOG).  
(5) Final validation: root `install.sh` (if used) and full target-gcs test/lint/type run.  

**Interfaces:** No public API or config-schema changes; only supported Python version and tool config. Regression gate: existing tests plus `ruff check`, `ruff format --check`, and `mypy target_gcs`.

## What was implemented

- **Task 01 — Update pyproject:** target-gcs `loaders/target-gcs/pyproject.toml` updated: `requires-python` set to `">=3.12"` (or `">=3.12,<4.0"`), `[tool.ruff]` `target-version` to `"py312"`, `[tool.mypy]` `python_version` to `"3.12"`. No dependency or other section changes.

- **Task 02 — Lockfile and verify:** From `loaders/target-gcs/`, venv ensured at Python 3.12, `uv lock` run to regenerate `uv.lock`, `uv sync` (with dev extras as needed), then pytest, ruff check, ruff format check, and mypy run; updated `uv.lock` committed. No application code changes.

- **Task 03 — Optional code style:** Ruff check (with fix) and ruff format run in target-gcs; optionally pyupgrade for 3.12-plus syntax. Tests and linters re-run; no behaviour change, no new tests.

- **Task 04 — Documentation and changelogs:** AI context (REPOSITORY, QUICK_REFERENCE) updated so target-gcs is documented as Python ≥3.12; target-gcs README and CHANGELOG updated (minimum version 3.12, breaking-change entry); root CHANGELOG updated (repo standard Python 3.12 minimum, target-gcs requires 3.12). Optional checks for AI_CONTEXT_target-gcs and restful-api-tap README.

- **Task 05 — Final validation:** Root `./install.sh` (if used) and from `loaders/target-gcs/` full run of pytest, ruff check, ruff format check, and mypy; regression gate: no unmarked failing tests or checks.

**Outcome:** target-gcs declares and enforces Python 3.12 minimum; lockfile and tooling aligned; docs and changelogs state the repo standard and breaking change. restful-api-tap unchanged (already 3.12). Optional validation script/CI for future plugins was not part of the delivered scope.
