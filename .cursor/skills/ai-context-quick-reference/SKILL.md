---
name: ai-context-quick-reference
description: Guides the ai-context-writer in maintaining a concise cheat sheet of environment, commands, runtime entry points, and troubleshooting. Use when creating or updating the quick reference AI context file.
---

# AI Context Quick Reference Skill

## Purpose

Help the `ai-context-writer` subagent produce `{context_docs_dir}/AI_CONTEXT_QUICK_REFERENCE.md` (default: `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md`) as a **high-signal, low-noise** reference for other agents.

This file is a **cheat sheet**, not a full architecture document. It should be safe to scan quickly when starting any task.

## Sources to Read

Before updating the quick reference, read (as needed):

- `@README.md` — project summary, goals, and high-level architecture
- `@{context_docs_dir}/AI_CONTEXT_REPOSITORY.md` — deeper architecture and entry points (if present)
- Project source and test layout — to confirm entry points and commands
- `@.cursor/rules/environment.mdc` — environment and tooling expectations
- `@.cursor/rules/documentation.mdc` and `@.cursor/rules/content_length.mdc` — style and length rules

Prefer **targeted reads** over exhaustive scans; this document must stay short.

## Required Sections

The target file must contain, at minimum:

1. **Metadata** — Version, Last Updated (ISO date), Tags (include `quick-reference`), Cross-References to other AI context files
2. **Project Summary** — One-paragraph description of purpose; bullet list of main components
3. **Environment & Versions** — Supported language/runtime versions; package managers; pointers to project config
4. **Key Commands (Shell)** — Setup/install; test; lint; quality gates that should pass before merging
5. **Runtime Entry Points** — How to run the application or main components (from project layout). For Singer/Meltano: how to run taps and targets (config file, state file, Catalog); use glossary terms per `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md`.
6. **Core Interfaces (Quick View)** — Brief view of main APIs or protocols if relevant
7. **Frequently Used Imports** — Short code blocks for typical imports (if applicable)
8. **Quick Troubleshooting Hints** — Common issues with concise bullet-point checks and actions

## Style & Constraints

- Keep sections **short and scannable**: bullets preferred over paragraphs; code fences for commands and imports
- Do **not** duplicate long explanations from the repository doc; link to it instead
- Assume a **developer / AI agent** reader
- Keep the file **well under** the content length limit

## Update Strategy

When modifying the quick reference: preserve existing structure where possible; update version and last-updated date; refresh commands and entry points if project tooling changes; ensure cross-references point to valid files.
