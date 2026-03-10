# Plugin class name alignment — Archive summary

## The request

Plugins used folder/slug names (e.g. `gcs-loader`, `restful-api-tap`) but exposed legacy class names and `name` values (`TargetGCS` / `"target-gcs"`, `TapRestApiMsdk` / `"tap-rest-api-msdk"`). The goal was to align class names and the `name` attribute with the plugin slug to improve consistency, discoverability, and Meltano UX. Scope: each plugin (loaders/gcs-loader, taps/restful-api-tap); impact on pyproject.toml, Python modules, tests, meltano.yml, and docs. Testing: all existing tests must pass; no remaining references to old class or `name` values.

## Planned approach

**Solution:** One-time per-plugin refactor: derive PascalCase class and slug from folder; set `name = "<slug>"`; update entry points, tests, meltano.yml, and docs. No new dependencies.

**Naming:** Slug from folder (e.g. `gcs-loader`, `restful-api-tap`). Class = PascalCase of slug (e.g. `GCSLoader`, `RestfulApiTap`). Acronyms (GCS, API) kept uppercase.

**Tasks:** (1) GCS loader: `TargetGCS` → `GCSLoader`, `name` → `"gcs-loader"`; update pyproject.toml, meltano.yml, tests, plugin README. (2) Restful API tap: `TapRestApiMsdk` → `RestfulApiTap`, `name` → `"restful-api-tap"`; rename shell script to `restful-api-tap.sh`; update pyproject.toml, meltano.yml, tests, plugin README, AI_CONTEXT. (3) Repo docs: root README and docs/monorepo — replace old plugin/executable names with `gcs-loader` and `restful-api-tap` in tables, YAML examples, directory layout, and pipeline examples.

## What was implemented

- **Task 01 (gcs-loader):** Class renamed to `GCSLoader`, `name` set to `"gcs-loader"`. Entry point, pyproject.toml, meltano.yml, tests, and plugin README updated. All tests pass.
- **Task 02 (restful-api-tap):** Class renamed to `RestfulApiTap`, `name` set to `"restful-api-tap"`. Shell script renamed to `restful-api-tap.sh`. Entry point, pyproject.toml, meltano.yml, tests, plugin README, and AI_CONTEXT docs updated. All tests pass.
- **Task 04 (repo docs):** Root README and docs/monorepo/README.md updated: plugins table, installation YAML, directory layout, version-pinning and pipeline examples now use `gcs-loader` and `restful-api-tap`. No code changes; verification grep and full test suite confirmed no regressions.

Singer SDK and Meltano interfaces unchanged; plugin identity remains `name` and entry point.
