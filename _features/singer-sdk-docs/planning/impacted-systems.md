# Impacted systems — Singer SDK docs

## Summary

This feature adds documentation only. No application code, tests, or CI are modified.

## Impacted areas

| Area | Impact |
|------|--------|
| **Repository root** | New `docs/` directory at repo root. |
| **README.md** | Optional: add a short "Documentation" section linking to `docs/README.md` or `docs/index.md`. Not required for the feature; implementer may add if desired. |
| **Existing taps/loaders** | No changes. Docs reference the existing layout (`taps/restful-api-tap`, `loaders/gcs-loader`) and README Installation section. |

## Not impacted

- No changes to `taps/`, `loaders/`, `pyproject.toml`, or plugin code.
- No new dependencies or tooling.
- No CI or build changes (unless the project later adds doc build/link checks).
