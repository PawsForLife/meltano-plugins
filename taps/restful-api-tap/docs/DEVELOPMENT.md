# restful-api-tap — Developer guide

Local setup, testing, and contribution for the restful-api-tap Singer tap (Meltano extractor).

## Initialize your development environment

Run the install script (runs pytest, ruff, and mypy; CI uses it for testing):

```bash
./install.sh
```

Or manually with [uv](https://docs.astral.sh/uv/):

```bash
uv venv
. .venv/bin/activate
uv sync --extra dev
```

## Create and run tests

Create tests within the `tests/` directory, then run:

```bash
uv run pytest
```

You can also test the `restful-api-tap` CLI directly:

```bash
uv run restful-api-tap --help
```

## Lint and type check

Use ruff and mypy per repo conventions (e.g. `uv run ruff check .`, `uv run ruff format .`, `uv run mypy restful_api_tap`). CI runs these via `./install.sh` or the repo root check scripts.

## Continuous Integration

`./install.sh` runs pytest, ruff, and mypy directly. CI relies on it for testing; run it locally to match CI. Optionally run `uv run tox -e py` for local use.

## Testing with Meltano

_This tap works in any Singer environment and does not require Meltano. The following is for convenience and end-to-end orchestration._

This project comes with an example `meltano.yml` project file. Install Meltano and plugins:

```bash
# Install Meltano (e.g. with uv)
uv tool install meltano
# From this directory, initialize
cd taps/restful-api-tap
meltano install
```

Test and orchestrate:

```bash
# Test invocation:
meltano invoke restful-api-tap --version
# OR run a test ELT pipeline:
meltano elt restful-api-tap target-jsonl
```

To test from another Meltano project, add this extractor with `pip_url` and `#subdirectory=taps/restful-api-tap` in `meltano.yml`, then run `meltano run restful-api-tap <target>`.

## SDK and references

- [Meltano Singer SDK — Dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for building Singer taps and targets.
