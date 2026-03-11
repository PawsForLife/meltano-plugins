# Plugin matrix unit tests workflow

## The request

The plugin-matrix workflow ran each discovered plugin's `install.sh` in CI. At least one plugin's install script runs the UV installer with an interactive prompt ("Press Enter to run installer..."), which causes the job to hang and exit with code 1 in GitHub Actions. The feature requested: rename the workflow so its purpose is explicit (running unit tests over plugins), run on self-hosted runners, and perform the same logical steps as `install.sh` inline so CI is non-interactive.

## Planned approach

- **Solution**: Use `astral-sh/setup-uv` in the workflow and inline environment setup and test steps (no `install.sh`).
- **Changes**: Rename workflow to "Plugin unit tests (matrix)"; set `runs-on: self-hosted` for both `discover` and `test` jobs; in the test job, add steps for setup-python 3.12, setup-uv, then with `working-directory: ${{ matrix.path }}`: `uv venv --python 3.12`, `uv sync --extra dev`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, `uv run pytest`. Triggers and matrix discovery left unchanged.
- **Task**: Single task — update `.github/workflows/plugin-matrix.yml` (rename, runs-on, replace single install step with the inline steps).

## What was implemented

- **File modified**: `.github/workflows/plugin-matrix.yml`
- **Rename**: `name` set to "Plugin unit tests (matrix)" with a short top comment.
- **Runners**: Both jobs use `runs-on: self-hosted` instead of `ubuntu-latest`.
- **Test job**: The step that ran `bash install.sh` was replaced by: checkout; Set up Python 3.12 (`actions/setup-python@v5`); Install UV (`astral-sh/setup-uv@v4`); then, with `working-directory: ${{ matrix.path }}`, steps for create venv + `uv sync --extra dev`, ruff check, ruff format check, mypy, pytest. Job fails if pytest fails.
- **Verification**: No new unit tests; confirmation is that the workflow runs in CI and matrix jobs complete without interactive prompts. Script and plugin test suites were run locally and passed.
