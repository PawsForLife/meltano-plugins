# Dependencies: Python 3.12 Typing Standards

## External Dependencies

**None.** This feature uses only the Python 3.12 standard library and existing project dependencies. No new packages or version changes are required.

- **typing** (stdlib): Still used for `Any`, `Callable`, `Iterator`, `Generator`, `Iterable`, `cast`. No new third-party typing helpers (e.g. `typing_extensions`).
- **singer-sdk**: Unchanged; continues to provide `singer_sdk.typing` for config/schema definitions. Application code type hints are independent of SDK typing.

## Internal Dependencies

- **restful-api-tap**: No dependency on target-gcs or scripts. Refactor can be done and tested in isolation.
- **target-gcs**: No dependency on tap or scripts. Refactor can be done after tap.
- **scripts**: No dependency on tap or target. Refactor can be done last.
- No shared library; each plugin has its own `pyproject.toml` and test suite.

## System Requirements

- **Python**: ≥3.12 (already required by both plugins). Built-in generics and `X | Y` union syntax are native in 3.10+; 3.12 is the project minimum.
- **Tooling**: Existing Ruff and mypy configuration per plugin (and scripts if applicable). No new tools required.

## Environment Setup

- Use existing setup: virtual environment per plugin (e.g. `uv venv`, `uv sync`), activate then run tests and type check. See `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md` for commands.
- No new env vars or config; no changes to config file, state file, or Catalog for Singer/Meltano (see `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md`).

## Configuration Requirements

- **Tap/target**: No changes to `meltano.yml`, `config.sample.json`, or config schema. Type hints are source-code only.
- **Ruff**: Enable 3.12 typing rules in each plugin (and root/scripts if applicable): UP006 (PEP 585 built-in generics), UP007 (PEP 604 union), UP045 (Optional → X | None). restful-api-tap currently does not enable UP; add these. target-gcs already has `"UP"` in select.
- **mypy**: Use `python_version = "3.12"` everywhere (tap has both pyproject.toml and mypy.ini — align both). Mypy does not have style-only options for pipe unions; Ruff enforces the style.
- **CI**: CI that runs ruff and mypy will enforce the new rules after config and code changes. No new CI jobs required.
