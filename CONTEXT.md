# CONTEXT

Public Python monorepo of Meltano/Singer plugins. Default branch `main`, promoted to `release`.

## CI/CD — commit-message linting

Conventional Commits ([spec](https://www.conventionalcommits.org/en/v1.0.0/)) are checked,
advisory for now. Reference: [Pet Circle commit-message linting](https://petcircle.atlassian.net/wiki/spaces/TEC/pages/2786427719).

- **CI** — `.github/workflows/commitlint.yaml` runs `wagoid/commitlint-github-action@v6`
  inline on `ubuntu-latest` for PRs into `main`, with the same relaxed rules as the data
  team's `PawsForLife/puggle` `commitlint-variant.yaml`. It mirrors that workflow inline
  because this repo is **public** and cannot call the private puggle workflow. The step is
  `continue-on-error: true`, so lint errors do not fail the check yet.
  - Merge commits are ignored (config-conventional `defaultIgnores`), so
    `Merge branch 'main' into ...` commits pass.
  - `release` promotion PRs (`M2R`) are skipped by the `branches: [main]` trigger and are
    deliberately not linted.
  - Not a required status check — branch protection is unchanged (out of scope).

- **Local** — `commit-msg` gitlint hook in `.pre-commit-config.yaml`
  (`jorisroovers/gitlint@v0.19.1`), config in `.gitlint` (title/body max 100 to match CI).
  - `install.sh` runs `pre-commit uninstall` then installs hooks explicitly, so
    `default_install_hook_types` alone is not honoured on onboarding. `install.sh` therefore
    installs both hook types: `pre-commit install --hook-type pre-push --hook-type commit-msg`.
  - `default_install_hook_types: [commit-msg, pre-push]`, so a plain `pre-commit install`
    also installs both. The Claude `SessionStart` hook in `.claude/settings.json` runs it for
    every agent session, and its `permissions` block allowlists routine git, test and lint commands.
  - `pre-push` runs `plugin-checks` (ruff/mypy/pytest per plugin, `scripts/run_plugin_checks.sh`)
    when `taps/` or `loaders/` change, and `script-tests` (`pytest scripts/tests`) when
    `scripts/` changes. A push touching neither runs no tests.

- **PR titles** — merges use `PR_TITLE` (both squash and merge-commit), so the PR title
  becomes the permanent history subject. Convention: Conventional Commits with a trailing
  Jira key, e.g. `feat: add campaigns stream (DNA-9537)` (decision (b) from DNA-9910).
  A PR-title lint is not wired up (out of scope for this rollout).

## Notes / deferred

- `loaders/target-gcs/.pre-commit-config.yaml` is a second, nested pre-commit config
  (ruff only). pre-commit reads only the root config, so gitlint/`.gitlint` live at root;
  the nested config is untouched here.
