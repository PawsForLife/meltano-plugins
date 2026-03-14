---
name: ai-context-repository
description: Guides the ai-context-writer in maintaining the repository architecture document: directory structure, component responsibilities, data flow, and extension points. Use when creating or updating the repository AI context file.
---

# AI Context Repository Skill

## Purpose

Help the `ai-context-writer` subagent generate and maintain `{context_docs_dir}/AI_CONTEXT_REPOSITORY.md` (default: `docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md`) as the **single source of truth** for:

- Overall architecture
- Directory and component layout
- Data flow between components (for Singer/Meltano: tap → target; source/destination; streams; config file, state file, Catalog per `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md`)
- High-level extension points

Other AI context documents (patterns, component-specific docs) should link back here for structure.

## Sources to Read

Before updating the repository document, read (as appropriate):

- `@README.md` — project purpose and high-level goals
- Project layout — discover components from repo structure (e.g. top-level packages or directories; do **not** assume fixed names like `python_service` or `webview-ui`)
- `@tests/` or project test layout — where tests live. When documenting: unit tests under `tests/unit/` mirroring source path; filenames `test_{module}.py`; global `conftest.py` and `files/` for fixtures and test data (see `@.cursor/CONVENTIONS.md`).
- `@.cursor/rules/environment.mdc` — structure and tooling expectations
- Existing `@{context_docs_dir}/AI_CONTEXT_REPOSITORY.md` (if present)

## Required Sections

At minimum, ensure the file contains:

1. **Metadata** — Version, Last Updated (ISO date), Tags (e.g. `architecture`, `repository`), Cross-References to quick reference, patterns, and component-specific AI context docs
2. **High-Level Overview** — Goal of the system in 1–2 paragraphs; summary of main components (discovered from layout)
3. **Directory Structure** — Annotated tree of important directories (source, tests, docs, `.cursor`, feature/bug dirs per conventions)
4. **Component Responsibilities** — For each major component discovered: what it does, key modules, main responsibilities
5. **Data Flow** — End-to-end flow where relevant; at least one **mermaid diagram** for the main happy path. When the repo has taps and targets, describe flow using glossary terms (tap, target, source, destination, streams, config file, state file, Catalog).
6. **Service/Module Boundaries & Dependencies** — Boundaries between components; key external libraries per component
7. **Entry Points & Extension Hooks** — How to run the system; where to plug in new behavior (as appropriate to the project)

## Style & Constraints

- Keep the document **architectural**, not tutorial-style
- Use **semantic headings** and short paragraphs
- Prefer diagrams and structured lists over long prose
- Avoid management or roadmap content; focus on **how the system is structured today**
- Keep under the content length limit; if it grows, split into sub-documents per `content_length` rules and provide an index

## Update Strategy

When the project structure or flow changes: update the directory tree; adjust component responsibilities and data flow; refresh diagrams; bump version/last-updated metadata; ensure cross-references to component docs remain valid.
