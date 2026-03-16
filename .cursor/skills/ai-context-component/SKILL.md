---
name: ai-context-component
description: Guides the ai-context-writer in documenting a single component (name and path provided by the orchestrator). Use when creating or updating per-component AI context files.
---

# AI Context Component Skill

## Purpose

Help the `ai-context-writer` subagent create and maintain **one** component-level context document: `{context_docs_dir}/AI_CONTEXT_{COMPONENT_NAME}.md`.

The orchestrator provides:
- **Component name** (e.g. for the filename and headings)
- **Component path** (directory or package to document)

Use these to discover entry points and key files; do not assume project-specific file or type names.

## Sources to Read

Before updating the component context:

- The component directory at the given path — entry points, main modules, public API
- Tests that target this component (if present). Unit tests live under `tests/unit/` mirroring the source path, with filenames `test_{module}.py` (e.g. `paths/simple.py` → `tests/unit/paths/test_simple.py`).
- Existing `@{context_docs_dir}/AI_CONTEXT_REPOSITORY.md` for overall architecture
- Any existing `AI_CONTEXT_{COMPONENT_NAME}.md` for this component

Use the code as **ground truth**; do not speculate about behavior that is not implemented.

## Required Sections

Include at least:

1. **Metadata** — Version, Last Updated (ISO date), Tags (include component name), Cross-References to repository, quick reference, and related component docs
2. **Module Overview** — Brief description of each core module or file and its responsibility
3. **Public Interfaces** — Main types, functions, or APIs; key fields and contracts
4. **Lifecycle / Entry Points** — How the component is started, used, and shut down (as applicable)
5. **Extension Points** — Where to add new behavior or plug in new functionality
6. **Examples** — Short input/output or usage examples where they clarify behavior

## Style & Constraints

- When the component is a **tap** (Singer extractor) or **target** (Singer loader), use glossary terminology: tap/target, source/destination, streams, SCHEMA/RECORD/STATE, config file, state file, Catalog, Discovery, replication method, replication key, bookmark (see `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md`).
- Focus on **behavior and integration points**, not generic concepts
- Use concise, structured sections; avoid long prose
- Include short code snippets or type definitions when they clarify contracts
- Keep the file under the content length limit; split if the component grows substantially

## Update Strategy

When the component changes: update module overview and public interfaces; adjust lifecycle and extension points; refresh examples; bump version and last-updated metadata.
