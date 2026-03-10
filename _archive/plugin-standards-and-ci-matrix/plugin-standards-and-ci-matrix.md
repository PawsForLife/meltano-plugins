# Archive: Plugin standards and CI matrix

## The request

The repo is a monorepo of Meltano/Singer plugins (taps and loaders). Each plugin lives in its own directory (e.g. `taps/restful-api-tap/`, `loaders/gcs-loader/`) and has a `pyproject.toml`. The feature requested:

- **Standards**: All plugins must comply with ruff and mypy. Each plugin must have an `install.sh` that: ensures `uv` is present; clears virtual environment and cache on run; installs the package in editable mode with dev and testing dependencies; runs pytest (and ruff/mypy). Tests must live at package root (e.g. `tests/` beside `pyproject.toml`), not inside the source package.
- **Discovery**: A Python script under `scripts/` must print a list of all package paths (directories containing `pyproject.toml`), one per line, for use by CI.
- **CI**: A GitHub workflow must use that script to build a matrix of package paths and, for each path, run the plugin’s install (uv-based) and pytest.

**Testing needs**: Manual or CI: run the script from repo root and confirm output lists all package paths. CI: workflow runs for each package; each job runs install and pytest; all jobs pass when plugins are compliant. Per-plugin: `./install.sh` in each package root passes (ruff, mypy, pytest).

---

## Planned approach

**Chosen solution**: Internal Python script (pathlib, stdlib only) in `scripts/list_packages.py`; one GitHub Actions workflow with a discover job and a matrix test job.

- **Discovery script**: Optional `ROOT` argument (default cwd). Walk from root; for each directory containing `pyproject.toml`, emit its path relative to root. Exclude `.git`, `.venv`, `_archive`, `node_modules`. Sort and print one path per line; exit 0. Stdlib only; no PyPI deps.
- **CI matrix**: Job 1 (discover): checkout, run script, convert stdout to JSON `{"path": ["path1", "path2", ...]}`, set as job output `packages`. Job 2 (test): `needs: discover`, `strategy.matrix: ${{ fromJson(needs.discover.outputs.packages) }}`; for each slice, run `bash install.sh` in `working-directory: matrix.path`. Success = install.sh exit code.
- **Plugin contract**: `install.sh` is idempotent from plugin dir: uv present, clean venv/cache, editable install with dev deps, run pytest and ruff and mypy; exit code = last critical step (pytest).

**Task breakdown** (execution order): (01) Discovery script tests (TDD, `scripts/tests/`); (02) Discovery script implementation; (03) gcs-loader — move tests from `target_gcs/tests/` to package-root `tests/`; (04) gcs-loader — add ruff and mypy to install.sh; (05) restful-api-tap — add direct pytest, ruff, mypy to install.sh (tox optional); (06) GitHub workflow (discover + matrix test); (07) Documentation (monorepo README, both plugin READMEs).

---

## What was implemented

All seven tasks were completed.

1. **Discovery script tests** — `scripts/` and `scripts/tests/` created. Black-box tests in `scripts/tests/test_list_packages.py` for: no packages, one package, multiple (sorted), excluded dirs, nested path, invalid root. Run via `pytest scripts/tests` from repo root. TDD red then green once script existed.

2. **Discovery script** — `scripts/list_packages.py` implemented: optional ROOT (default cwd), exclusion set, walk with pathlib, sort, one path per line to stdout, exit 0; invalid root exits non-zero. Stdlib only; module docstring documents usage and exclusions.

3. **gcs-loader test move** — Tests moved from `target_gcs/tests/` to `loaders/gcs-loader/tests/` (`test_core.py`, `test_sinks.py`); imports remain `from target_gcs...`. Old test dir removed. README updated to reference package-root `tests/`.

4. **gcs-loader install.sh** — Ruff (check + format --check) and mypy added; order ruff → mypy → pytest; script comment updated. Exit code reflects pytest.

5. **restful-api-tap install.sh** — Direct `uv run pytest`, ruff, and mypy added; tox removed from primary contract. Script comment states install.sh runs pytest, ruff, and mypy.

6. **GitHub workflow** — `.github/workflows/plugin-matrix.yml` added. Discover job: checkout, setup Python, run `scripts/list_packages.py`, convert output to JSON matrix, set output `packages`; optional step runs script tests. Test job: matrix from discover output; each job runs `bash install.sh` in `matrix.path`. Triggers: push and pull_request with path filters (scripts/, taps/, loaders/, .github/).

7. **Documentation** — `docs/monorepo/README.md` updated with “CI and plugin standards” (matrix over pyproject.toml dirs, install.sh contract, root-level `tests/`). gcs-loader and restful-api-tap READMEs updated: test location and install.sh behaviour (pytest, ruff, mypy); CI relies on install.sh.

**Outcome**: One discovery script, one CI workflow that discovers and tests every plugin via install.sh; both plugins conform to the standard (root-level tests, install.sh runs uv, pytest, ruff, mypy). See CHANGELOG.md for the same feature listed under [Unreleased].
