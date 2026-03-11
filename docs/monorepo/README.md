# Using plugins from this monorepo

This repo is a **monorepo** of Meltano/Singer SDK plugins. These plugins are **custom** (not on the Meltano Hub or PyPI). You install them from GitHub using Meltano’s `pip_url` and the **subdirectory** fragment so each plugin is installed from its own package path.

## Purpose

Use the extractors (taps) and loaders (targets) in this repo (e.g. **restful-api-tap**, **target-gcs**) in your Meltano project. Because they are not on the Meltano Hub, add them by editing `meltano.yml` with `pip_url`, `#subdirectory=`, and `namespace`. Do **not** set `variant` on custom plugins (see [Troubleshooting](#troubleshooting)); do not add via `meltano add` from the Hub.

## Mechanism

- **pip_url**: Use a Git URL to this repo plus the `#subdirectory=<path>` fragment.
- Each plugin lives in its own directory with its own `pyproject.toml`; the subdirectory tells pip which package to install.

Examples below are taken from the [repo root README](../../README.md). For the canonical Installation section and directory layout, see that file.

## Concrete examples

### Extractor (restful-api-tap)

Add to `meltano.yml` (use `namespace`, omit `variant`; use plain `git+https://...` URL, not `package @ url`):

```yaml
plugins:
  extractors:
    - name: restful-api-tap
      namespace: restful_api_tap
      pip_url: git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=taps/restful-api-tap
```

### Loader (target-gcs)

Add to `meltano.yml`:

```yaml
plugins:
  loaders:
    - name: target-gcs
      namespace: target_gcs
      pip_url: git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=loaders/target-gcs
```

Then run `meltano install` and use pipelines such as `meltano run restful-api-tap target-gcs`.

### Troubleshooting

- **"Extractor/Loader 'X' is not known to Meltano"** — Do not set `variant` on custom plugin definitions. Meltano treats `variant` as Hub-only lookup; remove `variant` and set `namespace` so the project definition is used.
- **"Failed to parse: `@`"** — Use a plain `git+https://...` URL in `pip_url`, not the `package @ git+https://...` form (some installers reject it).

## Directory layout

Plugin locations in this repo (see [README](../../README.md) for the authoritative list):

| Path | Plugin |
|------|--------|
| `taps/restful-api-tap/` | **restful-api-tap** (REST API extractor) |
| `loaders/target-gcs/` | **target-gcs** (GCS loader) |

Each subdirectory is a standalone Python package with its own `pyproject.toml` and is installable via pip from that path.

## CI and plugin standards

CI discovers packages via `scripts/list_packages.py` (directories with a `pyproject.toml`) and runs a matrix job over them. Each plugin must have an `install.sh` that runs **uv**, install, **pytest**, **ruff**, and **mypy**. Tests must live in the package-root `tests/` directory. The workflow is in [.github/workflows/plugin-matrix.yml](../../.github/workflows/plugin-matrix.yml).

## Root-level tooling

The repository provides a root **install.sh** that discovers plugin directories via `scripts/list_packages.py` and runs each plugin's `install.sh`; it also installs pre-commit if missing and runs `pre-commit install`. Root **pre-commit** runs ruff, mypy (and optionally pytest) per plugin using that plugin's virtual environment; discovery uses the same `list_packages.py` as CI.

## Version pinning

To pin to a tag, branch, or commit, put the ref **before** the `#` in the URL:

```yaml
pip_url: git+https://github.com/PawsForLife/meltano-plugins.git@v1.0.0#subdirectory=taps/restful-api-tap
```

## References

- [Meltano — Plugin management (custom fork)](https://docs.meltano.com/guide/plugin-management/#using-a-custom-fork-of-a-plugin)
- [Meltano — Plugin definition syntax](https://docs.meltano.com/reference/plugin-definition-syntax/) — `name`, `variant`, `pip_url`
- [pip VCS support](https://pip.pypa.io/en/stable/topics/vcs-support/) — `subdirectory` and URL fragments
