# Task: Configure Ruff and mypy for Python 3.12 typing style

## Background

The feature requires Ruff to enforce PEP 585/604 style (built-in generics and pipe unions) and mypy to use `python_version = "3.12"` everywhere. Phase 0 establishes this configuration so CI and subsequent refactor tasks can rely on it. No code refactor is done in this task; only tool config is changed.

**Dependencies:** None. This is the first task.

## This Task

- **restful-api-tap** (`taps/restful-api-tap/pyproject.toml`):
  - In `[tool.ruff.lint]`, add to `select` the pyupgrade rules: **UP006** (use `list`, `dict`, etc. instead of `typing.List`/`Dict`), **UP007** (use `X | Y`), **UP045** (use `X | None`). Use `extend-select = ["UP006", "UP007", "UP045"]` so only these UP rules are added.
  - Confirm `target-version = "py312"` is set (already present).
- **restful-api-tap** (`taps/restful-api-tap/mypy.ini`):
  - Set `python_version = 3.12` (replace current `3.9`).
- **target-gcs** (`loaders/target-gcs/pyproject.toml`):
  - Confirm `select` already includes `"UP"` (UP006, UP007, UP045 are part of UP). No change needed unless a subset is used; if so, ensure UP006, UP007, UP045 are in the effective rule set.
  - Confirm `target-version = "py312"` and `[tool.mypy]` `python_version = "3.12"` (already present).
- **Repo root / scripts:** If the repo has a root-level `pyproject.toml` or `ruff.toml` that applies to `scripts/`, add the same UP rules and `target-version = "py312"`. Otherwise, no change.
- Run `uv run ruff check .` and `uv run mypy restful_api_tap` from `taps/restful-api-tap/` and fix any violations introduced by the new Ruff rules (or document that violations will be fixed in tasks 02–07). Same for target-gcs from `loaders/target-gcs/` if needed.

**Acceptance criteria:** Ruff and mypy configs in tap and target-gcs enforce 3.12 typing style; mypy.ini uses python_version 3.12; running ruff/mypy in each plugin completes (any remaining violations are scoped to files refactored in later tasks).

## Testing Needed

- From `taps/restful-api-tap/`: `uv run ruff check .`, `uv run mypy restful_api_tap`. Resolve or scope any new failures.
- From `loaders/target-gcs/`: `uv run ruff check .`, `uv run mypy target_gcs`. Confirm no regressions.
- No new pytest tests; this task is configuration only. Existing tests need not pass until code is refactored in subsequent tasks (if enabling UP rules causes no code changes, existing tests should still pass).
