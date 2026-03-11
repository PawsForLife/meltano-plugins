# Possible Solutions — root-pre-commit-and-install

## Context

- **Pre-commit framework** ([pre-commit.com](https://pre-commit.com)): manages git hook scripts; supports “local” hooks (`repo: local`) that run repository-owned scripts. Hooks can use `language: system` to run a binary or script without a pre-commit-managed env.
- **Requirement**: Run ruff, mypy (and optionally pytest) **per plugin**, using **that plugin’s .venv**, from repo root.
- **Constraint**: pre-commit does not natively “run in subdirectory with that directory’s venv”; we must do that in the hook’s entry (script or inline).

---

## 1. Pre-commit: local hook + wrapper script (recommended)

**Approach**: One root `.pre-commit-config.yaml` with `repo: local` and `language: system`. Entry points at a script (e.g. `scripts/run_plugin_checks.sh`) that (a) discovers plugin dirs via `list_packages.py` or globs, (b) for each dir runs that dir’s `.venv/bin/ruff` and `.venv/bin/mypy` (and optionally `.venv/bin/pytest`) with correct cwd and package name.

**Pros**:
- Single source of truth for “what runs on commit”.
- Script is testable and reusable (e.g. from root `install.sh` or CI).
- Uses each plugin’s venv and config; no version drift.
- Aligns with pre-commit’s intended use of local hooks for “state in your repo” (e.g. app venvs).

**Cons**:
- Requires a small script and a way to map plugin path → mypy package name.
- If a plugin has no `.venv`, hook fails (document: run root `install.sh` first).

**References**: [pre-commit local hooks](https://pre-commit.com/#repository-local-hooks); [Issue #1417](https://github.com/pre-commit/pre-commit/issues/1417) (run in subdirectory via `bash -c 'cd dir && ...'`).

---

## 2. Pre-commit: one local hook per plugin (static)

**Approach**: Root `.pre-commit-config.yaml` with one `repo: local` hook per plugin (e.g. `ruff-mypy-restful-api-tap`, `ruff-mypy-target-gcs`). Each hook’s `entry` runs a fixed path: e.g. `bash -c 'cd taps/restful-api-tap && .venv/bin/ruff check . && ...'`. `files` regex restricts each hook to that plugin’s path.

**Pros**:
- No discovery logic; explicit and simple.
- No mapping of path → mypy package; each hook hardcodes the package name.

**Cons**:
- Adding a new plugin requires editing the root config.
- Duplication; diverges from CI/list_packages discovery.

---

## 3. Pre-commit: single “run root install” hook

**Approach**: One local hook that runs root `./install.sh` (which in turn runs each plugin’s `install.sh`, including full pytest).

**Pros**:
- Trivial config; one entry.

**Cons**:
- Very slow on every commit (full install + all tests).
- Not recommended by pre-commit for long-running hooks; poor UX.

---

## 4. Manual script only (no pre-commit)

**Approach**: Root `install.sh` only; document “run `./install.sh` before pushing”. No root `.pre-commit-config.yaml`; no git hooks.

**Pros**:
- No pre-commit dependency; simple.
- Same script can be used in CI or locally.

**Cons**:
- No automatic run on commit; relies on discipline; issues surface later (e.g. in CI).

---

## 5. CI-only checks

**Approach**: Rely entirely on existing CI (plugin-unit-tests.yml) to run ruff, mypy, pytest per plugin. No root install.sh, no root pre-commit.

**Pros**:
- No local tooling; zero extra setup.

**Cons**:
- Feedback only after push; no “before commit” gate; more failed PRs and round-trips.

---

## 6. Local hooks vs system hooks (pre-commit)

- **Local hooks** (`repo: local`): Scripts live in the repo; run in a context defined by `language` (e.g. `system` = no pre-commit-managed env). Used when the hook needs the repo’s own env (e.g. each plugin’s `.venv`).
- **System hooks** here means “hooks that run system/repo binaries” (e.g. `language: system`), not “system-wide git hooks”. pre-commit installs into `.git/hooks` by default; that’s repo-local. So we use **local hooks** with **language: system** and an **entry** that invokes a script (or inline bash) which `cd`s into each plugin and uses that plugin’s `.venv`.

**Verdict**: Use **repo: local**, **language: system**, **entry**: path to a script that discovers plugins and runs each plugin’s venv-based ruff/mypy (and optionally pytest). Script keeps logic out of the YAML and is easier to maintain.

---

## 7. Comparison summary

| Option | Pre-commit | Root install.sh | Discovery | Per-plugin venv | New plugin |
|--------|------------|------------------|-----------|-----------------|------------|
| 1. Local hook + script | Yes | Yes | Script (list_packages or glob) | Yes | Auto | Best fit |
| 2. One hook per plugin | Yes | Yes | N/A (static) | Yes | Edit config | OK, not scalable |
| 3. Hook runs root install | Yes | Yes | N/A | Yes | Auto | Too slow |
| 4. Script only | No | Yes | Script | Yes | Auto | No commit gate |
| 5. CI only | No | No | CI | N/A | Auto | Late feedback |

**Recommendation**: **Option 1** — root `.pre-commit-config.yaml` with a local hook that calls a small wrapper script; script discovers plugins (same as root `install.sh`, e.g. `list_packages.py`) and for each plugin runs ruff, mypy (and optionally pytest) using that plugin’s `.venv`. Root `install.sh` discovers plugins and runs each `./install.sh`.
