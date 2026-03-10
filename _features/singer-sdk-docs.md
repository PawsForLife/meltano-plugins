# Feature: Singer SDK documentation

## Background

This repository is a monorepo of Meltano/Singer SDK plugins (extractors and loaders). We need internal documentation that explains how to create Meltano plugins using the Singer SDK, so that contributors and consumers can understand the SDK, the Singer spec, and how to work with plugins in this repo.

References to use:

- **Meltano Singer SDK**: https://sdk.meltano.com/en/latest/
- **Singer Spec**: https://hub.meltano.com/singer/spec/

Documentation must include links to the official SDK and Singer spec where applicable, for deeper understanding of concepts and APIs.

## This Task

1. Research the Singer SDK and Singer Spec (using the weblinks above and, if needed, additional SDK reference pages).
2. Define a docs directory structure under `docs/` that makes finding relevant documents easy (e.g. by path name: taps, targets, spec, monorepo).
3. Create a series of documents in `docs/` that cover:
   - How to create Meltano plugins using the Singer SDK (taps and targets).
   - Key concepts: Singer spec messages (schema, record, state), taps vs targets, streams, sinks.
   - Links to the official SDK and Singer spec (and, where useful, to specific class/reference pages).
   - How to import and use plugins from this monorepo (e.g. `pip_url` with `#subdirectory=`, per-repo layout).
4. Keep each doc focused and under the project’s doc length limits; use an index or TOC where needed.

## Testing Needed

- Documentation builds or renders as intended (e.g. markdown links valid).
- Links to external SDK/Singer pages are correct.
- Monorepo import instructions match the repo’s actual layout (`taps/`, `loaders/`, README examples).
