# Task Plan: 04-documentation-updates

## Overview

This task updates user-facing and AI-context documentation so contributors know how to bootstrap the monorepo and run pre-commit from the repository root. It does not add or change code; it only edits README.md, docs/monorepo/README.md, and docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md to describe the behaviour delivered by tasks 01–03 (wrapper script, root install.sh, root .pre-commit-config.yaml). All wording must match the implemented behaviour and remove or replace any "no repo-wide install.sh" statements.

**Scope:** Documentation only. No automated tests for docs; validation is manual consistency check and clarity review.

**Dependencies:** Tasks 01 (wrapper script), 02 (root install.sh), and 03 (root .pre-commit-config.yaml) must be complete so documentation describes actual behaviour.

---

## Files to Create/Modify

| File | Action | Summary of changes |
|------|--------|--------------------|
| `README.md` | Modify | Add Development/Contributing content: root `./install.sh`, pre-commit install, `pre-commit run --all-files`; state that root install.sh runs each plugin's install.sh, installs pre-commit if missing, runs `pre-commit install`; require one run of root `./install.sh` so each plugin has a `.venv`. |
| `docs/monorepo/README.md` | Modify | Add section (or subsection) describing root **install.sh** (discovers plugins via `scripts/list_packages.py`, runs each plugin's `install.sh`) and root **pre-commit** (runs ruff, mypy, optionally pytest per plugin using that plugin's venv; discovery via same `list_packages.py` as CI). |
| `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md` | Modify | Add root-level commands (or "Repo root" subsection): root `./install.sh`, `pre-commit install`, `pre-commit run --all-files`. Retain existing per-plugin command tables. Replace "No repo-wide install.sh" with statement that root install.sh exists. |

### README.md — Specific content to add

- **Placement:** Add a **Development** or **Contributing** section, or a subsection under an existing Contributing section, after the main Installation section (Meltano usage) and before or within Directory layout/Documentation.
- **Required points (concise):**
  - To bootstrap all plugins and git hooks: run `./install.sh` from the repository root.
  - Root install.sh runs each plugin's install.sh (discovery via `scripts/list_packages.py`), then installs pre-commit if not present and runs `pre-commit install`.
  - To check all files without committing: run `pre-commit run --all-files`.
  - Contributors must run root `./install.sh` at least once so each plugin has a `.venv` before pre-commit hooks will work.
- **Style:** Short bullets or one short paragraph; no duplication of full install.sh or pre-commit internals.

### docs/monorepo/README.md — Specific content to add

- **Placement:** After "CI and plugin standards" or in a new "Root-level tooling" (or equivalent) subsection; ensure it does not replace the existing CI/discovery description but complements it.
- **Required points:**
  - The repository provides a root **install.sh** that discovers plugin directories via `scripts/list_packages.py` and runs each plugin's `install.sh`.
  - Root **pre-commit** runs ruff, mypy (and optionally pytest) per plugin using that plugin's virtual environment; discovery uses the same `list_packages.py` as CI.
- **Wording:** Declarative; align with implementation.md (discovery, per-plugin venv, no config edits for new plugins).

### docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md — Specific content to add/change

- **Add:** A "Repo root" or root-level commands subsection in "Key Commands (Shell)" (before or after the per-plugin tables). Include:
  - Root `./install.sh` — bootstrap all plugins (and pre-commit install when missing, then `pre-commit install`).
  - `pre-commit install` — install git hooks (after root install.sh).
  - `pre-commit run --all-files` — run all hooks on all files.
- **Retain:** Existing tables for `taps/restful-api-tap/` and `loaders/target-gcs/` (single-plugin workflows).
- **Replace:** The sentence "No repo-wide install.sh" (line 45 in current version) with a sentence stating that root install.sh exists and bootstraps all plugins and pre-commit; per-plugin commands remain for working in a single plugin directory.

---

## Test Strategy

- **No automated tests** for documentation (per master testing.md and task 04: "No automated tests for documentation").
- **Manual verification:**
  - Docs are consistent with the implementation: root install.sh discovers via list_packages.py, runs each plugin's install.sh, installs pre-commit if missing, runs `pre-commit install`; pre-commit hook runs ruff/mypy (and optionally pytest) per plugin using that plugin's .venv.
  - Wording is clear for a contributor who has just cloned the repo (run root `./install.sh` first, then pre-commit works).
  - No remaining "no repo-wide install" or "No repo-wide install.sh" in QUICK_REFERENCE or elsewhere.

---

## Implementation Order

1. **README.md** — Add Development/Contributing content so the main repo README is the first place contributors see root workflow.
2. **docs/monorepo/README.md** — Add root install.sh and pre-commit behaviour so monorepo docs match CI and root tooling.
3. **docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md** — Add root commands and update "no repo-wide install" wording so AI and humans have a single quick reference.

---

## Validation Steps

1. **Read-through:** Read each modified section; confirm no contradictions and that all three docs describe the same workflow (root install.sh → pre-commit install → pre-commit run --all-files).
2. **Cross-check with implementation:** Confirm that:
   - Root install.sh is described as using `scripts/list_packages.py` and running each plugin's `./install.sh`; installing pre-commit if missing; running `pre-commit install`.
   - Root pre-commit is described as running ruff, mypy (and optionally pytest) per plugin using that plugin's venv, with discovery via list_packages.py.
3. **Search for obsolete wording:** Grep for "no repo-wide", "No repo-wide", "repo-wide install" and ensure QUICK_REFERENCE (and any other hit) now states that root install.sh exists.
4. **Consistency with master plan:** Ensure wording matches plans/master/documentation.md and implementation.md (discovery, per-plugin venv, optional pytest).

---

## Documentation Updates

This task **is** the documentation update for the feature. No further documentation deliverables are required for task 04. After this task, README, docs/monorepo, and AI_CONTEXT_QUICK_REFERENCE are the only docs that need to reflect root install and pre-commit; implementation plan and planning docs in `_features/root-pre-commit-and-install/` remain the developer reference.

If README or docs reference a "Contributing" or "Development" section that is defined elsewhere (e.g. CONTRIBUTING.md), add or link as appropriate without creating new files unless the project already uses them.
