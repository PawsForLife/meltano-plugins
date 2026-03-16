---
name: ai-context-patterns
description: Guides the ai-context-writer in creating and maintaining the patterns document: code organization, typing, error handling, testing, data models, and validation. Use when generating or updating the patterns AI context file.
---

# AI Context Patterns Skill

## Purpose

Help the `ai-context-writer` subagent produce `{context_docs_dir}/AI_CONTEXT_PATTERNS.md` (default: `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md`) as a **pattern and convention guide**:

- How code is organized
- How data and types are modelled
- How errors, logging, and validation are handled
- How tests and TDD are approached

This document guides other agents in writing code that **fits the existing system**.

## Sources to Read

Before updating patterns, read (selectively):

- `@.cursor/rules/development_practices.mdc` — TDD, models, DI, validation rules
- `@.cursor/rules/environment.mdc` — tooling and layout assumptions
- Representative source directories — code organization, types, error handling
- `@tests/` or project test layout — how tests are structured and named. Document: test file naming (`test_{file-name}.py`), placement under `tests/unit/` mirroring source path (e.g. `target_gcs/paths/simple.py` → `tests/unit/paths/test_simple.py`), and use of global `conftest.py` and `files/` for fixtures and test data.
- Existing `@{context_docs_dir}/AI_CONTEXT_REPOSITORY.md` — overall architecture context

Prefer reading **specific files that demonstrate patterns** instead of every file.

## Required Sections

Include at least:

1. **Metadata** — Version, Last Updated (ISO date), Tags (e.g. `patterns`, `conventions`), Cross-References to repository and component-specific AI context docs
2. **Code Organization** — How modules and components are grouped; naming conventions for files and directories
3. **Type & Model Patterns** — How data is modelled (e.g. Pydantic, TypeScript types, dataclasses); conversion patterns if applicable
4. **Error Handling & Logging** — How errors are reported and surfaced; logging approach
5. **Testing & TDD** — Where tests live; typical test naming/structure; how to approach test-first development in this repo
6. **Dependency Injection & Validation** — How non-deterministic dependencies are passed in; how validation is done (per dev rules)
7. **Q&A Behavior Examples** — Short Q&A style entries for typical workflows (e.g. "How do I add X?"; "How should I handle Y?") with concrete file/function references

## Style & Constraints

- Use **Q&A style** for behavior explanations where possible
- Provide **short, real code snippets** and reference actual paths
- Keep each example focused
- Keep the file under the content length limit; split by topic with an index if needed (per `content_length` rules)

## Update Strategy

When implementation patterns evolve: sync documented patterns with the code; remove or mark deprecated patterns; add new Q&A entries for new workflows; refresh metadata and cross-references.
