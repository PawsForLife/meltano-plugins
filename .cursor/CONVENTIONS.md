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
- **Components/libraries**: use discovery-oriented language — e.g. "each major package or library in the repository", "affected component(s) as identified from the plan". Do not hardcode component names (e.g. `python_service/`, `src/`, `webview-ui/`). Discover components from repo layout (e.g. top-level packages or directories, or as documented in README). For Singer/Meltano projects: refer to data extractors as **taps**, data loaders as **targets**; use **source** (where data is extracted from) and **destination** (where data is loaded to); use **streams** for named data sets. See `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md` when describing taps, targets, or pipelines.

## Git / Fork

- **Default push target**: This repo is a fork. `origin` points to [PawsForLife/tap-rest-api-msdk](https://github.com/PawsForLife/tap-rest-api-msdk). `git push` uses `push.default = current` and `push.remote = origin`, so branches push to the fork by default, not the parent (Widen) repo.
- To pull from the parent without pushing there, add it as a fetch-only remote:
  `git remote add upstream https://github.com/Widen/tap-rest-api-msdk.git` then
  `git remote set-url --push upstream no_push`.

## Overriding

To use different paths in a repo: document them in the project README or in `.cursor/rules`. Agents and commands should resolve placeholders using those conventions when present.
