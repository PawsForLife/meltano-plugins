# Implement Single Bug Fix Task

Implement one task from the bug fix pipeline. Invoked once per task with a fresh agent context. The plan is pre-created by the architect in the per-task planning phase. For features, use `implement-task-feature.md` instead. For full bug fix implementation, use `implement-fix.md`.

## Regression Rules (MANDATORY)

- **Regression is not acceptable.** Failing tests that are not explicitly marked as expected failures (e.g., `@pytest.mark.xfail`, `@unittest.expectedFailure`) are regressions and must be fixed before the task is considered complete.
- **Expected failures are acceptable.** Tests annotated with framework-level expected-failure markers are excluded from the regression gate. Do not remove or alter these markers without explicit user approval.
- **Do not claim tests are unrelated.** If a test fails after your changes, it is your responsibility to fix it. You may not dismiss failing tests as "unrelated" or "pre-existing" without explicit user confirmation.
- **Full test suite requirement:** Before marking a task complete, run the full test suite for affected component(s). All tests must pass (excluding expected failures).

## Prerequisites

- Task document exists at `{bugs_dir}/{bug_name}/tasks/{task_file}.md` (where `{task_file}` is the basename without `.md`)
- Task plan exists in `{bugs_dir}/{bug_name}/plans/tasks/{task_file}.md` (created by architect)
- User provides: bug name, task file name without extension (e.g. `01-add-regression-test`)

## Instructions

Execute these phases in order. Focus only on this single task.

## Completion Checklist

**Check off each item as you complete it.**

**Phase 1: Context Gathering**
- [ ] Step 1.1: Read relevant codebase context from `{context_docs_dir}/`
- [ ] Step 1.2: Read root `CHANGELOG.md` (or create if it doesn't exist)
- [ ] Step 1.3: Read task document and task plan
- [ ] Step 1.4: Read `{scratchpad}` for context
- [ ] Step 1.5: Identified affected component(s)

**Phase 2: Implementation**
- [ ] Step 2.1: Wrote tests first (TDD), regression tests when feasible
- [ ] Step 2.2: Verified tests FAIL before implementation
- [ ] Step 2.3: Implemented code changes following the approved plan
- [ ] Step 2.4: Ran project code quality tools and fixed issues
- [ ] Step 2.5: Ran full test suite and verified all tests PASS (no regressions)
- [ ] Step 2.6: Completed validation steps from plan (reproduction, regression)

**Phase 3: Completion**
- [ ] Step 3.1: Updated root `CHANGELOG.md` under `## [Unreleased]` in `### Fixed`
- [ ] Step 3.2: Updated relevant documentation in `{context_docs_dir}/` and READMEs (if applicable)
- [ ] Step 3.3: Archived task and plan files to `{archive_dir}/fix-{bug_name}/`
- [ ] Step 3.4: Ran full test suite again; all tests passed
- [ ] Step 3.5: Verified no code quality errors remain
- [ ] Step 3.6: Updated `{scratchpad}` with "Task {task_file} completed, tests passing"
- [ ] Step 3.7: Committed all changes (Commit Procedure per bug-pipeline)

---

## Phase 1: Context Gathering

### Step 1.1: Read Codebase Context

Read relevant files from `{context_docs_dir}/` based on task scope:
- **Always read**: AI_CONTEXT_QUICK_REFERENCE.md, AI_CONTEXT_REPOSITORY.md
- **If affecting specific components**: Read the corresponding component context files in `{context_docs_dir}/`
- **Always read**: AI_CONTEXT_PATTERNS.md
- **If the task affects Singer/Meltano components (taps, targets)**: Use terminology from `GLOSSARY_MELTANO_SINGER.md` (tap, target, stream, catalog, config file, state file, SCHEMA/RECORD/STATE)

### Step 1.2: Read Changelog

Read root `CHANGELOG.md` (create if it doesn't exist). Understand recent changes and changelog format.

### Step 1.3: Read Task and Plan

1. Read the task from `{bugs_dir}/{bug_name}/tasks/{task_file}.md`
2. Read the plan from `{bugs_dir}/{bug_name}/plans/tasks/{task_file}.md`
3. If the plan seems incomplete, request the architect to update it before proceeding

### Step 1.4: Read Scratchpad

Read `{scratchpad}` for bug name, pipeline state, and prior task completions.

### Step 1.5: Analyze Scope

Determine which service(s) or component(s) are affected based on the task and plan.

---

## Phase 2: Implementation

Follow the TDD workflow. Run the project's test suite and code quality tools as defined in project rules; reference `@.cursor/workflows/implement-feature.md` for the full workflow.

Emphasize:
- Regression tests that reproduce the bug before fix
- Validation steps from `{bugs_dir}/{bug_name}/plans/master/validation.md`
- Black box testing - validate functionality, not internal behavior

### Step 2.1: Write Tests First

Create or update tests per the task plan's Test Strategy. Prioritize regression tests when feasible.

### Step 2.2: Verify Tests Fail

Run tests and verify they FAIL before implementation. If they pass, adjust tests until they correctly validate expected behavior and fail.

### Step 2.3: Implement Code Changes

Implement following the plan's Implementation Order. Follow component-specific patterns from AI_CONTEXT_PATTERNS.md.

### Step 2.4: Run Code Quality Tools

Run the project's code quality tools and fix any issues.

### Step 2.5: Run Full Test Suite

Run the **full** test suite for affected component(s). **All tests must pass (excluding expected failures).** Any failing test not explicitly marked as an expected failure is a regression and must be fixed before proceeding. Do not claim failures are "unrelated" to your changes.

### Step 2.6: Validation

Complete validation steps from `{bugs_dir}/{bug_name}/plans/master/validation.md` to confirm fix and prevent regression.

---

## Phase 3: Completion

### Step 3.1: Update Changelog

Changelog entries reference the **bug fix** and the **archive summary file** only (no links to task/plan files, which are removed during clean-up). Keep the changelog brief; full detail lives in the archive.

Under `## [Unreleased]` → `### Fixed`:

1. **If this is the first task for this bug**: Add a bug-level entry that names the fix and references the archive file (created in pipeline Phase 7). Use the path `{archive_dir}/fix-{bug_name}/fix-{bug_name}.md` even if the file does not exist yet.
2. **Append this task** as a bullet under that entry. Use the task name or a one-line description. Add sub-bullets only for major parts of the change (keep brief).

**Format**:

```markdown
### Fixed
- **fix-{bug_name}** — Details: [fix-{bug_name}.md]({archive_dir}/fix-{bug_name}/fix-{bug_name}.md)
  - Task name or one-line description (e.g. "Add regression test for auth")
    - Optional sub-point for a major part of the change
  - (Next task adds another bullet at this level)
```

When adding a subsequent task for the same bug, locate the existing bug entry and add a new top-level bullet for the new task; do not create a second entry.

### Step 3.2: Update Documentation

Update relevant files in `{context_docs_dir}/` and component READMEs based on what changed.

### Step 3.3: Archive Task and Plan

Move task and plan to archive:

```
mkdir -p {archive_dir}/fix-{bug_name}/tasks
mkdir -p {archive_dir}/fix-{bug_name}/plans/tasks
mv {bugs_dir}/{bug_name}/tasks/{task_file}.md {archive_dir}/fix-{bug_name}/tasks/
mv {bugs_dir}/{bug_name}/plans/tasks/{task_file}.md {archive_dir}/fix-{bug_name}/plans/tasks/
```

### Step 3.4: Final Validation

Run full test suite again. All tests must pass. Verify no code quality errors.

### Step 3.5: Update Scratchpad

Add to `{scratchpad}`: "Task {task_file} completed, tests passing"

### Step 3.6: Commit Changes

Commit all changes for this task following the Conventional Commits format (per `@.cursor/commands/commit.md`):

1. **Stage changed files**: `git add .`
2. **Safety check**: verify no `.env`, `*.key`, `*.pem`, or `secrets.*` files are staged. If found, unstage them (`git restore --staged <path>`) and warn.
3. **Generate a Conventional Commits message**: type inferred from changes; scope from affected paths; description goal-focused; optional body with brief bullets.
4. **Execute the commit**: `git commit -m "<message>"`

---

## Notes

- This workflow is invoked **once per task** with a fresh agent context
- Do not proceed to the next task until this task is fully complete and all tests pass
- The plan was created by the architect in the per-task planning phase; do not create a new plan
- Archive path uses `fix-` prefix: `{archive_dir}/fix-{bug_name}/`
