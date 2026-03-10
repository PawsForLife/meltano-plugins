# Glossary terminology (repo) — archive summary

## The request

Align repository-level and automation assets with `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md` so contributors and automation use consistent Meltano/Singer terminology (tap, target, extractor, loader, source, destination, stream, catalog, config file, state file, SCHEMA/RECORD/STATE). Scope: root README and CHANGELOG, scripts, `.github/workflows`, `.cursor/commands`, `.cursor/workflows`, `.cursor/agents` only. No code under `taps/restful-api-tap/` or `loaders/`; plugin names and paths unchanged. Testing: run repo scripts and project test suite; grep for terminology anti-patterns.

## Planned approach

- **Source of truth:** `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md`.
- **Approach:** Audit in-scope files → replace informal wording with glossary terms → preserve plugin names and paths → exclude tap/loader package code.
- **Tasks (6):** (1) Root README and CHANGELOG, (2) scripts (`list_packages.py`, `scripts/tests/*.py`), (3) `.github/workflows/*.yml`, (4) `.cursor/commands/*.md`, (5) `.cursor/workflows/*.md`, (6) `.cursor/agents/*.md`. No new tests; validation by existing test suite and terminology grep.

## What was implemented

- **Task 01 — Root README and CHANGELOG:** README directory layout bullets updated to “Meltano extractor (tap)” and “Meltano loader (target)”; CHANGELOG “GCS loader” clarified to “GCS loader (target)”; Unreleased entry added for glossary-terminology-repo.
- **Task 02 — Scripts:** `scripts/list_packages.py` and `scripts/tests/test_list_packages.py` docstrings updated to describe package dirs as including tap (extractor) and target (loader) plugin dirs; path literals unchanged.
- **Task 03 — GitHub workflows:** `.github/workflows/plugin-matrix.yml` top comment, workflow name, and step names aligned to “tap and target plugin” / “tap or target plugin” wording; no `run:` or path changes.
- **Task 04 — Cursor commands:** `.cursor/commands/update_context.md` already contained glossary sentence (extractors as taps, loaders as targets); audit only, no file changes.
- **Task 05 — Cursor workflows:** Terminology in `.cursor/workflows/*.md` already aligned where relevant; CHANGELOG bullet added; pipeline state vs Singer state kept distinct.
- **Task 06 — Cursor agents:** All seven agent files already had Resources sentences referencing the glossary; CHANGELOG bullet added.

All six tasks completed; script and package tests pass; terminology anti-pattern grep clean for in-scope files.
