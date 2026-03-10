# Pipeline Scratchpad

## Feature: singer-sdk-docs

- **Pipeline State:** Phase 1 (research) complete; Phases 2–6 Not started.
- **Task Completion Status:** Research planning docs created.
- **Execution Order:** (empty until Phase 3 completes).
- **Output directory:** `_features/singer-sdk-docs/planning/` (impacted-systems, new-systems, possible-solutions, selected-solution).

### Research summary (Phase 1)

- **Key findings:** (1) SDK and Singer Spec are the canonical sources—SDK covers Tap/Stream/Target/Sink, Getting Started, guides, testing, and class reference; Singer Spec defines schema/record/state messages, config/state/catalog, and taps vs targets. (2) Repo is a monorepo with `taps/restful-api-tap` and `loaders/gcs-loader`; each has its own `pyproject.toml`; README already documents `pip_url` with `#subdirectory=` for Meltano. (3) Docs should live under `docs/` by topic (spec, taps, targets, monorepo) to stay within 500-line limit and match feature ask. (4) Monorepo doc can reference README for exact YAML and layout; no new mechanisms required.
- **Selected solution:** Topic-based structure under `docs/` with `README.md` index plus `spec/`, `taps/`, `targets/`, `monorepo/` subdirs, each with a README; each doc links to the relevant SDK and Singer Spec URLs; monorepo doc points to repo README for Installation and directory layout.
