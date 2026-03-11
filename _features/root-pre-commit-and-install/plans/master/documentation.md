# Documentation — root-pre-commit-and-install

## Documentation to Create

- None. All deliverables are code and updates to existing docs.

## Documentation to Update

### README.md (repository root)

- Add a short **Development** or **Contributing** section (or subsection under existing Contributing).
- Content: To bootstrap all plugins and git hooks, run `./install.sh` from the repository root. Root install.sh runs each plugin's install.sh, then installs pre-commit if not present and runs `pre-commit install`. To check all files without committing, run `pre-commit run --all-files`. Ensure root `./install.sh` has been run at least once so each plugin has a `.venv`.

### docs/monorepo/README.md

- State that the repository provides a root **install.sh**: it discovers plugin directories via `scripts/list_packages.py` and runs each plugin’s `install.sh`. Add that root **pre-commit** runs ruff, mypy (and optionally pytest) per plugin using that plugin’s virtual environment; discovery uses the same `list_packages.py` as CI.

### docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md

- Add **root-level commands** (or a “Repo root” subsection): root `./install.sh` (bootstrap all plugins), `pre-commit install` (install git hooks), `pre-commit run --all-files` (run all hooks on all files). Keep existing per-plugin command tables (e.g. for `taps/restful-api-tap/`, `loaders/target-gcs/`) for single-plugin workflows. Update any “No repo-wide install.sh” wording to reflect that root install.sh now exists.

## Code Documentation

- **install.sh**: Short comment at top stating purpose (bootstrap all plugins by running each plugin’s install.sh; discovery via list_packages.py; then install pre-commit if missing and run pre-commit install).
- **scripts/run_plugin_checks.sh**: Short comment at top stating purpose (run ruff and mypy per plugin using each plugin’s venv; discovery via list_packages.py; optional pytest). Inline comments for package-name mapping if non-obvious.
- **.pre-commit-config.yaml**: No mandatory comments; structure is self-explanatory. Optional one-line comment that hook runs plugin checks via wrapper script.

## User-Facing Documentation

- README and docs/monorepo are the user-facing entries for contributors. QUICK_REFERENCE is for both humans and AI context; keep concise.

## Developer Documentation

- Implementation plan (this set of documents) and planning docs in `_features/root-pre-commit-and-install/planning/` serve as developer reference. No separate “developer guide” required for this feature.
