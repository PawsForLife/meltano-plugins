# Archive: Singer SDK documentation

## The request

The repository is a monorepo of Meltano/Singer SDK plugins (extractors and loaders). The feature requested internal documentation so contributors and consumers could:

- Create Meltano plugins with the Singer SDK (taps and targets).
- Understand key concepts: Singer spec messages (schema, record, state), taps vs targets, streams, sinks.
- Use official references: [Meltano Singer SDK](https://sdk.meltano.com/en/latest/) and [Singer Spec](https://hub.meltano.com/singer/spec/).
- Import and use plugins from this monorepo (e.g. `pip_url` with `#subdirectory=`).

Requirements included a clear `docs/` structure (e.g. by path: taps, targets, spec, monorepo), focused docs under the project’s length limit, and links to the official SDK and Singer spec. Testing was defined as: docs render correctly, external links are valid, and monorepo import instructions match the repo layout (`taps/`, `loaders/`, README).

---

## Planned approach

**Chosen solution:** Topic-based docs under `docs/`, with one topic per subdirectory. Option 3 (by topic with subdirs) was selected over a single long guide, role-based docs, or a flat set of files — to match requested path names, stay under the 500-line rule, and keep spec, implementation, and repo usage clearly separated.

**Doc structure:**

- **docs/README.md** — Entry point: purpose of the doc set, TOC to spec/taps/targets/monorepo, primary links to SDK and Singer Spec.
- **docs/spec/README.md** — Singer concepts only: message types (schema, record, state), taps vs targets, config/state/catalog; links to Singer Spec (and optionally SDK Implementation).
- **docs/taps/README.md** — Building taps: Tap/Stream, cookiecutter, stream types (REST/GraphQL/SQL), config schema, testing; links to SDK Getting Started, Reference, guides, testing.
- **docs/targets/README.md** — Building targets: Target/Sink, RecordSink vs BatchSink, config, testing; same link pattern as taps.
- **docs/monorepo/README.md** — Using plugins from this repo: `pip_url` with `#subdirectory=`, concrete YAML examples from repo README, directory layout, version pinning; links to Meltano and pip docs.

**Task breakdown (execution order):** (1) Create docs index; (2) Create spec doc; (3) Create taps doc; (4) Create targets doc; (5) Create monorepo doc; (6) Optional: add Documentation section to repo root README. Tasks 02–05 depend on 01 for index links; 05 references repo README for examples. No code or test file changes; validation by link checks and manual review.

---

## What was implemented

All six tasks were completed.

- **docs/README.md** — Intro, table of contents (spec, taps, targets, monorepo), and external references to Meltano Singer SDK and Singer Spec.
- **docs/spec/README.md** — Messages (schema, record, state), Taps vs targets, Config/state/catalog; links to Singer Spec and SDK Implementation.
- **docs/taps/README.md** — Goal, Getting started (cookiecutter, Tap + stream), Stream types table (REST/GraphQL/SQL), Config, Testing, Further reading; SDK links (Getting Started, Reference, config-schema, testing, guides, code samples).
- **docs/targets/README.md** — Goal, Getting started (cookiecutter, Target + Sink), Sink types (RecordSink vs BatchSink), Config, Testing, Further reading; same SDK link set.
- **docs/monorepo/README.md** — Purpose, Mechanism (`pip_url` + `#subdirectory=`), Concrete YAML examples (extractor and loader from repo README), Directory layout table, Version pinning, References (Meltano plugin management, plugin definition syntax, pip VCS support); internal link to repo root README.
- **Root README** — Optional task implemented: a short “Documentation” section was added linking to `docs/README.md`.

Docs are concept- and task-focused, under 500 lines each, and use the canonical SDK and Singer Spec URLs from the plan. Monorepo examples use `taps/restful-api-tap` and `loaders/gcs-loader` and align with the repo README Installation and Directory layout.
