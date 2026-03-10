# Cursor configuration

This folder contains Cursor agents, commands, rules, skills, and workflows used for feature development, bug fixing, and AI context documentation. All paths and component names are **generic** and convention-based so this config can be reused across repositories.

## Path conventions

Path placeholders and discovery rules are defined in **[CONVENTIONS.md](CONVENTIONS.md)**. Defaults include:

- `{features_dir}` — feature request docs and planning (default: `_features`)
- `{bugs_dir}` — bug investigation and fix artifacts (default: `_bugs`)
- `{archive_dir}` — completed feature/bug artifacts (default: `_archive`)
- `{context_docs_dir}` — AI/context documentation output (default: `docs/AI_CONTEXT`)
- `{scratchpad}` — handoff file for pipeline phases (default: `.cursor/scratchpad.md`)

To use different paths in a repo, document them in the project README or in `.cursor/rules`; agents and commands resolve placeholders using those conventions.

## Contents

- **agents/** — Personas for research, planning, implementation, debugging, task decomposition, and AI context writing
- **commands/** — Orchestrator commands (e.g. `update_context`, `feature-pipeline`, `bug-pipeline`, `commit`)
- **rules/** — Project rules (environment, development practices, documentation, content length)
- **skills/** — Skills for the ai-context-writer (quick reference, repository, patterns, per-component; when documenting taps/targets or pipelines, terminology follows the project glossary in `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md`)
- **workflows/** — Phase workflows invoked by pipeline commands; path placeholders are defined in CONVENTIONS.md

## Usage

Use the pipeline commands from Composer (e.g. `/feature-pipeline`, `/bug-pipeline`, `/update_context`) rather than invoking individual workflow files. See CONVENTIONS.md for overriding path defaults.
