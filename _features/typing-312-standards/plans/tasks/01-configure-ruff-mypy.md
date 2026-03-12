# Task Plan: 01-configure-ruff-mypy

## Overview

This task accomplishes **Phase 0** of the typing-312-standards feature: configure Ruff and mypy so that CI and subsequent refactor tasks enforce Python 3.12 typing style (PEP 585 built-in generics, PEP 604 pipe unions). No application code is refactored; only tool configuration is changed. It establishes the baseline that tasks 02–07 rely on for lint and type checking.

- **restful-api-tap**: Add Ruff rules UP006, UP007, UP045; set mypy `python_version` to 3.12 (in both `pyproject.toml` and `mypy.ini`).
- **target-gcs**: Confirm existing config already includes UP rules and mypy 3.12; no changes required.
- **Repo root / scripts**: No repo-level `pyproject.toml` or `ruff.toml`; no change.

## Files to Create/Modify

| File | Action |
|------|--------|
| `taps/restful-api-tap/pyproject.toml` | In `[tool.ruff.lint]`, add `extend-select = ["UP006", "UP007", "UP045"]`. Confirm `target-version = "py312"` (already set). Do not add full `"UP"` group; only these three rules. |
| `taps/restful-api-tap/mypy.ini` | Set `python_version = 3.12` (replace current `3.9`). Leave all other `[mypy]` and `[mypy-*]` sections unchanged. |
| `loaders/target-gcs/pyproject.toml` | No edits. Confirm `select` includes `"UP"` (covers UP006, UP007, UP045), `target-version = "py312"`, and `[tool.mypy]` `python_version = "3.12"`. |
| Repo root / scripts | No config file at repo root or under `scripts/`; no change. |

## Test Strategy

- **No new pytest tests.** This task is configuration-only.
- **Validation**: Run Ruff and mypy in each plugin. From `taps/restful-api-tap/`: `uv run ruff check .`, `uv run mypy restful_api_tap`. From `loaders/target-gcs/`: `uv run ruff check .`, `uv run mypy target_gcs`.
- **Handling new Ruff violations in restful-api-tap**: Enabling UP006, UP007, UP045 may cause Ruff to report existing old-style hints. Either (1) fix those violations in this task (replace with built-in generics and pipe unions) so that `ruff check` passes, or (2) document that violations are scoped to files refactored in tasks 02–07 and add per-file ignores only for those files so that this task delivers a passing CI baseline. Prefer (1) if the number of violations is small; otherwise (2) with clear per-file ignores.
- **mypy**: Updating `mypy.ini` to 3.12 may surface new type errors. Resolve any new mypy failures in this task so that `mypy restful_api_tap` passes (or document and scope as above).

## Implementation Order

1. **restful-api-tap Ruff** — Edit `taps/restful-api-tap/pyproject.toml`: under `[tool.ruff.lint]`, add `extend-select = ["UP006", "UP007", "UP045"]`. Confirm `target-version = "py312"` in `[tool.ruff]`.
2. **restful-api-tap mypy** — Edit `taps/restful-api-tap/mypy.ini`: set `python_version = 3.12` in `[mypy]`.
3. **Run checks in restful-api-tap** — From `taps/restful-api-tap/`: `uv run ruff check .`, `uv run ruff format --check`, `uv run mypy restful_api_tap`. Fix any new violations or add targeted per-file ignores for files refactored in 02–07 so that all commands pass.
4. **Verify target-gcs** — From `loaders/target-gcs/`: `uv run ruff check .`, `uv run mypy target_gcs`. Confirm no regressions; no config change needed.
5. **Repo root** — Confirm no root or scripts-specific Ruff/mypy config; document N/A in handoff if needed.

## Validation Steps

- [ ] From `taps/restful-api-tap/`: `uv run ruff check .` exits 0.
- [ ] From `taps/restful-api-tap/`: `uv run ruff format --check` exits 0 (if used in CI).
- [ ] From `taps/restful-api-tap/`: `uv run mypy restful_api_tap` exits 0.
- [ ] From `loaders/target-gcs/`: `uv run ruff check .` exits 0.
- [ ] From `loaders/target-gcs/`: `uv run mypy target_gcs` exits 0.
- [ ] Existing pytest suites in both plugins still pass (no code change in this task; tests should be unchanged).

## Documentation Updates

- None required. No new user-facing behaviour or repo structure.
- If per-file Ruff ignores are added for restful-api-tap, consider a short comment in `pyproject.toml` or the task doc that they are temporary until tasks 02–07 refactor those files.
