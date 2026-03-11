# Task 03: Root `.pre-commit-config.yaml`

## Background

Root pre-commit must trigger the wrapper script so that ruff and mypy (and optionally pytest) run per plugin using each plugin's venv. This is done via a single local hook (`repo: local`, `language: system`) whose entry points to `scripts/run_plugin_checks.sh`. This task depends on task 01 (wrapper script) existing and being executable. Do not remove or alter `loaders/target-gcs/.pre-commit-config.yaml`; it remains optional for single-plugin workflows.

## This Task

- **Create** `.pre-commit-config.yaml` at repository root.
- **Content**: Minimal `repos:` list with one entry:
  - `repo: local`
  - `hooks`: one hook with `id` (e.g. `plugin-checks`), `name` (e.g. `Run plugin checks (ruff, mypy)`), `entry` pointing to the wrapper script (e.g. `scripts/run_plugin_checks.sh` or `bash scripts/run_plugin_checks.sh` if needed), `language: system`, `pass_filenames: false`, and either `files: '^taps/|^loaders/'` or `always_run: true` so the hook runs when relevant files change or on every commit.
- Optional: one-line comment that the hook runs plugin checks via the wrapper script.

## Testing Needed

- No new application unit tests. Validation is behavioural: after root `./install.sh` has been run, execute `pre-commit run --all-files` from repo root and expect exit 0 when all plugin checks pass; expect non-zero when a plugin lacks `.venv` or a check fails. Do not assert hook invocation counts or internal behaviour.
