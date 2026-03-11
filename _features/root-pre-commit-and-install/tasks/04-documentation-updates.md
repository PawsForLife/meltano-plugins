# Task 04: Documentation updates

## Background

Contributors must know to run root `./install.sh`, install pre-commit if needed, and run `pre-commit install`. The plan requires updates to README, docs/monorepo, and AI_CONTEXT_QUICK_REFERENCE. This task depends on tasks 01–03 being implemented (scripts and config exist) so that documentation accurately describes behaviour.

## This Task

- **README.md** (repository root): Add a short Development or Contributing section (or subsection under existing Contributing). Content: to bootstrap all plugins and git hooks, run `./install.sh` from the repository root; root install.sh runs each plugin's install.sh, then installs pre-commit if not present and runs `pre-commit install`; to check all files without committing, run `pre-commit run --all-files`; ensure root `./install.sh` has been run at least once so each plugin has a `.venv`.
- **docs/monorepo/README.md**: State that the repository provides a root **install.sh** that discovers plugin directories via `scripts/list_packages.py` and runs each plugin's `install.sh`; and that root **pre-commit** runs ruff, mypy (and optionally pytest) per plugin using that plugin's virtual environment, with discovery via the same `list_packages.py` as CI.
- **docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md**: Add root-level commands (or a "Repo root" subsection): root `./install.sh` (bootstrap all plugins), `pre-commit install` (install git hooks), `pre-commit run --all-files` (run all hooks). Retain existing per-plugin command tables for single-plugin workflows. Update any "No repo-wide install.sh" wording to state that root install.sh now exists.

## Testing Needed

- No automated tests for documentation. Verify that README, docs/monorepo, and QUICK_REFERENCE are consistent with the implementation (install.sh and pre-commit behaviour) and that wording is clear for contributors.
