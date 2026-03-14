---
name: test-creation
description: Use when writing or generating unit/integration tests. Encodes test file naming, path under tests/unit/, TDD, black-box testing, and regression rules.
disable-model-invocation: true
---

# Test Creation

Use this skill when creating or updating tests (unit or integration) for this project.

## When to use

Invoke this skill when the test-writer subagent (or equivalent) is asked to generate or update tests. It is applied only when explicitly invoked with the test-writer; it does not auto-apply.

## Test file naming

- **Pattern:** `test_{file-name}.py` where `{file-name}` is the **source module basename only** (e.g. `simple.py` → `test_simple.py`).
- Folder path has no relevance to the test file name.

## Test path

- Mirror the source path under `tests/unit/`.
- **Example:** source `target_gcs/paths/simple.py` → test `tests/unit/paths/test_simple.py`.
- Use `tests/unit/` for unit tests; global `conftest.py` and `files/` for fixtures and complex test data.

## Rules to follow

- **TDD:** Write tests first, see them fail, then implement.
- **Black-box testing:** Validate behaviour, not internals (no "called_once" or log-line checks; assert returned/updated data).
- **Regression gate:** Any failing test not marked as expected failure (`@pytest.mark.xfail`, `@unittest.expectedFailure`) is a regression and must be fixed.
- **Scope:** One test file per source module; unit tests focus on one module; integration tests are thin and trust unit coverage.
- **Valid tests:** Tests must be able to fail; fix or remove tests that can only pass.

## Authority

Full rules: `@.cursor/rules/development_practices.mdc`. Test layout and path conventions: `@.cursor/CONVENTIONS.md`. Do not contradict them.
