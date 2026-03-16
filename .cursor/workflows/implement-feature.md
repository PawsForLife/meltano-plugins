# Implement Feature

Implement a feature in one or more services/libraries following a structured workflow with mandatory planning, TDD, and documentation updates. For bug fixes, use the `implement-fix` command instead.

## Prerequisites

- Feature file must exist in `{features_dir}` directory (see `@cursor/CONVENTIONS.md`) following the template format
- Feature file should contain: Background, This Task, and Testing Needed sections

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
- [ ] Step 1.1: Read relevant changelog(s) (root and affected plugin per CONVENTIONS § Changelogs)
- [ ] Step 1.2: Read feature file and extracted Background, This Task, and Testing Needed sections
- [ ] Step 1.3:

**Phase 2: Planning**
- [ ] Step 2.1: Created implementation plan using `create_plan` tool (saved to `{features_dir}/{feature}/plans/tasks/`)
- [ ] Step 2.2: Presented plan to user and received explicit approval before proceeding

**Phase 3: Implementation**
- [ ] Step 3.1: Wrote tests first (TDD approach) following service-specific patterns
- [ ] Step 3.1: Verified tests FAIL before implementation
- [ ] Step 3.2: Implemented code changes following the approved plan
- [ ] Step 3.3: Ran project code quality tools and fixed issues
- [ ] Step 3.4: Ran tests again and verified they PASS
- [ ] Step 3.5: Completed service-specific validation (if applicable)

**Phase 4: Completion**
- [ ] Step 4.1: Updated the correct changelog(s) per scope (root date-based, plugin per CONVENTIONS); one heading per change type per section; feature and archive summary (no task/plan links)
- [ ] Step 4.2: Updated relevant documentation in `{context_docs_dir}/` directory
- [ ] Step 4.2: Updated service READMEs (if applicable)
- [ ] Step 4.3: Archived task and plan files to `{archive_dir}/{feature}/` (maintaining folder hierarchy)
- [ ] Step 4.4: Ran full test suite for affected service(s) and all tests passed
- [ ] Step 4.4: Verified no code quality errors remain
- [ ] Step 4.4: Confirmed all files are ready for commit

---

## Phase 1: Context Gathering

### Step 1.1: Read Codebase Context

1. Read relevant context files from `{context_docs_dir}/` directory based on feature scope:
   - **Always read**: `AI_CONTEXT_QUICK_REFERENCE.md` for URLs, commands, and configurations
   - **Always read**: `AI_CONTEXT_REPOSITORY.md` for system architecture and component relationships
   - **If affecting specific components**: Read the corresponding component context files in `{context_docs_dir}/`
   - **Always read**: `AI_CONTEXT_PATTERNS.md` for code patterns and conventions
   - **If the feature affects Singer/Meltano components (taps, targets)**: Use terminology from `GLOSSARY_MELTANO_SINGER.md` (tap, target, stream, catalog, config file, state file, SCHEMA/RECORD/STATE)

2. Read the relevant changelog(s) (see CONVENTIONS § Changelogs): root `CHANGELOG.md` and, if the feature affects a single plugin, that plugin's `taps/{name}/CHANGELOG.md` or `loaders/{name}/CHANGELOG.md`. Create root changelog if it doesn't exist. Understand recent changes, format, and the rule: root uses date headings (`## YYYY-MM-DD`); one heading per change type per date/version (append under existing headings).

### Step 1.2: Read Feature File

1. The user will provide the path to a feature file in `{features_dir}/` (e.g., `{features_dir}/my-feature.md`)
2. Read the feature file and extract:
   - **Background**: Context for what and why the change is needed
   - **This Task**: Specific list of changes to implement
   - **Testing Needed**: Tests that must be created or updated

### Step 1.3: Analyze Scope

Determine which service(s) or component(s) will be affected:

**Identify affected component(s) based on:**
- Feature file description and task list
- Which component's functionality is being modified (discover from project layout or README)
- Cross-component dependencies as documented in project context

---

## Phase 2: Planning (MANDATORY)

**You MUST create a plan before any implementation. Do not skip this phase.**

### Step 2.1: Create Implementation Plan

Use the `CreatePlan` tool to generate a detailed implementation plan that includes:

1. **Overview**: What the feature accomplishes
2. **Files to Create/Modify**: List all files with specific changes
3. **Test Strategy**: Which tests to write first (TDD approach)
4. **Implementation Order**: Step-by-step implementation sequence
5. **Validation Steps**: How to verify the implementation works
6. **Documentation Updates**: What docs need updating

Save the plan to `{features_dir}/{feature}/plans/tasks/` with the plan file name matching the task file name (e.g., `01-stubbing.md` for task `01-stubbing.md`).

Example: `cat > {features_dir}/add-logging/plans/tasks/01-stubbing.md << 'PLAN_EOF'`

### Step 2.2: Wait for User Approval

After the plan is created:

1. Present the plan summary to the user
2. **STOP and wait for user approval** before proceeding to implementation
3. The user may request changes to the plan
4. Only proceed when user explicitly confirms

---

## Phase 3: Implementation (After Approval Only)

Follow the TDD workflow defined in project rules:

### Step 3.1: Write Tests First

1. Create or update tests based on the affected service type:

   Create or update tests per the project's test layout and patterns (see `{context_docs_dir}/` and project rules). Follow black box testing principles.

2. Run the tests and **verify they FAIL**: run the project's test suite for the affected component(s) as defined in project rules. If tests pass before implementation, the tests don't validate the changes; adjust tests until they correctly validate the expected behavior and fail.

### Step 3.2: Implement Code Changes

1. Implement the code changes following the plan
2. Follow component-specific patterns:
   Reference `{context_docs_dir}/` for the affected component(s) and AI_CONTEXT_PATTERNS.md for code organization, logging, and conventions. Maintain consistency with existing code in the component.

### Step 3.3: Run Code Quality Tools

After code changes, run the project's code quality tools as defined in project rules (e.g. `.cursor/rules/environment.mdc` or README) and fix any issues.

### Step 3.4: Run Tests

1. Run the project's test suite for the affected component(s) and **verify they PASS** (per project rules). If tests fail:
   - Validate implementation logic against the plan
   - Validate test logic against expected behavior
   - Fix issues and re-run until passing

### Step 3.5: Component-Specific Validation (If Needed)

Run the validation steps appropriate to the affected component(s) as documented in project context (`{context_docs_dir}/`) or README.

---

## Phase 4: Completion

### Step 4.1: Update Changelog(s)

**Which changelog to edit**: Per `@.cursor/CONVENTIONS.md` § Changelogs — **root** `CHANGELOG.md` for repo-wide changes; **plugin** `taps/{name}/CHANGELOG.md` or `loaders/{name}/CHANGELOG.md` for that plugin only. Update only the changelog(s) for the feature's scope.

**Root changelog**: Use date-based heading `## YYYY-MM-DD` (commit date). If that date section exists, append; otherwise add it at the top. **Plugin changelog**: Under each version (e.g. `## [Unreleased]`), one heading per change type; append bullets. Do not add a second heading of the same type in the same section.

If root `CHANGELOG.md` doesn't exist, create it with a date section for the commit:
```markdown
# Changelog

All notable changes to this project will be documented in this file.

## YYYY-MM-DD

```

Add entries under the appropriate subsection (`### Added`, `### Changed`, `### Fixed`, or `### Removed`). Reference the feature and the archive summary file only (no links to task/plan files). Each task is a brief bullet; optional sub-bullets for major parts. Full detail lives in the archive.

**Format** (feature pipeline):

```markdown
### Added/Changed/Fixed
- **{feature name}** — Details: [{feature_name}.md]({archive_dir}/{feature_name}/{feature_name}.md)
  - Task name or one-line description
  - (Next task adds another bullet)
```

**Note:** The root changelog uses date-based sections only (`## YYYY-MM-DD`). The repo is released by pushing; no version numbers. Each commit adds or appends under the commit date.

### Step 4.2: Update Documentation

Review and update documentation based on what changed:

1. **Review relevant files in `{context_docs_dir}/` directory**: update the repository, patterns, quick reference, and any component-specific context files that correspond to the affected component(s). Keep these files current for future AI agent context.

2. **Update component READMEs** if applicable (e.g. in component directories as defined by project layout).

### Step 4.3: Archive Task and Plan Files

On completion of a task, move both task and plan files to the archive maintaining folder hierarchy under `{archive_dir}/{feature}/`:

```bash
# On completion of a task, move both task and plan files to archive
# maintaining folder hierarchy under {archive_dir}/{feature}/

FEATURE="<feature-name>"   # e.g., add-logging
TASK_FILE="01-stubbing.md" # the completed task file name

mkdir -p {archive_dir}/${FEATURE}/tasks
mkdir -p {archive_dir}/${FEATURE}/plans/tasks

mv {features_dir}/${FEATURE}/tasks/${TASK_FILE} {archive_dir}/${FEATURE}/tasks/
mv {features_dir}/${FEATURE}/plans/tasks/${TASK_FILE} {archive_dir}/${FEATURE}/plans/tasks/
```

### Step 4.4: Final Validation

1. Run the full test suite for affected component(s) as defined in project rules. All tests must pass (excluding expected failures).

2. Run the project's code quality tools (linters, type checkers) and fix any issues.

3. Confirm all files are ready for commit

4. Review the **Completion Checklist** at the start of this document to ensure all items are checked before considering the job complete.

---

## Examples

### Example 1: Adding a feature to a backend component

**Feature File (`{features_dir}/add-parser-feature.md`):**
```markdown
# Background
Need to add support for new parsing behavior in the relevant component.

# This Task
- Add new logic in the component's main modules
- Update schemas or types as needed
- Add error handling

# Testing Needed
- Unit tests for new logic
- Integration tests
- Error handling tests
```

**Changelog Entry:** Root: add under `## YYYY-MM-DD` (commit date). Plugin: add under `## [Unreleased]`. Reference the feature and archive summary `{archive_dir}/{feature}/{feature}.md` only (no task/plan file links).

### Example 2: Adding a UI or frontend component

**Feature File (`{features_dir}/add-custom-component.md`):**
```markdown
# Background
Users need a new UI component or frontend behavior.

# This Task
- Create component in the appropriate source directory
- Add registration or wiring as per project layout
- Integrate with existing APIs

# Testing Needed
- Component unit tests
- Integration tests
- Any visual or E2E tests per project conventions
```

**Changelog Entry:** Root: add under `## YYYY-MM-DD` (commit date). Plugin: add under `## [Unreleased]`. Reference the feature and archive summary `{archive_dir}/{feature}/{feature}.md` only (no task/plan file links).

---

## Important Notes

- **Planning is mandatory**: Never skip Phase 2, even for "simple" changes
- **TDD is required**: Always write failing tests before implementation
- **Component boundaries matter**: Identify which component(s) are affected and follow component-specific patterns
- **Keep AI_CONTEXT files current**: Update relevant files in `{context_docs_dir}/` directory for future changes
- **Archive, don't delete**: Task and plan files go to `{archive_dir}/{feature}/` maintaining folder hierarchy (`tasks/`, `plans/tasks/`), not trash
- **Links in changelog**: Reference the feature and archive summary file only; do not link to task/plan files (removed during clean-up)
- **One feature per file**: Each feature file should describe a single coherent change
- **Date-based root changelog**: Root `CHANGELOG.md` uses date headings only (`## YYYY-MM-DD`); no version numbers; released by pushing
- **Component-specific testing**: Follow testing patterns appropriate to the affected component(s) as documented in project context

## Feature File Template Reference

Feature files in `{features_dir}/` should follow this template:

```markdown
# Background
User to add details of what and why the change is being done

# This Task
- a list of changes that need to be made

# Testing Needed
- a list of tests that should at least be made and or updated
```

See `{features_dir}/_template.md` for the template file.
