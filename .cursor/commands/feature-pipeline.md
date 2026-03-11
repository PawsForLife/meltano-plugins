# Feature Pipeline

Orchestrated multi-phase feature implementation. Invokes specialized subagents in sequence with scratchpad handoff. Use when implementing a feature from a feature file in `{features_dir}` (default: `_features`). For bug fixes, use `bug-pipeline` instead. Default path conventions are documented in `cursor/CONVENTIONS.md`.

## Prerequisites

- Feature file exists in `{features_dir}/{feature_name}.md` with Background, This Task, and Testing Needed sections
- User provides the feature name or path

## Commit Procedure

Reusable commit workflow executed only after **implementation tasks** (Phase 5) and **archive** (Phase 6). Planning artifacts (Phases 1–4) are not committed—they are deleted at clean-up and committing them would bloat git history.

When committing:

1. **Run the project's full test suite** as defined in project rules (e.g. `.cursor/rules/environment.mdc` or README). Only tests marked as expected failures (`@pytest.mark.xfail`, `@unittest.expectedFailure`) may fail; any other failure is a regression and **must** be resolved before committing.
2. **Stage changed files**: `git add .`
3. **Safety check**: verify no `.env`, `*.key`, `*.pem`, or `secrets.*` files are staged. If found, unstage them (`git restore --staged <path>`) and warn.
4. **Generate a Conventional Commits message** per `@.cursor/commands/commit.md`:
   - Format: `<type>(<scope>): <brief description>`
   - Optional body: goal-focused bullet points, each under 100 characters
   - Type and scope are provided per-phase below; for implementation tasks the implementer infers them from the changes
   - **Changelog**: Entries reference the feature and the archive summary file (`{archive_dir}/{feature_name}/{feature_name}.md`); each task is a brief bullet (with optional sub-bullets for major parts). Keep the changelog brief; full detail lives in the archived file. Do not link to task/plan files (they are removed during clean-up).
5. **Execute the commit**: `git commit -m "<message>"`

## Instructions

Execute these phases in order. **Wait for user approval between Phase 2 and Phase 3** before proceeding to implementation tasks.

### Resume Detection (Before Phase 1)

1. Read `{scratchpad}` and determine `{feature_name}` from the user's request (e.g. feature path or name).
2. If the scratchpad contains a "Feature: {feature_name}" section with "Pipeline State" and "Task Completion Status":
   - **Phase 1-4**: Skip each phase marked "Complete" in Pipeline State
   - **Phase 5**: Compute remaining tasks = tasks in Execution Order that are NOT listed in Task Completion Status. Proceed to Phase 5 Implementation with only remaining tasks.
3. If no matching feature state or the scratchpad is empty:
   - **Add** a "Feature: {feature_name}" section to the scratchpad with initial state. Include:
     - **Pipeline State:** Phase 1–6 all "Not started" (or equivalent; no phase Complete).
     - **Task Completion Status:** (empty) or "None completed."
     - **Execution Order:** (empty until Phase 3 completes.)
   - Then **start from Phase 1** and run the pipeline. Do not skip or ignore the pipeline.

### Phase 1: Research

**Skip if Pipeline State shows Phase 1 Complete when resuming.**

Invoke the `/researcher` subagent. Pass it the feature path and ask it to:

1. Read the feature file from `{features_dir}/{feature_name}.md`
2. Execute the workflow in `@.cursor/workflows/1-research-feature.md`
3. Produce planning docs in `{features_dir}/{feature_name}/planning/`
4. Write a summary to `{scratchpad}` (feature name, output directory, key findings, selected solution)

**No commit** — planning artifacts are not committed (see Commit Procedure).

### Phase 2: Plan

**Skip if Pipeline State shows Phase 2 Complete when resuming.**

Invoke the `/architect` subagent. Ask it to:

1. Read `{scratchpad}` and the planning docs from `{features_dir}/{feature_name}/planning/`
2. Execute the workflow in `@.cursor/workflows/2-plan-feature.md`
3. Create implementation plan in `{features_dir}/{feature_name}/plans/master/`
4. Update `{scratchpad}` with plan location and key decisions
5. Present the plan summary to the user

**STOP here. Wait for explicit user approval before Phase 3.**

**No commit** — planning artifacts are not committed (see Commit Procedure).

### Phase 3: Task List Generation

**Skip if Pipeline State shows Phase 3 Complete when resuming.**

Invoke the `/task-decomposer` subagent. Ask it to:

1. Read `{scratchpad}` and the plan from `{features_dir}/{feature_name}/plans/master/`
2. Execute the workflow in `@.cursor/workflows/3-task_list.md` and `@.cursor/workflows/4-feature-tasks.md`
3. Create task documents in `{features_dir}/{feature_name}/tasks/`
4. Update `{scratchpad}` with task count, ordered list of task file names, and execution order

**No commit** — planning artifacts are not committed (see Commit Procedure).

### Phase 4: Per-Task Planning

**Skip if Pipeline State shows Phase 4 Complete when resuming.**

For **each** task in execution order (from the scratchpad's task list):

Invoke the `/architect` subagent with a **fresh agent context**. Pass the feature name and single task file name (without `.md` extension). Ask it to:

1. Execute the workflow in `@.cursor/workflows/5-plan-task-feature.md`
2. Create plan at `{features_dir}/{feature_name}/plans/tasks/{task_file}.md`
3. Update `{scratchpad}` with plan location

**No commit** — planning artifacts are not committed (see Commit Procedure).

### Phase 5: Per-Task Implementation

When resuming: iterate over **remaining tasks** only (from Resume Detection). Otherwise: full execution order.

For **each** task in the applicable list:

1. If plan does NOT exist at `{features_dir}/{feature_name}/plans/tasks/{task_file}.md`: invoke `/architect` first (per `5-plan-task-feature.md`), then proceed.
2. Invoke the `/implementer` subagent with a **fresh agent context**. Pass the feature name and single task file name (without `.md` extension). Ask it to:
   - Read `{scratchpad}` for context
   - Execute the workflow in `@.cursor/workflows/implement-task-feature.md`
   - Implement **only** that task; do not proceed to the next task until all project tests pass (tests marked as expected failures are excluded; all other failures are regressions that must be resolved)
   - Run the **Commit Procedure** (defined in `implement-task-feature.md` Step 3.6: Commit Changes) to commit all changes for the completed task
   - Update `{scratchpad}` with task completion status

**Invoke architect and implementer once per task. Each invocation uses a fresh agent context.**

### Phase 6: Clean UP

1. **Tests**: Ensure **all** project tests pass: run the project's full test suite as defined in project rules. If any tests fail, present a report and halt.
2. **Summarise and archive**: Invoke the `/archivist` subagent. Pass feature name and paths (`{features_dir}`, `{archive_dir}`). Ask it to:
   - Execute the workflow in `@.cursor/workflows/6-archive-feature-summary.md`
   - Read all documents under `{features_dir}/{feature_name}` and the feature request at `{features_dir}/{feature_name}.md`
   - Write the summary to `{archive_dir}/{feature_name}/{feature_name}.md`
3. **Clean archive directory**: Remove any existing non-summary files and directories under `{archive_dir}/{feature_name}/` (e.g. `tasks/`, `plans/`, `planning/`, task-list files) so that only `{feature_name}.md` remains. Ensures the archive stays summary-only before every commit.
4. **Delete feature artifacts**: Delete the feature request file and the feature folder:
   - Delete `{features_dir}/{feature_name}.md`
   - Delete the entire tree `{features_dir}/{feature_name}/`
5. **Commit**: Run the **Commit Procedure**. Use type `docs`, scope `feature`, description: `archive summary for {feature_name}`.
6. **Scratchpad**: Clear completed feature from the scratchpad file.

## Notes

- Each subagent runs in an isolated context window; the scratchpad ensures handoff continuity
- Original commands (1-research-feature, 2-plan-feature, etc.) remain available for standalone use
- Subagents are invoked via `/name` syntax (e.g., `/researcher`, `/architect`, `/archivist`)
- **Resume**: When a "Feature: {feature_name}" section with Pipeline State and Task Completion Status exists, a fresh invocation skips completed phases and Phase 5 iterates only over remaining tasks. When it does not exist, the pipeline **adds** that section to the scratchpad and **starts from Phase 1**; the pipeline is never ignored.
