# Archive: Target Filenames and Glossary Alignment

## The request

**Background:** The project uses `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md` as the source of truth for Meltano and Singer terminology. Class names and prose were already aligned; **file names, module names, CLI/entry point names, and plugin identifiers** for targets under `loaders/` still used Meltano-style “loader” naming (e.g. `gcs-loader`, `gcs_loader`), which did not match the glossary or the main class name (`GCSTarget`).

**Goal:** For each target under `loaders/` (initially the GCS target), align file names, module/package names, CLI entry point, and plugin identifiers with (1) the glossary’s `target-<destination>` convention and (2) the main target class (e.g. `GCSTarget` → module `gcs_target`). All references (imports, docs, config samples, Meltano plugin name/namespace) were to be updated so the target continued to work and stayed consistent with the glossary.

**Scope:** One target package: `loaders/gcs-loader/` (GCS). Canonical names: CLI/plugin `target-gcs`, Python package `gcs_target`, top-level directory `loaders/target-gcs/`. Terminology rule (per research): Singer/spec/SDK use **target** for artifact naming; Meltano uses **loader** only for plugin type; project artifacts follow Singer → `target-<destination>`.

**Testing:** Full test suite per target (`uv run pytest` from package root); CLI run with new name (`target-gcs --config ...`); Meltano invocation with updated plugin name; grep for old names with no matches outside CHANGELOG or migration notes; CI/install scripts updated and passing.

---

## Planned approach

**Chosen solution:** Option A (full alignment) from planning: Python package `gcs_loader` → `gcs_target`, CLI/plugin `gcs-loader` → `target-gcs`, top-level directory `loaders/gcs-loader/` → `loaders/target-gcs/`. No new behaviour or interfaces; config schema, Singer I/O, and Meltano capabilities unchanged.

**Architecture:** Rename-and-reference only. Component layout after alignment: `loaders/target-gcs/` with package `gcs_target/` (target.py, sinks.py), entry point `target-gcs = "gcs_target.target:GCSTarget.cli"`, and `meltano.yml` with `name: target-gcs`, `namespace: gcs_target`. Class names `GCSTarget` and `GCSSink` retained; only module, CLI, and plugin names changed. CI uses `scripts/list_packages.py` for discovery; no hardcoded loader path.

**Task breakdown (three tasks, strict order):**

1. **Task 01 — Rename package and update loader dir (inside loaders/gcs-loader/):** Rename `gcs_loader/` → `gcs_target/`; set `GCSTarget.name = "target-gcs"` and imports to `gcs_target`; update `pyproject.toml` (name, packages, script), `meltano.yml` (name, namespace), `install.sh` (mypy target); update test imports and patch paths to `gcs_target.*`; run pytest, ruff, mypy from `loaders/gcs-loader/`. No doc or path changes outside the loader dir.

2. **Task 02 — Rename top-level dir and repo refs:** Rename `loaders/gcs-loader/` → `loaders/target-gcs/`; update root README, `docs/monorepo/README.md`, and all `docs/AI_CONTEXT/` files (paths, plugin name, entry point, mypy target, cross-links); rename `AI_CONTEXT_gcs-loader.md` → `AI_CONTEXT_target-gcs.md` and update its contents. Regression: run tests and tooling from `loaders/target-gcs/`; grep for old names only in CHANGELOG or migration notes.

3. **Task 03 — Update package docs and changelog:** Update `loaders/target-gcs/README.md` and `sample.config.json` (if needed) to use `target-gcs`, `gcs_target`, and `loaders/target-gcs/`; add root CHANGELOG entry describing the rename and that users must set `target-gcs` in `meltano.yml` and re-run `meltano install`; optionally update package CHANGELOG.

---

## What was implemented

All three tasks were completed; tests and quality checks passed (per pipeline scratchpad and repo state).

- **Task 01:** Python package renamed `gcs_loader` → `gcs_target`; CLI/plugin set to `target-gcs` in `pyproject.toml`, `GCSTarget.name`, and `meltano.yml`; imports, entry points, and test patch paths updated to `gcs_target`; `install.sh` and lockfile updated. Tests, ruff, and mypy run from the loader directory and pass.

- **Task 02:** Top-level directory renamed `loaders/gcs-loader/` → `loaders/target-gcs/`. Root README, `docs/monorepo/README.md`, and AI context docs (`AI_CONTEXT_QUICK_REFERENCE.md`, `AI_CONTEXT_REPOSITORY.md`, `AI_CONTEXT_PATTERNS.md`) updated for plugin name, paths, entry point, and cross-links. `AI_CONTEXT_gcs-loader.md` renamed to `AI_CONTEXT_target-gcs.md` with internal references updated. Verification from `loaders/target-gcs/` and grep for old names performed.

- **Task 03:** Package README and sample config updated to use `target-gcs`, `gcs_target`, and `loaders/target-gcs/`. Root CHANGELOG updated with an entry describing the rename and the required user action (update `meltano.yml` to `target-gcs`, re-run `meltano install`). Optional package CHANGELOG note applied if present.

**Outcome:** The GCS target is exposed as plugin `target-gcs` with package `gcs_target` under `loaders/target-gcs/`. No remaining references to `gcs-loader` or `gcs_loader` outside CHANGELOG or migration context. Config schema, CLI flags, and Singer I/O behaviour are unchanged; only names and paths align with the glossary and Singer convention.
