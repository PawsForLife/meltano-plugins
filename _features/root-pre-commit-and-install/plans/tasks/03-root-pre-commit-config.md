# Task Plan: 03-root-pre-commit-config

## Overview

This task adds a root-level `.pre-commit-config.yaml` so that `pre-commit run` (and git hook execution) invokes the wrapper script `scripts/run_plugin_checks.sh`, which discovers plugins via `list_packages.py` and runs ruff and mypy (and optionally pytest) per plugin using each plugin’s `.venv`. It accomplishes the “root pre-commit” objective of the feature without changing any plugin code or the existing plugin-level config at `loaders/target-gcs/.pre-commit-config.yaml`.

**Scope:** Create exactly one new file at repository root. No modifications to existing files (no edits to wrapper script, install.sh, or plugin configs).

**Prerequisite:** Task 01 (wrapper script) must be complete: `scripts/run_plugin_checks.sh` exists, is executable, and runs successfully when invoked from repo root (e.g. `./scripts/run_plugin_checks.sh`).

---

## Files to Create/Modify

### Create

| File | Description |
|------|--------------|
| `.pre-commit-config.yaml` (repository root) | New file. Single `repos:` list with one `repo: local` entry and one hook that runs the wrapper script. |

### Modify

None. Do not change `loaders/target-gcs/.pre-commit-config.yaml` or any other file.

---

## Exact Specification for `.pre-commit-config.yaml`

- **Location:** Repository root (same directory as `install.sh`, `README.md`).
- **Format:** YAML. Top-level key `repos:` (list).
- **Single repo entry:**
  - `repo: local`
  - `hooks:` (list) with exactly one hook object having:
    - **id:** e.g. `plugin-checks` (string; used by pre-commit in output and `pre-commit run plugin-checks`).
    - **name:** Human-readable description, e.g. `Run plugin checks (ruff, mypy)`.
    - **entry:** Path to the wrapper script. Use `scripts/run_plugin_checks.sh` so pre-commit runs it from repo root; if the system does not execute scripts without a shell, use `bash scripts/run_plugin_checks.sh`. The script must be executable (task 01 ensures this).
    - **language:** `system` (no pre-commit-managed env; script uses repo root and each plugin’s `.venv`).
    - **pass_filenames:** `false` (the script discovers plugin paths via `list_packages.py`; it does not operate on a list of filenames).
    - **files** or **always_run:** Either `files: '^taps/|^loaders/'` so the hook runs when any file under `taps/` or `loaders/` changes, or `always_run: true` so it runs on every commit. Master plan allows either; choose one and apply consistently.
- **Optional:** A one-line comment at the top (e.g. that the hook runs plugin checks via the wrapper script). Keep minimal; pre-commit config is not the place for long prose.

**Example structure (illustrative; implement to match the above):**

```yaml
# Root pre-commit: runs plugin checks (ruff, mypy) via wrapper script.
repos:
  - repo: local
    hooks:
      - id: plugin-checks
        name: Run plugin checks (ruff, mypy)
        entry: scripts/run_plugin_checks.sh
        language: system
        pass_filenames: false
        files: '^taps/|^loaders/'
```

If `entry` must be `bash scripts/run_plugin_checks.sh` for portability, use that; otherwise the direct script path is sufficient.

---

## Test Strategy

- **No new application or unit tests** are required for this task (per master testing.md).
- **Validation is behavioural and manual:**
  1. **Success path:** From repo root, after `./install.sh` has been run (so every discovered plugin has a `.venv` and passing checks), run `pre-commit run --all-files`. Expected: exit code 0; hook “plugin-checks” (or the chosen id) runs and all plugin checks pass. Do not assert hook invocation counts or internal behaviour.
  2. **Failure path (optional):** If a plugin has no `.venv` or a check fails (e.g. introduce a mypy error in a plugin), run `pre-commit run --all-files` (or run the wrapper script directly). Expected: non-zero exit. Again, no assertions on internal behaviour.
- **Regression:** Existing plugin test suites and CI remain unchanged. No new pytest files or marks.

---

## Implementation Order

1. **Confirm prerequisite:** Ensure `scripts/run_plugin_checks.sh` exists and is executable; run it once from repo root and confirm it exits 0 when all plugins are healthy.
2. **Create root `.pre-commit-config.yaml`:**
   - Add `repos:` with one `repo: local` entry.
   - Add the single hook with `id`, `name`, `entry`, `language: system`, `pass_filenames: false`, and either `files: '^taps/|^loaders/'` or `always_run: true`.
   - Optionally add a one-line comment at the top.
3. **Validate:** From repo root run `pre-commit run --all-files` and confirm exit 0 (and that the hook runs). If pre-commit is not installed, install it (e.g. `pip install pre-commit` or as per root install.sh) and run `pre-commit install` once; then run `pre-commit run --all-files`.

---

## Validation Steps

- [ ] `.pre-commit-config.yaml` exists at repository root.
- [ ] File is valid YAML and valid pre-commit config (e.g. `pre-commit run --all-files` does not error with a config parse failure).
- [ ] The single hook runs the wrapper script (observable by hook output and success/failure of plugin checks).
- [ ] From repo root, after a full root `./install.sh`, `pre-commit run --all-files` exits 0.
- [ ] `loaders/target-gcs/.pre-commit-config.yaml` is unchanged and remains optional for single-plugin workflows.

---

## Documentation Updates

None required as part of this task. Documentation (README, docs/monorepo, AI_CONTEXT_QUICK_REFERENCE) is updated in task 04; this task only adds the config file.

---

## Interfaces and Contracts (from master interfaces.md)

- **Root `.pre-commit-config.yaml`:** pre-commit runs the hook’s `entry` from repo root. The entry (wrapper script) must be executable and fulfil the wrapper script contract: discover plugins via `list_packages.py`, run ruff and mypy (and optionally pytest) per plugin using that plugin’s `.venv`, exit 0 only when all pass. This task does not implement the script; it only wires it from pre-commit.

## Out of Scope

- Editing or removing `loaders/target-gcs/.pre-commit-config.yaml`.
- Changing `scripts/run_plugin_checks.sh` or `install.sh`.
- Adding CI jobs or new test files.
- Documentation changes (handled in task 04).
