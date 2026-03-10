# Archive: glossary-terminology-docs

## The request

The project adopted `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md` as the single source of truth for Meltano and Singer terminology. The feature requested a **documentation-only** alignment pass: all in-scope docs and AI context were to use the glossary’s terms so that prose, file names, and AI guidance stay aligned with the Singer Spec and Meltano Singer SDK.

**Scope:** Root README; `docs/` (README and subdir READMEs); every file under `docs/AI_CONTEXT/` (except the glossary itself); and `.cursor` conventions, README, commands, agents, and skills that describe taps, targets, streams, loaders, extractors, or Singer/Meltano concepts. **Out of scope:** Application code, tests, config under `taps/` or `loaders/`; plugin READMEs (separate features); file or directory renames.

**Goal:** Replace informal or inconsistent wording with glossary terms (e.g. tap vs extractor, target vs loader, source/destination, SCHEMA/RECORD/STATE, config file/state file, Catalog, Discovery, replication terms). Replacements were to be context-aware (e.g. “loader” → “target” only when meaning the Singer data loader; retain “loader” for Meltano plugin type).

**Testing:** No new automated tests. Manual verification only: grep for anti-patterns (e.g. “loader” meaning Singer component in technical prose, lowercase “schema”/“record”/“state” when referring to Singer message types), spot-check alignment with the glossary, and confirm existing links and cross-references still work.

---

## Planned approach

**Chosen solution:** Internal, systematic terminology pass over each in-scope file using the glossary. No new tooling; no file or directory renames. Option A/C from planning: per-file review, optionally informed by grep for anti-patterns. Automation (e.g. scripted search-replace) was rejected due to context-sensitivity and risk of wrong fixes.

**Architecture:** Documentation-only. “Architecture” was the grouping of in-scope docs: (1) root README, (2) `docs/` READMEs, (3) `docs/AI_CONTEXT/` (glossary reference-only; all other files updated), (4) `.cursor` (CONVENTIONS, README, commands, agents, skills). Terminology conventions were taken from the glossary: tap/target for Singer components; extractor/loader for Meltano plugin types; source/destination; SCHEMA, RECORD, STATE for message types; config file, state file, Catalog, Discovery; replication terms (FULL_TABLE, INCREMENTAL, replication key, bookmark, etc.); pipeline and ELT as defined in the glossary.

**Task breakdown (four tasks, execution order):**

| Task | Scope |
|------|--------|
| 01 — Root README | `README.md` at repo root |
| 02 — docs READMEs | `docs/README.md`, `docs/taps/README.md`, `docs/targets/README.md`, `docs/monorepo/README.md`, `docs/spec/README.md` |
| 03 — AI context files | All `docs/AI_CONTEXT/*` except `GLOSSARY_MELTANO_SINGER.md` (e.g. AI_CONTEXT_REPOSITORY, AI_CONTEXT_QUICK_REFERENCE, AI_CONTEXT_PATTERNS, per-component context files) |
| 04 — .cursor docs | `.cursor/CONVENTIONS.md`, `.cursor/README.md`, `.cursor/commands/update_context.md`, `.cursor/agents/ai-context-writer.md`, `.cursor/skills/ai-context-component/SKILL.md`, `.cursor/skills/ai-context-quick-reference/SKILL.md`, and any other `.cursor` markdown describing taps, targets, streams, loaders, extractors, or Singer/Meltano concepts |

Per-task steps: read the glossary; for each file, apply context-aware replacements (prose and headings only); preserve links and cross-references; no renames. Validation: grep for anti-patterns, spot-check against glossary, verify links.

---

## What was implemented

All four tasks were completed as planned. The work was **doc-only terminology alignment**; no code, tests, or config under `taps/` or `loaders/` were modified, and no files or directories were renamed.

1. **Task 01 — Root README:** Root `README.md` was updated so that Singer/Meltano concepts use glossary terms (tap/target, extractor/loader, source/destination, and any message-type or replication wording where present). Links, structure, and path references were preserved.

2. **Task 02 — docs READMEs:** `docs/README.md`, `docs/taps/README.md`, `docs/targets/README.md`, `docs/monorepo/README.md`, and `docs/spec/README.md` were updated with the same glossary term replacements. Cross-references and internal/external links were preserved.

3. **Task 03 — AI context files:** All in-scope files under `docs/AI_CONTEXT/` (e.g. `AI_CONTEXT_REPOSITORY.md`, `AI_CONTEXT_QUICK_REFERENCE.md`, `AI_CONTEXT_PATTERNS.md`, and per-component context files such as `AI_CONTEXT_restful-api-tap.md`, `AI_CONTEXT_gcs-loader.md`) were aligned with the glossary. `GLOSSARY_MELTANO_SINGER.md` was not edited. Links and cross-references in AI context docs were preserved.

4. **Task 04 — .cursor docs:** In-scope `.cursor` markdown (CONVENTIONS, README, commands, agents, skills, and any other workflow/agent/skill docs that describe taps, targets, streams, loaders, extractors, or Singer/Meltano concepts) was updated to use glossary terminology. Links and cross-references were preserved.

**Outcomes:** In-scope documentation and AI context now use glossary terminology consistently. No code or test files under `taps/` or `loaders/` were changed. Existing links and cross-references in docs continue to work. Verification was manual (grep for anti-patterns, spot-check alignment with the glossary).
