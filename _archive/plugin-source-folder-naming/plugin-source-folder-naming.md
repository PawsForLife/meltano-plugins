# Plugin source folder naming — archive summary

## The request

Plugin directories use hyphenated names (`restful-api-tap`, `gcs-loader`) while Python source packages used different names (`tap_rest_api_msdk`, `target_gcs`). The goal was a single rule: source folder and package name = plugin directory name with dashes → underscores (`restful_api_tap`, `gcs_loader`), with provenance kept in docs (e.g. "formerly tap_rest_api_msdk"). Testing: all existing tests, ruff, mypy, and each plugin’s `install.sh` must pass.

## Planned approach

- **Solution:** Internal refactor only. Per plugin: rename source dir to underscore form of plugin dir; update pyproject.toml (packages, script module path, ruff known-first-party where present); update all imports and test patch paths; update install.sh, tox.ini (tap only), meltano.yml; update README and AI_CONTEXT with new names and a short provenance note. Pip/CLI names (`tap-rest-api-msdk`, `target-gcs`) unchanged.
- **Order:** restful-api-tap first (tasks 01–05: rename dir → pyproject → imports → scripts/config → docs), then gcs-loader (06–10: same sequence). Validate (pytest, ruff, mypy, install.sh) after scripts/config in each plugin.
- **Tasks:** 10 task docs in `_features/plugin-source-folder-naming/tasks/` with matching plans in `plans/tasks/`.

## What was implemented

- **restful-api-tap:** `tap_rest_api_msdk/` renamed to `restful_api_tap/`. pyproject.toml (packages, script path, isort known-first-party), all source and test imports, install.sh, tox.ini, meltano.yml updated. README and docs/AI_CONTEXT updated; provenance note added; AI_CONTEXT component title and tags updated to `restful_api_tap` (formerly `tap_rest_api_msdk`).
- **gcs-loader:** `target_gcs/` renamed to `gcs_loader/`. pyproject.toml (packages, script path), gcs_loader/target.py and test imports/patch paths, install.sh, meltano.yml, README updated; provenance note added.
- **Validation:** Script tests, restful-api-tap `install.sh`, and gcs-loader `install.sh` all pass. CHANGELOG updated with a bullet under [Unreleased] referencing this archive.
