# Task 05: Update documentation

## Background

All docs that reference the package name, module path, or mypy/install commands for target-gcs must use `target_gcs`, and the source-package naming rule must be stated in AI context. Depends on tasks 03 and 04 so code and tooling are final.

## This Task

**Plugin-local**

- `loaders/target-gcs/README.md`: "Python package is `gcs_target`" → "Python package is `target_gcs`"; `uv run mypy gcs_target` → `uv run mypy target_gcs`.
- `loaders/target-gcs/CHANGELOG.md`: Add entry for package/namespace rename from `gcs_target` to `target_gcs` (part of normalise-plugin-source-folders). Historical mentions of `gcs_target` may remain.

**Repository docs**

- `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md`: Commands table (mypy), entry point table, namespace, Frequently Used Imports, troubleshooting—all `gcs_target` → `target_gcs`.
- `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`: Paths `gcs_target/` → `target_gcs/`; module names `gcs_target.*` → `target_gcs.*`; entry point and package root `target_gcs`.
- `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md`: Source package naming rule (plugin dir with `-` → `_`); examples `restful_api_tap`, `target_gcs`; replace `gcs_target` with `target_gcs` where applicable.
- `docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md`: Directory structure and entry point table: `gcs_target` → `target_gcs`.
- `CHANGELOG.md` (repo root): Add migration note—target-gcs package/namespace `gcs_target` → `target_gcs`; update `meltano.yml` namespace and re-run `meltano install`; verification commands use `mypy target_gcs`.

**Acceptance**

- Grep for `gcs_target` across the repo: only CHANGELOG or explicit migration notes may retain it (no code, config, or active docs).

## Testing Needed

- **Validation only** (no new tests per plan): Grep for `gcs_target` and confirm no matches in code, config, or docs except intended historical/migration text. Doc files remain within project line limits (content_length rule).
