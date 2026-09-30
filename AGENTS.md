# meltano-plugins — agent instructions

Public monorepo of Pet Circle's custom Meltano/Singer plugins (`taps/restful-api-tap`,
`taps/tap-talon-one`, `loaders/target-gcs`), each a standalone uv package. Before your first
change, read [CONTEXT.md](CONTEXT.md) and [README.md](README.md).

## Commands
- Setup: `./install.sh` from the root (creates each plugin's `.venv`, runs its checks, installs hooks)
- Test one plugin: `uv run pytest` from its directory; all plugins: `scripts/run_plugin_checks.sh`
  (ruff, ruff format, mypy, pytest per plugin, as CI's `plugin-unit-tests.yml` does)
- Script tests: `uv run --no-project --with pytest pytest scripts/tests -q`
- Hooks: `pre-commit install` (the Claude `SessionStart` hook does this for you). The `pre-push`
  hook runs plugin checks when `taps/` or `loaders/` change and script tests when `scripts/`
  changes; a docs-only push runs neither.

## Deploy
No service. Consumers install via `pip_url: git+https://...#subdirectory=<plugin>`. A `main` →
`release` PR (titled `M2R`) tags `<plugin>/v<version>` for each plugin whose
`pyproject.toml` version changed.

## Conventions
- Commits and PR titles: Conventional Commits with a trailing key, e.g.
  `feat(tap-talon-one): add campaigns stream (DNA-9537)`. Checked by the gitlint `commit-msg`
  hook and CI `commitlint.yaml`. Merges use the PR title, so it lands in history. Never `--no-verify`.
- Changelogs: plugin-only changes go in that plugin's `CHANGELOG.md`; root tooling, CI and docs
  go in the root `CHANGELOG.md` under `## YYYY-MM-DD` (see `.cursor/CONVENTIONS.md`).

## Gotchas
- The repo is public: never commit credentials or real config values.
- The `pre-push` plugin checks use each plugin's `.venv`; in a fresh worktree run `./install.sh`
  (or each plugin's `install.sh`) first, or the push fails with `Missing .venv`.
- `loaders/target-gcs/.pre-commit-config.yaml` is nested and ignored by pre-commit; the root
  config is the one that runs.

## Maintaining this file
Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
