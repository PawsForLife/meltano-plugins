# remove-sample-config-advertise-meltano-yml — Archive Summary

## The request

The target-gcs loader shipped an unused `sample.config.json`. Configuration is supplied by Meltano via `meltano.yml` (and env vars). The feature asked to remove the sample config and update documentation so configuration is advertised only via `meltano.yml`, reducing confusion and aligning docs with actual usage. No new automated tests were required; validation was to confirm no remaining references to `sample.config.json` in live docs and that the README directs users to `meltano.yml` for configuration.

## Planned approach

**Chosen solution:** Remove the file and update all live documentation (Option 1). No new systems or code changes; artifact removal and doc updates only.

- **Delete:** `loaders/target-gcs/sample.config.json`.
- **Update:** (1) `loaders/target-gcs/README.md` — Configuration and Usage sections: state config via Meltano (`meltano.yml` + env), remove every reference to `sample.config.json`, point to in-repo `meltano.yml` for example structure; direct-run example use Meltano or generic config path. (2) `docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md` — Remove `sample.config.json` from the `loaders/target-gcs` directory tree. (3) `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` — Replace the "Running as part of a pipeline" CLI example that used `--config sample.config.json` with Meltano or generic config path; prefer Meltano.
- **Leave unchanged:** CHANGELOG.md and `_archive/` (historical references only).

**Task order:** (1) Delete sample config; (2)–(4) update README, AI_CONTEXT_REPOSITORY.md, AI_CONTEXT_target-gcs.md (doc tasks independent after 01). Verification: repo-wide grep for `sample.config.json` returns matches only in CHANGELOG and `_archive/`; README and AI context clearly direct users to `meltano.yml`.

## What was implemented

All four tasks were completed in order.

1. **01-delete-sample-config:** `loaders/target-gcs/sample.config.json` was removed from the repository.
2. **02-update-readme:** README Configuration section states that the target is configured via Meltano (`meltano.yml` + env) and points to `meltano.yml` in the directory for example structure; Usage/direct-run example uses Meltano and generic config path. No references to `sample.config.json` remain in the README.
3. **03-update-ai-context-repository:** The directory tree in `AI_CONTEXT_REPOSITORY.md` no longer lists `sample.config.json` under `loaders/target-gcs`.
4. **04-update-ai-context-target-gcs:** The "Running as part of a pipeline" example in `AI_CONTEXT_target-gcs.md` uses Meltano (and generic config path); it does not reference `sample.config.json`.

Outcome: Configuration is advertised solely via `meltano.yml` (and env). Live docs and target-gcs package contain no references to `sample.config.json`; remaining mentions are only in CHANGELOG and archived feature docs, as intended.
