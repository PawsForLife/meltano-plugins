# Implementation Plan — Overview: root-pre-commit-and-install

## Purpose

Add root-level automation so contributors can bootstrap all plugins and run lint/type-check (and optionally tests) from the repository root before push. No changes to plugin application or test code; only new root scripts and config plus documentation updates.

## Objectives

1. **Root `install.sh`**: One command at repo root discovers plugin directories (via `scripts/list_packages.py`) and runs each plugin's `./install.sh`. Failure handling: stop on first failure for clear feedback.
2. **Root `.pre-commit-config.yaml`**: Single local hook that invokes a wrapper script; the script discovers plugins and runs ruff (check + format) and mypy per plugin using that plugin's `.venv`. Optionally run pytest (same hook or pre-push; implementation choice).
3. **Wrapper script**: e.g. `scripts/run_plugin_checks.sh` — discovers plugins via `list_packages.py`, runs per-plugin checks with correct cwd and mypy package name (derived from directory name with optional fallback map).
4. **Documentation**: README, docs/monorepo, and AI_CONTEXT_QUICK_REFERENCE updated so contributors know to run root `./install.sh`, install pre-commit, and run `pre-commit install`.

## Success Criteria

- Root `./install.sh` runs and all plugin installs/tests pass.
- `pre-commit run --all-files` succeeds.
- New plugins discovered by `list_packages.py` are included automatically (no manual config edits).
- Regression gate remains existing plugin test suites and CI; no new application unit tests required.

## Key Requirements

- **Discovery**: Reuse `scripts/list_packages.py` (invoke from repo root with `ROOT=.` or equivalent); output is one path per line. Same source of truth as CI.
- **Plugin contract**: Each plugin's `install.sh` is invoked from its directory with no arguments; root script `cd`s into each path and runs `./install.sh`.
- **Pre-commit**: Hooks run from repo root; each plugin's checks use that plugin's `.venv` (e.g. `plugin_dir/.venv/bin/ruff`) and correct working directory so tool config (e.g. `pyproject.toml`) is respected.
- **Mypy package name**: Derived from plugin directory name (e.g. `restful-api-tap` → `restful_api_tap`, `target-gcs` → `gcs_target`) with an optional fallback map for exceptions.

## Constraints

- No modification to plugin application or test code under `taps/` and `loaders/`.
- No new CI jobs; existing `.github/workflows/plugin-unit-tests.yml` unchanged.
- Scripts must be runnable from repo root; Bash and Python (for `list_packages.py`) are available.
- Document that contributors must run root `./install.sh` before pre-commit hooks (so `.venv` exists per plugin).

## Relationship to Existing Systems

- **list_packages.py**: Consumed by root `install.sh` and wrapper script; no changes to script logic or output format unless we add an optional mode (e.g. line vs JSON); default line output is sufficient.
- **Per-plugin install.sh**: Invoked as-is; no changes.
- **CI**: Continues to use `list_packages.py --json` for matrix; root tooling uses line output. Behaviour aligns (same tools, per-plugin venv).
- **Plugin-level pre-commit**: e.g. `loaders/target-gcs/.pre-commit-config.yaml` can remain as optional for single-plugin workflows; root config is the standard for whole-repo commits.

## Out of Scope

- Meltano usage or plugin definitions (`meltano.yml`, `pip_url`).
- Changes to `list_packages.py` discovery logic or excludes.
- Application or test code inside plugin packages.

