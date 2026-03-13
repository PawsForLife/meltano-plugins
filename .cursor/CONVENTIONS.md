# Cursor Path Conventions

Path placeholders used by agents, commands, and workflows in this folder. Defaults apply unless the project overrides them (e.g. in README or `.cursor/rules`).

## Placeholders

| Placeholder | Purpose | Default |
| ---------- | -------- | ------- |
| `{features_dir}` | Feature request docs and planning | `_features` |
| `{bugs_dir}` | Bug investigation and fix artifacts | `_bugs` |
| `{archive_dir}` | Completed feature/bug artifacts | `_archive` |
| `{context_docs_dir}` | AI/context documentation output | `docs/AI_CONTEXT` |
| `{scratchpad}` | Handoff file for pipeline phases | `.cursor/scratchpad.md` |

## Usage

- In agents, commands, and workflows: use these placeholders (or the default paths) so paths stay consistent and overridable.
- **Test layout**: One test file per source module; unit vs integration scope and thin integration tests per `.cursor/rules/development_practices.mdc`.
- **Components/libraries**: use discovery-oriented language — e.g. "each major package or library in the repository", "affected component(s) as identified from the plan". Do not hardcode component names (e.g. `python_service/`, `src/`, `webview-ui/`). Discover components from repo layout (e.g. top-level packages or directories, or as documented in README). For Singer/Meltano projects: refer to data extractors as **taps**, data loaders as **targets**; use **source** (where data is extracted from) and **destination** (where data is loaded to); use **streams** for named data sets. See `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md` when describing taps, targets, or pipelines.

## Git / Fork

- **Default push target**: This repo is a fork. `origin` points to [PawsForLife/tap-rest-api-msdk](https://github.com/PawsForLife/tap-rest-api-msdk). `git push` uses `push.default = current` and `push.remote = origin`, so branches push to the fork by default, not the parent (Widen) repo.
- To pull from the parent without pushing there, add it as a fetch-only remote:
  `git remote add upstream https://github.com/Widen/tap-rest-api-msdk.git` then
  `git remote set-url --push upstream no_push`.

## Changelogs

- **Root changelog** (`CHANGELOG.md` at repo root): Repo-wide changes only — scripts, CI, root tooling (e.g. `install.sh`, `run_plugin_checks.sh`, `list_packages.py`), pre-commit, docs under `docs/` (e.g. monorepo, AI context), root README, Cursor workflows/commands/agents, and changes that affect multiple plugins or have no single plugin. Uses **date-based** headings only (no version numbers): `## YYYY-MM-DD` (commit date). New entries go under the heading for the commit date; if that date section does not exist, add it at the top. The repo is “released” by pushing; no separate versioning.
- **Plugin changelog** (per plugin): Changes that affect only that plugin. Paths:
  - Tap: `taps/{tap_directory_name}/CHANGELOG.md` (e.g. `taps/restful-api-tap/CHANGELOG.md`)
  - Target: `loaders/{target_directory_name}/CHANGELOG.md` (e.g. `loaders/target-gcs/CHANGELOG.md`)
  Plugin changelogs may use version blocks (e.g. `## [Unreleased]`, `## [1.0.0]`) if the plugin is published with versions; otherwise use the same date-based format as the root.
- **Which to update**: From the task/plan, determine affected scope. Update the root changelog only for global scope; update the relevant plugin changelog(s) only for that plugin’s scope; update both only when a change has both global and plugin-specific parts.
- **One heading per type per section**: Under each root date (`## YYYY-MM-DD`) or plugin version block (e.g. `## [Unreleased]`, `## [1.0.0]`), each change type must appear at most once. Use a single `### Added`, `### Changed`, `### Fixed`, `### Removed`, or `### Breaking` per section; append new bullets under that heading. Do not add a second `### Fixed` (or other type) in the same section.

## Overriding

To use different paths in a repo: document them in the project README or in `.cursor/rules`. Agents and commands should resolve placeholders using those conventions when present.
