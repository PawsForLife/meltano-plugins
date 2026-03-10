# Implement Bug Fix

Implement a bug fix following the structured workflow from investigation through tasks. Reads from `{bugs_dir}/{bug_name}/` (path placeholders in `@cursor/CONVENTIONS.md`), uses mandatory planning, TDD, and documentation updates. For detailed Phase 3/4 steps (test commands, code quality, changelog format), reference `@.cursor/workflows/implement-feature.md`.

## Prerequisites

- Bug artifacts must exist in `{bugs_dir}/{bug_name}/` directory:
  - `investigation/` - Investigation documents
  - `research/` - Research documents
  - `plans/master/` - Fix plan
  - `tasks/` - Task documents from 4-bug-fix-tasks

## Regression Rules (MANDATORY)

- **Regression is not acceptable.** Failing tests that are not explicitly marked as expected failures (e.g., `@pytest.mark.xfail`, `@unittest.expectedFailure`) are regressions and must be fixed before the task is considered complete.
- **Expected failures are acceptable.** Tests annotated with framework-level expected-failure markers are excluded from the regression gate. Do not remove or alter these markers without explicit user approval.
- **Do not claim tests are unrelated.** If a test fails after your changes, it is your responsibility to fix it. You may not dismiss failing tests as "unrelated" or "pre-existing" without explicit user confirmation.
- **Full test suite requirement:** Before marking work complete, run the full test suite for affected component(s). All tests must pass (excluding expected failures).

## Instructions

You MUST follow these phases in order. **Planning is mandatory** - do not skip to implementation.

## Completion Checklist

**Check off each item as you complete it. Review this checklist throughout execution to ensure all tasks are completed.**

**Phase 1: Context Gathering**
- [ ] Step 1.1: Read relevant codebase context files from `{context_docs_dir}/` directory
- [ ] Step 1.2: Read root `CHANGELOG.md` (or create if it doesn't exist)
- [ ] Step 1.3: Read investigation, research, plan, and task documents from `{bugs_dir}/{bug_name}/`
- [ ] Step 1.4: Identified affected component(s)

**Phase 2: Planning**
- [ ] Step 2.1: Created implementation plan per task (saved to `{bugs_dir}/{bug_name}/plans/tasks/`)
- [ ] Step 2.2: Presented plan to user and received explicit approval before proceeding

**Phase 3: Implementation**
- [ ] Step 3.1: Wrote tests first (TDD approach), regression tests when feasible
- [ ] Step 3.2: Verified tests FAIL before implementation
- [ ] Step 3.3: Implemented code changes following the approved plan
- [ ] Step 3.4: Ran code quality tools (ruff/mypy for Python, lint/check for UI) and fixed issues
- [ ] Step 3.5: Ran tests again and verified they PASS
- [ ] Step 3.6: Completed validation steps from plan (reproduction, regression)

**Phase 4: Completion**
- [ ] Step 4.1: Updated root `CHANGELOG.md` under `## [Unreleased]` in `### Fixed` subsection
- [ ] Step 4.2: Updated relevant documentation in `{context_docs_dir}/` directory
- [ ] Step 4.3: Archived bug artifacts to `_archive/fix-{bug_name}/` (maintaining folder hierarchy)
- [ ] Step 4.4: Ran full test suite for affected service(s) and all tests passed
- [ ] Step 4.5: Verified no code quality errors remain
- [ ] Step 4.6: Confirmed all files are ready for commit

---

## Phase 1: Context Gathering

### Step 1.1: Read Codebase Context

1. Read relevant context files from `{context_docs_dir}/` directory based on bug scope:
   - **Always read**: AI_CONTEXT_QUICK_REFERENCE.md and AI_CONTEXT_REPOSITORY.md
   - **If affecting specific components**: Read the corresponding component context files in `{context_docs_dir}/`
   - **Always read**: AI_CONTEXT_PATTERNS.md for code patterns and conventions
   - **If the fix affects Singer/Meltano components (taps, targets)**: Use terminology from `GLOSSARY_MELTANO_SINGER.md` (tap, target, stream, catalog, config file, state file, SCHEMA/RECORD/STATE)

2. Read root `CHANGELOG.md` (create if it doesn't exist) to understand recent changes and changelog format.

### Step 1.2: Read Bug Artifacts

1. The user will provide the bug name (e.g., `python-service-hang`).
2. Read from `{bugs_dir}/{bug_name}/`:
   - **investigation/**: `observed-behavior.md`, `reproduction-steps.md`, `affected-components.md`, `root-cause-hypothesis.md`
   - **research/**: `applicable-solutions.md`
   - **plans/master/**: `overview.md`, `fix-approach.md`, `implementation.md`, `testing.md`, `validation.md`
   - **tasks/**: All task files in execution order (01-, 02-, etc.)

### Step 1.3: Analyze Scope

Determine which component(s) are affected based on `affected-components.md` and the fix plan (use project context for component names).

---

## Phase 2: Planning (MANDATORY)

**You MUST create a plan before any implementation. Do not skip this phase.**

### Step 2.1: Create Implementation Plan

For each task in `{bugs_dir}/{bug_name}/tasks/`, create an implementation plan that includes:

1. **Overview**: What the fix accomplishes for this task
2. **Files to Create/Modify**: List all files with specific changes
3. **Test Strategy**: Regression tests first when feasible (TDD)
4. **Implementation Order**: Step-by-step sequence
5. **Validation Steps**: How to verify the fix and prevent regression

Save plans to `{bugs_dir}/{bug_name}/plans/tasks/` with file names matching task files (e.g., `01-add-regression-test.md`).

### Step 2.2: Wait for User Approval

1. Present the plan summary to the user
2. **STOP and wait for user approval** before proceeding
3. Only proceed when user explicitly confirms

---

## Phase 3: Implementation (After Approval Only)

Follow the TDD workflow. Reference `@.cursor/workflows/implement-feature.md` for detailed commands:

Run the project's test suite and code quality tools as defined in project rules (e.g. `.cursor/rules/environment.mdc` or README).

Emphasize:
- Regression tests that reproduce the bug before fix
- Validation steps from `{bugs_dir}/{bug_name}/plans/master/validation.md`
- Black box testing - validate functionality, not internal behavior

---

## Phase 4: Completion

### Step 4.1: Update Changelog

Add entry under `### Fixed` in `## [Unreleased]`:

```markdown
### Fixed
- Brief description of the bug fix
  - Plan: [task-name](_archive/fix-{bug_name}/plans/tasks/{task-name}.md)
  - Task: [task-name](_archive/fix-{bug_name}/tasks/{task-name}.md)
```

### Step 4.2: Update Documentation

Update relevant files in `{context_docs_dir}/` and component READMEs based on what changed.

### Step 4.3: Archive Bug Artifacts

On completion, move bug artifacts to `_archive/fix-{bug_name}/` maintaining folder hierarchy:

```
_archive/fix-{bug_name}/
├── investigation/
├── research/
├── plans/
│   ├── master/
│   └── tasks/
└── tasks/
```

### Step 4.4: Final Validation

1. Run full test suite for affected component(s)
2. Verify no code quality errors
3. Confirm all files are ready for commit
4. Review the Completion Checklist

---

## Important Notes

- **Read from {bugs_dir}/**: This command consumes `{bugs_dir}/{bug_name}/`, not `{features_dir}/`
- **Changelog**: Entries go under `### Fixed`, not `### Added` or `### Changed`
- **Archive path**: `_archive/fix-{bug_name}/` (prefix with `fix-` for consistency)
- **Regression tests**: Prioritize tests that reproduce the bug before applying the fix
- **Validation**: Follow steps in `validation.md` to confirm fix and prevent regression
