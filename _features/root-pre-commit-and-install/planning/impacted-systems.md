# Impacted Systems — root-pre-commit-and-install

## Summary

This feature adds root-level automation (root `install.sh` and root `.pre-commit-config.yaml`) to bootstrap and run lint/type-check/test across all plugins. The following existing systems are impacted; no plugin application code or tests are modified.

---

## 1. Repository root

| Aspect | Current state | Impact |
|--------|----------------|--------|
| **Root install** | No root `install.sh`; each plugin is bootstrapped only from its own directory. | New root `install.sh` will be added; existing behaviour per plugin unchanged. |
| **Root pre-commit** | No root `.pre-commit-config.yaml`. | New root `.pre-commit-config.yaml` will run ruff, mypy (and optionally pytest) per plugin using each plugin’s venv. |

---

## 2. Discovery and CI

| Component | Current state | Impact |
|-----------|----------------|--------|
| **scripts/list_packages.py** | Discovers directories containing `pyproject.toml` under a given root; used by CI to build the matrix. Excludes `.git`, `.venv`, `_archive`, `node_modules`. | May be reused by root `install.sh` and/or root pre-commit to discover plugin directories. No change required to the script unless we standardise on it for discovery (then it remains as-is). |
| **.github/workflows/plugin-unit-tests.yml** | Discover job runs `list_packages.py --json`; test job runs per matrix path with `working-directory: ${{ matrix.path }}`, runs uv venv, uv sync, ruff, ruff format --check, mypy, pytest. | No direct code change. Root pre-commit and root install align behaviour with CI (same tools, per-plugin venv). CI remains the regression gate for PRs. |

---

## 3. Per-plugin assets

| Component | Current state | Impact |
|-----------|----------------|--------|
| **taps/restful-api-tap/install.sh** | Creates `.venv` with Python 3.12, `uv sync --extra dev`, then ruff check, ruff format --check, mypy `restful_api_tap`, pytest. Exit code = pytest. | Invoked by root `install.sh`; no change to script content. Must remain runnable from plugin directory. |
| **loaders/target-gcs/install.sh** | Same pattern; mypy target is `gcs_target`. | Same as above. |
| **loaders/target-gcs/.pre-commit-config.yaml** | Exists; Ruff only (ruff-check, ruff-format). No mypy. | Decision: either remove (root becomes single source of truth) or keep as optional local override. Root config will run ruff + mypy (and optionally pytest) per plugin with that plugin’s venv, so root config supersedes plugin-level for repo-wide commits. |

---

## 4. Documentation

| Document | Current state | Impact |
|----------|----------------|--------|
| **README.md** | Describes plugin install via Meltano only; no root bootstrap or pre-commit. | Add section for repo contributors: run root `./install.sh` to bootstrap all plugins; install pre-commit and run `pre-commit install` for git hooks; optionally document `pre-commit run --all-files`. |
| **docs/monorepo/README.md** | States CI discovers packages via `scripts/list_packages.py` and that each plugin has `install.sh` (uv, pytest, ruff, mypy). | Add that root `install.sh` runs each plugin’s `install.sh` and that root pre-commit runs ruff/mypy (and optionally pytest) per plugin. |
| **docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md** | Lists per-plugin commands (e.g. from `taps/restful-api-tap/` or `loaders/target-gcs/`); “No repo-wide install.sh”. | Update to describe root `install.sh` and root pre-commit; keep per-plugin commands for single-plugin workflows. |

---

## 5. Interfaces and behaviour

- **Plugin interface**: Each plugin’s `install.sh` is invoked from its directory; it is not passed arguments. Root `install.sh` will `cd` into each discovered plugin dir and run `./install.sh`; failure in one plugin can be defined as “exit non-zero and optionally stop” (TBD in implementation).
- **Pre-commit interface**: Hooks run from repo root. Each hook that runs per-plugin must use that plugin’s `.venv` (e.g. `plugin_dir/.venv/bin/ruff`) and correct working directory so that ruff/mypy see the right `pyproject.toml` and source tree. Plugin mypy targets differ (e.g. `restful_api_tap` vs `gcs_target`) and must be derived from plugin path or config.
- **Discovery**: Plugin list can come from (a) globs such as `taps/*/`, `loaders/*/` with existence of `install.sh` or `pyproject.toml`, or (b) `scripts/list_packages.py`. Using `list_packages.py` keeps one source of truth with CI.

---

## 6. Out of scope (no impact)

- Application or test code under `taps/` and `loaders/` (no changes).
- Meltano usage or plugin definitions (`meltano.yml`, `pip_url`, etc.).
- `scripts/list_packages.py` logic or output format (unless we add a mode for pre-commit usage).
- Other workflows under `.github/workflows/` (e.g. `script-tests.yml`).
