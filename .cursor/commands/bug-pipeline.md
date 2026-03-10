# Bug Pipeline

Orchestrated multi-phase bug fix implementation. Invokes specialized subagents in sequence with scratchpad handoff. Use when fixing a bug from `{bugs_dir}` (default: `_bugs`). For new features, use `feature-pipeline` instead. Default path conventions are documented in `cursor/CONVENTIONS.md`.

## Commit Procedure

Same as feature-pipeline: run tests, stage, safety check, Conventional Commits, then commit. **Only implementation tasks (Phase 6) and the archive (Phase 7) are committed.** Investigation, research, plan, task list, and per-task plan artifacts (Phases 1–5) are not committed—they are deleted at clean-up and committing them would bloat git history. **Changelog**: Entries reference the bug fix and the archive summary file (`{archive_dir}/fix-{bug_name}/fix-{bug_name}.md`); each task is a brief bullet (with optional sub-bullets for major parts). Keep the changelog brief; full detail lives in the archived file. Do not link to task/plan files (they are removed during clean-up).

## Prerequisites

- User provides the bug name or identifier (used for `{bug_name}` in paths)
- Initial error description, symptoms, or reproduction report

## Instructions

Execute these phases in order. **Wait for user approval between Phase 3 and Phase 4** before proceeding to implementation tasks.

### Resume Detection (Before Phase 1)

1. Read `{scratchpad}`
2. If it contains a "Bug: {bug_name}" section with "Pipeline State" and "Task Completion Status":
   - **Phase 1-5**: Skip each phase marked "Complete" in Pipeline State
   - **Phase 6**: Compute remaining tasks = tasks in Execution Order that are NOT listed in Task Completion Status. Proceed to Phase 6 Implementation with only remaining tasks.
3. If no matching bug state or scratchpad is empty, start from Phase 1.

### Phase 1: Investigate

**Skip if Pipeline State shows Phase 1 Complete when resuming.**

Invoke the `/debug-specialist` subagent. Pass it the bug name and ask it to:

1. Review the bug report or error description provided by the user
2. Execute the workflow in `@.cursor/workflows/1-investigate-bug.md`
3. Create investigation docs in `{bugs_dir}/{bug_name}/investigation/`
4. Write a summary to `{scratchpad}` (bug name, investigation directory, root cause hypothesis, affected components)

**No commit** — planning artifacts are not committed (see Commit Procedure).

### Phase 2: Research

**Skip if Pipeline State shows Phase 2 Complete when resuming.**

Invoke the `/researcher` subagent. Ask it to:

1. Read `{scratchpad}` and investigation docs from `{bugs_dir}/{bug_name}/investigation/`
2. Execute the workflow in `@.cursor/workflows/2-research-bug.md`
3. Create research docs in `{bugs_dir}/{bug_name}/research/`
4. Update `{scratchpad}` with key findings and applicable solutions

**No commit** — planning artifacts are not committed (see Commit Procedure).

### Phase 3: Plan

**Skip if Pipeline State shows Phase 3 Complete when resuming.**

Invoke the `/architect` subagent. Ask it to:

1. Read `{scratchpad}` and research docs from `{bugs_dir}/{bug_name}/research/`
2. Execute the workflow in `@.cursor/workflows/3-plan-bug-fix.md`
3. Create fix plan in `{bugs_dir}/{bug_name}/plans/master/`
4. Update `{scratchpad}` with plan location and fix approach
5. Present the plan summary to the user

**STOP here. Wait for explicit user approval before Phase 4.**

**No commit** — planning artifacts are not committed (see Commit Procedure).

### Phase 4: Task List Generation

**Skip if Pipeline State shows Phase 4 Complete when resuming.**

Invoke the `/task-decomposer` subagent. Ask it to:

1. Read `{scratchpad}` and the plan from `{bugs_dir}/{bug_name}/plans/master/`
2. Execute the workflow in `@.cursor/workflows/4-bug-fix-tasks.md`
3. Create task documents in `{bugs_dir}/{bug_name}/tasks/`
4. Update `{scratchpad}` with task count, ordered list of task file names, and execution order

**No commit** — planning artifacts are not committed (see Commit Procedure).

### Phase 5: Per-Task Planning

**Skip if Pipeline State shows Phase 5 Complete when resuming.**

For **each** task in execution order (from the scratchpad's task list):

Invoke the `/architect` subagent with a **fresh agent context**. Pass the bug name and single task file name (without `.md` extension). Ask it to:

1. Execute the workflow in `@.cursor/workflows/5-plan-task-bug.md`
2. Create plan at `{bugs_dir}/{bug_name}/plans/tasks/{task_file}.md`
3. Update `{scratchpad}` with plan location

**No commit** — planning artifacts are not committed (see Commit Procedure).

### Phase 6: Per-Task Implementation

When resuming: iterate over **remaining tasks** only (from Resume Detection). Otherwise: full execution order.

For **each** task in the applicable list:

1. If plan does NOT exist at `{bugs_dir}/{bug_name}/plans/tasks/{task_file}.md`: invoke `/architect` first (per `5-plan-task-bug.md`), then proceed.
2. Invoke the `/implementer` subagent with a **fresh agent context**. Pass the bug name and single task file name (without `.md` extension). Ask it to:
   - Read `{scratchpad}` for context
   - Execute the workflow in `@.cursor/workflows/implement-task-fix.md`
   - Implement **only** that task; do not proceed to the next task until all tests pass (tests marked as expected failures are excluded; all other failures are regressions that must be resolved)
   - Run the **Commit Procedure** (defined in `implement-task-fix.md` Step 3.6: Commit Changes) to commit all changes for the completed task
   - Update `{scratchpad}` with task completion status

**Invoke architect and implementer once per task. Each invocation uses a fresh agent context.**

### Phase 7: Clean UP

1. **Tests**: Ensure **all** project tests pass: run the project's full test suite as defined in project rules (e.g. `.cursor/rules/environment.mdc` or README). Only tests marked as expected failures may fail; any other failure is a regression — present a report and halt.
2. **Summarise and archive**: Invoke the `/archivist` subagent. Pass bug name and paths (`{bugs_dir}`, `{archive_dir}`). Ask it to:
   - Execute the workflow in `@.cursor/workflows/6-archive-bug-summary.md`
   - Read the bug request and all documents under `{bugs_dir}/{bug_name}/`
   - Write the summary to `{archive_dir}/fix-{bug_name}/fix-{bug_name}.md`
3. **Delete bug artifacts**: Delete the bug request and the bug folder:
   - Delete `{bugs_dir}/{bug_name}.md`
   - Delete the entire tree `{bugs_dir}/{bug_name}/`
4. **Commit**: Run the **Commit Procedure** (as defined above). Use type `docs`, scope `bug`, description: `archive summary for fix-{bug_name}`.
5. **Scratchpad**: Clear completed items from the scratchpad file.

## Notes

- Each subagent runs in an isolated context window; the scratchpad ensures handoff continuity
- Original commands (1-investigate-bug, 2-research-bug, etc.) remain available for standalone use
- Subagents are invoked via `/name` syntax (e.g., `/debug-specialist`, `/researcher`, `/architect`, `/archivist`)
- **Resume**: A fresh invocation reads the scratchpad and skips completed phases; Phase 6 iterates only over remaining tasks
