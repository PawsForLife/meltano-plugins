# Testing: Python 3.12 Typing Standards

## Test Strategy

This feature is a **refactor-only** change: type hints and imports are updated with no intended behaviour change. The testing strategy is:

- **Regression**: All existing tests must pass after the refactor.
- **Static checks**: Linters (Ruff) and type checker (mypy) must pass; fix any new issues introduced by the typing updates.
- **Black-box**: Tests continue to assert observable behaviour (returned values, raised exceptions, emitted records); no new tests that assert on internal call counts or log output.

No new product behaviour is added; therefore no new behaviour-level test cases are required unless a gap is discovered. Optional: run or add a static type-check step in CI if not already present.

## TDD and This Refactor

- **Existing tests first**: Treat the current test suite as the specification. Before changing a file, ensure its tests pass; after changing type hints, re-run tests to confirm no regressions.
- **Type checker as specification**: Where mypy (or pyright) is configured, treat it as part of the gate: typing changes must not introduce new type errors. Fix type errors that appear after replacing old-style hints with 3.12-style.

## Test Execution Order (per component)

1. **restful-api-tap**
   - From `taps/restful-api-tap/`: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check`, `uv run mypy restful_api_tap`.
   - Resolve any failure before moving to the next component.
2. **target-gcs**
   - From `loaders/target-gcs/`: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check`, `uv run mypy target_gcs`.
3. **Scripts**
   - Run script tests as defined at repo root (e.g. `.github/workflows/script-tests.yml` or project docs).

## Test Cases (what is validated)

- **Unit/integration tests**: Unchanged assertions; they validate behaviour. Passing tests confirm that the refactor did not change runtime behaviour.
- **Type checker**: Validates that annotations are consistent and that no new type errors are introduced (e.g. missing imports, wrong types after replacing `Optional` with `X | None`).
- **Linter**: Ruff enforces style and import hygiene; after enabling UP006/UP007/UP045, Ruff will fail on any remaining old-style hints, so the refactor and config together keep the codebase compliant. Unused imports removed when dropping old `typing` symbols must not break anything.

## Integration Test Requirements

No new integration tests. Existing tap and target tests (including SDK standard tests) remain the integration gate. If the project has end-to-end or Meltano pipeline tests, run them after all components are updated to confirm no regressions.

## Validation Steps

1. After each file or logical group of files (e.g. all of `restful_api_tap/`): run pytest for that plugin.
2. After each plugin: run mypy for that plugin’s package.
3. After all changes: run full test suite and any CI workflows (e.g. plugin matrix, script tests).
4. Regression gate: Any failing test that is not explicitly marked as expected failure (`@pytest.mark.xfail`, `@unittest.expectedFailure`) must be fixed before the task is complete.

## Black-Box Approach

- Do not add tests that assert on "typing was updated" (e.g. parsing source or checking for `Optional` in the AST). The contract is: behaviour unchanged, type checker and linter pass.
- If a test fails, fix the implementation (or the type hints) so behaviour is preserved and tests pass; do not change tests to accommodate unintended behaviour changes.
