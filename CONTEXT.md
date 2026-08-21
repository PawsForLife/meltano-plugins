# CONTEXT

Public Python monorepo of Meltano/Singer plugins. Default branch `main`, promoted to `release`.

## CI/CD — commit-message linting

Conventional Commits ([spec](https://www.conventionalcommits.org/en/v1.0.0/)) are enforced.
Reference: [Pet Circle commit-message linting](https://petcircle.atlassian.net/wiki/spaces/TEC/pages/2786427719).

- **CI** — `.github/workflows/commitlint.yaml` runs `wagoid/commitlint-github-action@v6`
  inline on `ubuntu-latest` for every PR (`if: github.base_ref == 'main'`), in relaxed
  mode (a generated `commitlint.config.mjs` extending `@commitlint/config-conventional`,
  `subject-case` downgraded to a warning; `strict` is not set). It is inlined rather than
  calling the org reusable workflow because this repo is **public**: it cannot read the
  private `pc-central-services`, and self-hosted runners on a public repo would expose
  internal infra to fork PRs — so it keeps `ubuntu-latest`.
  - Merge commits are ignored (config-conventional `defaultIgnores`), so
    `Merge branch 'main' into ...` commits pass.
  - `release` promotion PRs (`M2R`) are skipped by `github.base_ref == 'main'` and are
    deliberately not linted.
  - Not a required status check — branch protection is unchanged (out of scope).

- **Local** — `commit-msg` gitlint hook in `.pre-commit-config.yaml`
  (`jorisroovers/gitlint@v0.19.1`), config in `.gitlint` (title/body max 100 to match CI).
  - `install.sh` runs `pre-commit uninstall` then installs hooks explicitly, so
    `default_install_hook_types` alone is not honoured on onboarding. `install.sh` therefore
    installs both hook types: `pre-commit install --hook-type pre-push --hook-type commit-msg`.
  - The existing `plugin-checks` hook (ruff/mypy/pytest) is pinned to `stages: [pre-push]`
    so it does not fire on commit-msg.

- **PR titles** — merges use `PR_TITLE` (both squash and merge-commit), so the PR title
  becomes the permanent history subject. Convention: Conventional Commits with a trailing
  Jira key, e.g. `feat: add campaigns stream (DNA-9537)` (decision (b) from DNA-9910).
  A PR-title lint is not wired up (out of scope for this rollout).

## Notes / deferred

- `loaders/target-gcs/.pre-commit-config.yaml` is a second, nested pre-commit config
  (ruff only). pre-commit reads only the root config, so gitlint/`.gitlint` live at root;
  the nested config is untouched here.
