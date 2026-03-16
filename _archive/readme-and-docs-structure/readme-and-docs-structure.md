# Archive: README and documentation structure

Summary of the **readme-and-docs-structure** feature: documentation-only restructure to separate user-facing and developer-facing content across the repo and plugin READMEs.

---

## The request

Documentation had to be brought in line with a clear structure after large codebase changes:

- **Plugin READMEs** should present **user-facing** content (installation, configuration, usage) for people using the plugin in a Meltano project.
- **Developer documentation** (local setup, lint/test, CI, contributing) should live in each plugin’s **docs folder** and be **linked from** the plugin README.
- The **repository README** should provide an executive summary, list available plugins (extractors/taps and loaders/targets), and point to repo-level documentation for **developing new plugins** without duplicating that content.

Goals: keep user and developer audiences clearly separated and avoid README bloat.

**Concrete asks:**

- **Repo README:** Retain/refine executive summary and plugins table; ensure a clear reference to repo documentation (e.g. `docs/`) for developing new plugins; do not duplicate developer guides.
- **Each plugin README** (e.g. `taps/restful-api-tap/README.md`, `loaders/target-gcs/README.md`): Focus on user content (what the plugin is, installation including `pip_url`/monorepo, configuration, usage). Remove or relocate lengthy developer sections (e.g. “Developer Resources”, lint/test, Meltano dev testing) into the plugin’s `docs/` folder and add a short “Developer documentation” link.
- **Plugin `docs/` folders:** Create or use existing `docs/` under each plugin; add a developer guide (e.g. `docs/DEVELOPMENT.md`) covering local env setup, running tests, lint/format/type-check, and plugin-specific dev notes; link from the plugin README.
- No sensitive or internal-only content in user-facing READMEs.

**Testing:** No automated tests for documentation-only changes. Manual verification: plugin READMEs read as user-focused; developer links resolve; repo README clearly points to docs for developing new plugins; all links work.

---

## Planned approach

**Chosen solution:** Single developer guide per plugin (Option A). Documentation-only; no new code or external libraries.

- **Repo README:** Retain executive summary and plugins table. Keep the link to `docs/` and refine wording so it is explicit that **developing new plugins** is covered there (Singer SDK, Singer spec, building taps/targets, monorepo usage). Keep Development to a short bootstrap (e.g. `./install.sh`, pre-commit); detailed contributor/plugin-development instructions live in `docs/`.
- **Plugin READMEs:** Focus on user content only. Remove the long “Developer Resources” block from each plugin README and replace with one line linking to the plugin’s developer doc (e.g. “Developer documentation: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)” or “See [Development guide](docs/DEVELOPMENT.md).”).
- **Plugin `docs/` and developer guide:**
  - **target-gcs:** Create `loaders/target-gcs/docs/` and add `docs/DEVELOPMENT.md`. Content: Python 3.12+, uv, `./install.sh`; ruff and mypy; pytest and test layout; optional Meltano dev testing; link to Meltano/Singer SDK dev guide. Source: current “Developer Resources” from target-gcs README.
  - **restful-api-tap:** Use existing `taps/restful-api-tap/docs/` (keep `AI_CONTEXT/` as-is). Add `docs/DEVELOPMENT.md` alongside `AI_CONTEXT/`. Same topics as target-gcs; source: “Developer Resources” from tap README.
- **Naming:** `docs/DEVELOPMENT.md` preferred for the developer guide so `docs/README.md` can later serve as an index if multiple dev docs are added.
- **Links and safety:** All new/updated links (repo → docs, plugin README → plugin docs) verified manually; no sensitive or internal-only content in user-facing READMEs.
- **Changelog:** Update root `CHANGELOG.md` with an entry for the documentation restructure; optionally update plugin CHANGELOGs for visibility.

**Architecture:** Audience separation—user-facing docs (what the plugin is, install, config, usage) in plugin READMEs; developer docs (local env, tests, ruff/mypy, CI, Meltano dev testing, SDK link) in each plugin’s `docs/DEVELOPMENT.md`, reached via one link from the plugin README. Repo `docs/` remains the canonical place for “developing new plugins”; no structural change to repo `docs/`. All doc files under 500 lines (content_length.mdc).

**Task breakdown (execution order 01 → 07):**

1. Create `loaders/target-gcs/docs/` and `docs/DEVELOPMENT.md`.
2. Create `taps/restful-api-tap/docs/DEVELOPMENT.md`.
3. Update target-gcs README: remove Developer Resources, add developer link.
4. Update restful-api-tap README: remove Developer Resources, add developer link.
5. Refine repo README: explicit “developing new plugins” in Documentation section.
6. Update root CHANGELOG; optionally plugin CHANGELOGs.
7. Manual verification (links, audience separation, no sensitive content in user-facing READMEs).

Dependencies: developer guides (01, 02) create link targets before READMEs (03, 04) reference them.

---

## What was implemented

All seven tasks were completed.

**New artifacts:**

- **loaders/target-gcs/docs/:** New directory with `DEVELOPMENT.md` containing local env (Python 3.12+, uv, `./install.sh`), commands (ruff, mypy, pytest), test layout, Meltano dev testing, SDK link, and CI note. Content relocated from target-gcs README “Developer Resources.”
- **taps/restful-api-tap/docs/DEVELOPMENT.md:** New file alongside existing `docs/AI_CONTEXT/`. Same topics as target-gcs; content relocated from tap README “Developer Resources.” `AI_CONTEXT/` unchanged.

**Updated artifacts:**

- **loaders/target-gcs/README.md:** “Developer Resources” section removed. User-facing sections (Installation, Supported formats, Configuration, Authentication, Usage) retained. One “Developer documentation” section added with link: “See [Development guide](docs/DEVELOPMENT.md) for local setup, tests, lint, and contributing.”
- **taps/restful-api-tap/README.md:** “Developer Resources” section removed. One “Developer documentation” section added with the same link style to `docs/DEVELOPMENT.md`. User-facing content (install, config, usage, examples) preserved.
- **README.md** (repo root): Documentation section refined. Single clear reference: “See [docs/](docs/README.md) for **developing new plugins** (Singer SDK, Singer spec, building taps and targets) and using plugins from this monorepo.” No duplicated developer guides.
- **CHANGELOG.md** (root): Entry under 2026-03-16 (### Changed) describing the documentation restructure: separate user and developer docs; per-plugin developer guides and links from plugin READMEs; repo README points explicitly to `docs/` for developing new plugins; link to this archive summary.
- **loaders/target-gcs/CHANGELOG.md** and **taps/restful-api-tap/CHANGELOG.md:** Optional entries added for readme-and-docs-structure (developer guide at `docs/DEVELOPMENT.md`, README user-focused, link to archive summary).

**Verification:** Task 07 manual verification checklist covers repo README, plugin READMEs, existence and content of both developer guides, link resolution (repo → docs, plugin README → plugin docs/DEVELOPMENT.md), absence of sensitive content in user-facing READMEs, and CHANGELOG entries. No automated tests; completion is sign-off when the checklist passes.

**Outcome:** User and developer audiences are separated: plugin READMEs are user-focused with one developer link each; developer content lives in `docs/DEVELOPMENT.md` per plugin; repo README clearly points to `docs/` for developing new plugins. All links resolve from the intended contexts (repo root and each plugin root).
