# target-gcs — Developer guide

Local setup, testing, and contribution for the target-gcs Singer target (Meltano loader).

## Requirements

- **Python 3.12+**
- **uv** for dependency management; lockfile is `uv.lock`
- **Ruff** and **mypy** for linting, formatting, and type checking

## Initialize your development environment

**Option A (recommended):** Run the install script to ensure uv is available, create a clean virtual environment, install dependencies (including dev), and run pytest, ruff, and mypy:

```bash
./install.sh
```

**Option B:** Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and then:

```bash
uv sync --extra dev
```

## Lint, format, and type check

```bash
uv run ruff check .
uv run ruff format .          # format in place; CI runs ruff format --check
uv run mypy target_gcs
```

## Create and run tests

Create tests in the package-root `tests/` directory. Test layout follows repo conventions: tests live under `tests/unit/` mirroring the source path (see `.cursor/rules/development_practices.mdc` or repo CONVENTIONS). Then run:

```bash
uv run pytest
```

You can also run the `target-gcs` CLI directly:

```bash
uv run target-gcs --help
```

## Testing with Meltano

_This target works in any Singer environment and does not require Meltano. The following is for convenience and end-to-end orchestration._

Your project comes with a custom `meltano.yml` project file. Open it and follow any _TODO_ items. Then install Meltano (if needed) and plugins:

```bash
# Install Meltano with uv (if needed)
uv tool install meltano
# From this directory, install plugins
cd loaders/target-gcs
meltano install
```

Test and orchestrate:

```bash
# Test invocation:
meltano invoke target-gcs --version
# OR run a test ELT pipeline with the Carbon Intensity sample tap:
meltano elt tap-carbon-intensity target-gcs
```

To test from another Meltano project, add this loader with `pip_url` and `#subdirectory=loaders/target-gcs` in `meltano.yml`, then run `meltano run <tap> target-gcs`.

## CI

Lint, type-check, and tests run in CI (e.g. via the repo root install/check scripts or GitHub Actions). Run `./install.sh` or `pre-commit run --all-files` from the repo root to match CI locally.

## SDK and references

- [Meltano Target SDK / Singer SDK — Dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for building Singer taps and targets.
