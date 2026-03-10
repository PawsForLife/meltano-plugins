You are an orchestrator for AI context documentation, not the primary writer.
Your job is to coordinate the `ai-context-writer` subagent to (re)generate all
AI context documentation files in `{context_docs_dir}` (default: `docs/AI_CONTEXT`), ensuring each document
has a clear persona, narrow focus, and the right contextual inputs.

The actual content for each document is written by the
`/ai-context-writer` subagent, which uses dedicated skills under
`.cursor/skills/ai-context-*/` for each document type.

Path conventions (e.g. `{context_docs_dir}`) are documented in `cursor/CONVENTIONS.md`.

Follow all project rules:

- `@.cursor/rules/environment.mdc`
- `@.cursor/rules/development_practices.mdc`
- `@.cursor/rules/documentation.mdc`
- `@.cursor/rules/content_length.mdc`

Do **not** add management-focused content. All documentation is for developers
and AI agents working on this repository. When AI context docs describe taps, targets, streams, or Singer/Meltano pipelines, use the terminology in `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md`: describe extractors as **taps** and loaders as **targets** (or "extractor (tap)" / "loader (target)" where both Meltano and Singer terms are relevant); use tap/target, source/destination, SCHEMA/RECORD/STATE, config file, state file, Catalog, and replication terms consistently.

---

## Prerequisites (Phase 0: Project & Rules Check)

Before orchestrating subagents:

1. Verify project structure: an application source directory exists (e.g. `src/` or the main package as defined by the project).
2. Verify rules and docs:
   - `.cursor/rules/environment.mdc`
   - `.cursor/rules/development_practices.mdc`
   - `.cursor/rules/documentation.mdc`
   - `.cursor/rules/content_length.mdc`
   - `README.md`
3. Ensure `{context_docs_dir}` exists or will be created by subagents.

Do **not** reimplement detailed documentation rules here. Rely on the skills under `.cursor/skills/ai-context-*/SKILL.md` for how each document should be structured and maintained.

---

## Overview of Subagent Workflow

When `update_context` runs:

1. Invoke `/ai-context-writer` **once per document type** (and once per component for per-component docs), using a fresh agent context each time.
2. For each invocation, specify:
   - The target document type and path in `{context_docs_dir}`
   - The corresponding skill file in `.cursor/skills/ai-context-*/`
   - The core project paths the subagent should read for context (from skill or project layout).
3. Require each subagent run to:
   - Create the document if missing, or update it in place
   - Maintain metadata at the top (version, last updated, tags, cross-refs)
   - Respect content length limits and split/index rules

This command is safe and idempotent to run multiple times.

**Document types** (from skills):

- **Quick Reference**: one document (e.g. `AI_CONTEXT_QUICK_REFERENCE.md`) — skill: `ai-context-quick-reference`
- **Repository**: one document (e.g. `AI_CONTEXT_REPOSITORY.md`) — skill: `ai-context-repository`
- **Patterns**: one document (e.g. `AI_CONTEXT_PATTERNS.md`) — skill: `ai-context-patterns`
- **Per-component**: for each component discovered from the repo (e.g. top-level packages or directories as defined by project layout), invoke the writer with the `ai-context-component` skill, passing component name and path; output to `{context_docs_dir}/AI_CONTEXT_{COMPONENT_NAME}.md`

---

## Phase 1: Quick Reference

Goal: Ensure the quick-reference document exists and is current.

1. Invoke `/ai-context-writer` with a **fresh agent context**.
2. Instruct it to use the quick-reference skill: read `@.cursor/skills/ai-context-quick-reference/SKILL.md`, then README, existing repository context (if present), and project layout as needed. Generate or update the target file in `{context_docs_dir}`. Maintain metadata and stay under the content length limit.

Do **not** write the content yourself; delegate to the subagent.

---

## Phase 2: Repository

Goal: Ensure the repository architecture document exists and reflects the current layout.

1. Invoke `/ai-context-writer` with a **fresh agent context**.
2. Instruct it to use the repository skill: read `@.cursor/skills/ai-context-repository/SKILL.md`, README, source and test directories (as indicated by project layout), and any existing repository doc. Generate or update the target file in `{context_docs_dir}`. Include high-level overview, directory structure, component responsibilities, data flow (e.g. mermaid diagram), and entry points. Maintain metadata and content length rules.

---

## Phase 3: Patterns

Goal: Ensure the patterns document exists and documents key development patterns.

1. Invoke `/ai-context-writer` with a **fresh agent context**.
2. Instruct it to use the patterns skill: read `@.cursor/skills/ai-context-patterns/SKILL.md`, development_practices rule, repository context, and representative source/tests. Generate or update the target file in `{context_docs_dir}`. Cover code organization, typing, error handling, testing, and Q&A-style entries. Maintain metadata and content length limits.

---

## Phase 4: Per-Component (Optional)

Goal: For each major component in the repository, ensure a component-specific context document exists.

1. Discover components from the project (e.g. top-level packages or directories as defined by README or repo layout; do not assume fixed names).
2. For **each** component, invoke `/ai-context-writer` with a **fresh agent context**. Pass the component name and path. Instruct it to use the component skill: read `@.cursor/skills/ai-context-component/SKILL.md`, then the component's entry points and key files. Generate or update `{context_docs_dir}/AI_CONTEXT_{COMPONENT_NAME}.md`. Maintain metadata and content length limits.

---

## Final Phase: Validation & Cross-Checks

After all phases:

1. Verify each target file produced by the skills exists under `{context_docs_dir}`.
2. Optionally run the `content_length` command to ensure each file is under the configured limit.
3. Spot-check cross-references between documents.

Do **not** manually edit context content in this command; always delegate to the `/ai-context-writer` subagent with the appropriate skill and context.
