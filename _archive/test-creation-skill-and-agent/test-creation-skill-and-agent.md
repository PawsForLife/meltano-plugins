# Archive: Test Creation Skill and Agent

## The request

The project had test-creation guidance spread across `development_practices.mdc`, CONVENTIONS.md, and implement workflows (Step 2.1). The goal was to: (1) add one **skill** that consolidates test naming, path, TDD, black-box, and regression rules; (2) add one **subagent** for test generation, following current Cursor best practice; (3) have existing cursor systems (implement-task-feature and implement-task-fix) call that subagent with the skill and a concrete request (what to test, scope, constraints). No application code; .cursor configuration only.

## Planned approach

- **Skill:** `.cursor/skills/test-creation/SKILL.md` with `disable-model-invocation: true`, encoding test file naming (`test_{file-name}.py`), path under `tests/unit/` mirroring source, TDD/black-box/regression, and pointers to `development_practices.mdc` and CONVENTIONS.md.
- **Agent:** `.cursor/agents/test-writer.md` (YAML frontmatter: name, description, model). Invoked with the test-creation skill and a request string (module, behaviour, scope).
- **Workflows:** implement-task-feature.md and implement-task-fix.md Step 2.1 updated to: invoke the test-writer subagent with the test-creation skill and pass a request string (with example). Authority remains in development_practices and CONVENTIONS.

## What was implemented

- **Task 01:** Created `.cursor/skills/test-creation/SKILL.md` with frontmatter and body (naming, path, rules, authority).
- **Task 02:** Created `.cursor/agents/test-writer.md` with frontmatter and prompt (role, steps, output).
- **Task 03:** Updated `implement-task-feature.md` Step 2.1 to invoke test-writer with test-creation skill and request; checklist item updated.
- **Task 04:** Updated `implement-task-fix.md` Step 2.1 to the same pattern, with regression-test emphasis and example request.
- **Task 05:** Verified skill and agent files exist and are well-formed; both workflows reference test-writer and test-creation skill and request; no contradiction with development_practices or CONVENTIONS.
