# Archive Feature Summary

Produce a single summary document from feature pipeline artifacts for the archive. Invoked by the feature pipeline in Phase 6 via the `/archivist` sub-agent. Path placeholders are defined in `@.cursor/CONVENTIONS.md`.

## Prerequisites

- Feature name and paths (`{features_dir}`, `{archive_dir}`) provided by the pipeline
- Feature request and folder exist at `{features_dir}/{feature_name}.md` and `{features_dir}/{feature_name}/`

## Process

### Step 1: Gather

Read all documents that would have been archived:

1. **Feature request**: `{features_dir}/{feature_name}.md`
2. **Planning**: All files in `{features_dir}/{feature_name}/planning/` (e.g. impacted-systems.md, new-systems.md, possible-solutions.md, selected-solution.md)
3. **Master plan**: All files in `{features_dir}/{feature_name}/plans/master/` (e.g. overview.md, architecture.md, implementation.md)
4. **Task list**: Any task-list file in `{features_dir}/{feature_name}/` (e.g. `{feature_name}-task-list.md`)
5. **Task plans**: All files in `{features_dir}/{feature_name}/plans/tasks/`
6. **Tasks**: All files in `{features_dir}/{feature_name}/tasks/`

### Step 2: Summarise

Produce one markdown document with exactly three sections. Keep each section concise; cite key decisions and outcomes rather than copying large blocks.

- **The request**: Summary of the feature request (background, goal, testing needs). Draw from the feature file and planning context.
- **Planned approach**: Summary of the chosen solution, architecture, and task breakdown. Draw from planning docs, master plan, task list, and task plans.
- **What was implemented**: Summary of completed tasks and outcomes. Draw from task documents and any implementation context (e.g. CHANGELOG or scratchpad if available).

Obey `@.cursor/rules/content_length.mdc` for the overall document length.

### Step 3: Write

1. Ensure the directory exists: `{archive_dir}/{feature_name}/`
2. Write the summary document to `{archive_dir}/{feature_name}/{feature_name}.md`

Do not delete or move any other files; the pipeline deletes feature artifacts after the archivist returns.

## Notes

- This workflow does not perform any deletion. The feature pipeline orchestrator deletes `{features_dir}/{feature_name}.md` and the tree `{features_dir}/{feature_name}/` after the archivist completes.
- The archive will contain only this single summary file for the feature.
