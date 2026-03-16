# Archive: Normalise plugin source folders

## The request

**Background:** Plugin directories use hyphenated names (e.g. `target-gcs`, `restful-api-tap`). Source package names inside them were inconsistent: some used the plugin name with hyphens replaced by underscores (e.g. `restful_api_tap`), while `loaders/target-gcs` used `gcs_target`. That made it impossible to derive the source folder from the plugin folder name by a single rule and forced special-case logic in tooling and docs.

**Goal:** Establish one rule for all plugins: **source package name = plugin directory name with all hyphens replaced by underscores** (e.g. `target-gcs` → `target_gcs`). The only plugin that violated this was `loaders/target-gcs`; its source folder had to change from `gcs_target` to `target_gcs`. All references (imports, entry points, namespace, scripts, CI, docs) were to be updated accordingly, and discovery logic simplified to a single derivation rule with no per-plugin exceptions.

**Testing needs:** No new tests. Existing tests (pytest, ruff, mypy) had to pass after the rename and reference updates. Validation: run full project test suite and lint/type checks from repo root and from `loaders/target-gcs/`; confirm no remaining references to `gcs_target` except in CHANGELOG or migration notes.

---

## Planned approach

**Chosen solution:** Internal rename and reference update only (Option A). Rename `loaders/target-gcs/gcs_target/` to `target_gcs/` and update all references to `target_gcs`. Simplify discovery so the mypy/source package name is derived by: last path component with `-` replaced by `_`. No external tools or new behaviour; public API (CLI name `target-gcs`, Meltano plugin name, config schema) unchanged.

**Task breakdown (execution order 01 → 02 → 03 → 04 → 05):**

1. **01-rename-source-directory** — Rename `loaders/target-gcs/gcs_target/` to `loaders/target-gcs/target_gcs/`. No file content changes.
2. **02-update-plugin-config** — Update `pyproject.toml` (scripts entry point and wheel packages), `meltano.yml` (namespace), `install.sh` (mypy target) to use `target_gcs`.
3. **03-update-python-imports-and-tests** — Update all Python imports and test patch paths in the plugin from `gcs_target` to `target_gcs` (source: `target.py`; tests: `__init__.py`, `test_core.py`, `test_sinks.py`, `test_partition_key_generation.py`).
4. **04-update-repository-tooling** — In `scripts/run_plugin_checks.sh`, replace `get_mypy_package()` with a single rule: `comp="${path##*/}"; echo "${comp//-/_}"`. In `.github/workflows/plugin-unit-tests.yml`, derive `mypy_pkg` the same way and remove plugin-specific case blocks.
5. **05-update-documentation** — Update plugin README and CHANGELOG; all `docs/AI_CONTEXT/` files and root CHANGELOG to use `target_gcs` and document the naming rule; add migration note for namespace and verification commands.

**Success criteria:** All existing tests pass; ruff, mypy, pytest pass from repo root and from `loaders/target-gcs/`; no `gcs_target` references except in CHANGELOG/migration text; run_plugin_checks.sh and CI use the single derivation rule with no target-gcs or target-* exceptions.

---

## What was implemented

All five tasks were completed in order.

- **Task 01:** Directory `loaders/target-gcs/gcs_target/` was renamed to `loaders/target-gcs/target_gcs/`. The package layout is `target_gcs/__init__.py`, `target_gcs/target.py`, `target_gcs/sinks.py`.

- **Task 02:** Plugin config was updated: `pyproject.toml` entry point and wheel packages set to `target_gcs`; `meltano.yml` namespace set to `target_gcs`; `install.sh` mypy invocation changed to `uv run mypy target_gcs`.

- **Task 03:** All Python imports and test patches were updated from `gcs_target` to `target_gcs` in the source and in tests (`__init__.py`, `test_core.py`, `test_sinks.py`, `test_partition_key_generation.py`). Pytest, ruff, and mypy pass from `loaders/target-gcs/`.

- **Task 04:** Repository tooling was simplified: `get_mypy_package()` in `scripts/run_plugin_checks.sh` and the Mypy step in `.github/workflows/plugin-unit-tests.yml` now derive the package name from the last path component with hyphens replaced by underscores; plugin-specific case blocks were removed.

- **Task 05:** Documentation was updated: plugin README and CHANGELOG use `target_gcs` and the correct mypy command; AI context docs (QUICK_REFERENCE, target-gcs component, PATTERNS, REPOSITORY) use `target_gcs` throughout and state the naming rule; root CHANGELOG includes a migration note (namespace `target_gcs`, re-run `meltano install`, verification command `mypy target_gcs`).

**Outcomes:** The single rule (source package = plugin directory name with `-` → `_`) is applied consistently. No per-plugin exceptions remain in scripts or CI. The target-gcs loader (Singer target) is now aligned with the same pattern as the restful-api-tap extractor (tap). Users upgrading are directed via CHANGELOG to update `meltano.yml` namespace to `target_gcs` and re-run `meltano install`.
