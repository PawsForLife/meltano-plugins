# Task Plan: 02 — Root `install.sh`

## Overview

This task adds a single root-level `install.sh` at the repository root. The script bootstraps all plugins by discovering them via `scripts/list_packages.py`, running each plugin's `./install.sh` in turn and stopping on the first failure. After all plugin installs succeed, it ensures pre-commit is available (installing it if missing) and runs `pre-commit install` so git hooks are installed. This gives contributors one command at repo root to prepare the monorepo for development and pre-commit.

**Scope**: Create only `install.sh` at repo root. No changes to plugin code, `list_packages.py`, or documentation (documentation is task 04).

**Dependencies**: Requires `scripts/list_packages.py` to exist and to accept `ROOT` as first argument and output one relative path per line (no `--json`). Does not depend on task 01 (wrapper script) or task 03 (pre-commit config); those are separate.

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `install.sh` | **Create** | New executable at repository root. Only file created or modified in this task. |

No other files are created or modified. Do not change `scripts/list_packages.py`, README, or docs in this task.

---

## Test Strategy

- **No new application unit tests.** Per master testing plan, validation is behavioural.
- **Behavioural acceptance**:
  1. **Success**: From repo root, run `./install.sh`; exit code must be 0 when every plugin's `install.sh` and `pre-commit install` succeed. No assertion on number of invocations.
  2. **Plugin failure**: If any plugin's `install.sh` fails (e.g. temporarily break a plugin or mock failure), root `install.sh` must exit non-zero and must stop on first failure (remaining plugins may not run).
  3. **Pre-commit install failure**: If `pre-commit install` fails (e.g. not a git repo or hook install error), root `install.sh` must exit non-zero.
- **Optional black-box script test**: If adding a script test (e.g. under `scripts/tests/` or similar), it must only assert exit code of `./install.sh` (e.g. 0 when all succeed). It must not assert call counts, log lines, or internal behaviour (per development_practices.mdc).
- **TDD**: No test-first requirement for application code. If an optional script test is added, write the test first (e.g. “root install exits 0 when all plugin installs and pre-commit install succeed”), then implement until it passes.

---

## Implementation Order

Execute in this order so the implementer can follow without ambiguity.

1. **Create `install.sh` at repository root** (path: `install.sh` relative to repo root).

2. **Top-of-file comment**  
   State purpose in a short comment block: bootstrap all plugins by running each plugin's `install.sh`; discovery via `list_packages.py`; then install pre-commit if missing and run `pre-commit install`.

3. **Shebang and root resolution**  
   - Shebang: `#!/usr/bin/env bash`.  
   - Set repo root: `ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` so the script works regardless of current working directory.

4. **Discovery**  
   Run `python "$ROOT/scripts/list_packages.py" "$ROOT"` (no `--json`). Script outputs one relative path per line; treat each non-empty line as a plugin path. Use a loop that reads lines (e.g. `while IFS= read -r path` or equivalent). Skip empty lines if any.

5. **Per-plugin install**  
   For each path: run `(cd "$ROOT/$path" && ./install.sh)`. If the exit code is non-zero, exit immediately with that same exit code (stop on first failure). Do not run remaining plugins after a failure.

6. **Pre-commit availability**  
   After all plugin installs succeed, check if pre-commit is available (e.g. `command -v pre-commit`). If not available, install it using a single mechanism that allows hooks to run without activating a venv (e.g. `pip install pre-commit` or `pip3 install pre-commit`). Do not require a root venv; prefer system or user pip. If the install step fails, exit non-zero.

7. **Install hooks**  
   From repo root, run `pre-commit install`. If it returns non-zero, exit with that code.

8. **Make executable**  
   Ensure `install.sh` is executable: `chmod +x install.sh` (or rely on VCS/file mode; document that the file must be executable).

9. **Edge cases**  
   - If `list_packages.py` returns no paths, the loop runs zero times; then pre-commit check/install and `pre-commit install` still run.  
   - If the repo is not a git repo, `pre-commit install` may fail; script must exit non-zero.  
   - Use `set -e` only if it does not conflict with capturing exit codes from subshells; otherwise explicitly check each critical command’s exit code and exit accordingly.

---

## Validation Steps

1. **Happy path**: From repository root, run `./install.sh`. Expect exit code 0. Confirm that each plugin’s environment (e.g. `.venv`, ruff, mypy, pytest) is in place and that `pre-commit install` has run (e.g. `.git/hooks/pre-commit` exists).
2. **Plugin failure**: Temporarily cause one plugin’s `install.sh` to fail (e.g. remove execute bit or introduce a failing command). Run `./install.sh` from root. Expect non-zero exit and that the script stops (e.g. later plugins not fully run).
3. **Pre-commit missing**: In a clean environment where pre-commit is not installed, run `./install.sh` (after ensuring plugins install). Expect script to install pre-commit (or exit with clear failure) and then run `pre-commit install`; if `pre-commit install` fails, exit code must be non-zero.
4. **Discovery**: Ensure the set of directories run matches `list_packages.py` output (no extra or missing plugins). Validated implicitly by success of step 1 and by repo layout.

---

## Documentation Updates

**None.** Documentation changes (README, docs/monorepo, AI_CONTEXT_QUICK_REFERENCE) are handled in task 04. This task only adds `install.sh`; do not update docs here.

---

## Interface Contract (Reference)

From master interfaces.md:

- **Invocation**: From repo root: `./install.sh`. No arguments.
- **Input**: None (discovery uses repo root via `list_packages.py`).
- **Output**: Stdout/stderr from each plugin’s `install.sh`, then pre-commit install if applicable. Exit code: 0 if all plugin installs and pre-commit install succeeded; non-zero on first plugin failure or if pre-commit install fails.
- **Contract**: Script is executable; depends on `python` (or `python3`) and `scripts/list_packages.py`; each discovered path must have an executable `install.sh`. After all plugin installs succeed, script installs pre-commit if not present and runs `pre-commit install` at repo root.

---

## Notes for Implementer

- `list_packages.py` usage: `python scripts/list_packages.py [ROOT]` — pass `"$ROOT"` explicitly so behaviour is correct regardless of caller’s CWD. Default (no args) is current working directory; passing `$ROOT` is preferred for clarity.
- Pre-commit: Use one consistent method to install (e.g. `pip install pre-commit`). The repo has no root `pyproject.toml`; per-plugin tooling uses uv. Installing pre-commit via pip ensures the hook can run without activating a root venv.
- Do not add or modify tests for plugin application code. Optional script tests must be black-box (exit code only).
