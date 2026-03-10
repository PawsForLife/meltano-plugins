# Archive Bug Fix Summary

Produce a single summary document from bug pipeline artifacts for the archive. Invoked by the bug pipeline in Phase 7 via the `/archivist` sub-agent. Path placeholders are defined in `@.cursor/CONVENTIONS.md`.

## Prerequisites

- Bug name and paths (`{bugs_dir}`, `{archive_dir}`) provided by the pipeline
- Bug request and folder exist at `{bugs_dir}/{bug_name}.md` and `{bugs_dir}/{bug_name}/`

## Process

### Step 1: Gather

Read all documents that would have been archived:

1. **Bug request**: `{bugs_dir}/{bug_name}.md`
2. **Investigation**: All files in `{bugs_dir}/{bug_name}/investigation/` (e.g. observed-behavior.md, reproduction-steps.md, affected-components.md, root-cause-hypothesis.md)
3. **Research**: All files in `{bugs_dir}/{bug_name}/research/` (e.g. internal-documentation.md, applicable-solutions.md)
4. **Master plan**: All files in `{bugs_dir}/{bug_name}/plans/master/` (e.g. overview.md, fix-approach.md, implementation.md, validation.md)
5. **Task list**: Any task-list file in `{bugs_dir}/{bug_name}/` (if present)
6. **Task plans**: All files in `{bugs_dir}/{bug_name}/plans/tasks/`
7. **Tasks**: All files in `{bugs_dir}/{bug_name}/tasks/`

### Step 2: Summarise

Produce one markdown document with exactly three sections. Keep each section concise; cite key decisions and outcomes rather than copying large blocks.

- **The request**: Summary of the bug report (symptoms, reproduction, expected vs actual behaviour). Draw from the bug request and investigation context.
- **Planned approach**: Summary of the chosen fix, architecture, and task breakdown. Draw from research docs, master plan, task list, and task plans.
- **What was implemented**: Summary of completed tasks and outcomes. Draw from task documents and any implementation context (e.g. CHANGELOG or scratchpad if available).

Obey `@.cursor/rules/content_length.mdc` for the overall document length.

### Step 3: Write

1. Ensure the directory exists: `{archive_dir}/fix-{bug_name}/`
2. Write the summary document to `{archive_dir}/fix-{bug_name}/fix-{bug_name}.md`

Do not delete or move any other files; the pipeline deletes bug artifacts after the archivist returns.

## Notes

- This workflow does not perform any deletion. The bug pipeline orchestrator deletes `{bugs_dir}/{bug_name}.md` and the tree `{bugs_dir}/{bug_name}/` after the archivist completes.
- The archive will contain only this single summary file for the fix.
