# Implementation: Python 3.12 Typing Standards

## Implementation Order

1. **Configure Ruff (and mypy) for 3.12 style** — enable rules so CI and pre-commit enforce the style going forward.
2. **Tap (restful-api-tap)** — highest impact; run tests and mypy after tap changes.
3. **Loader (target-gcs)** — lower impact; run tests and mypy after target changes.
4. **Repo-root scripts** — run script tests after script changes.

No new models or interfaces are introduced; changes are in-place edits to type hints and imports plus tool config. TDD still applies where new tests would be added (e.g. type-checker compliance); for this refactor, existing tests validate no behaviour change.

## Step-by-Step Implementation

### Phase 0: Ruff and mypy configuration

1. **restful-api-tap** (`taps/restful-api-tap/pyproject.toml`)
   - In `[tool.ruff.lint]`, add to `select` the pyupgrade rules for 3.12 typing: **UP006** (non-pep585-annotation: use `list`, `dict`, etc. instead of `typing.List`, `typing.Dict`), **UP007** (non-pep604-annotation-union: use `X | Y`), **UP045** (non-pep604-annotation-optional: use `X | None`). Either add the full `"UP"` group or extend with `extend-select = ["UP006", "UP007", "UP045"]` so only these are added.
   - Ensure `target-version = "py312"` is set (already present).
   - Mypy: ensure `python_version = "3.12"` in `[tool.mypy]` (pyproject.toml); the tap also has `mypy.ini` — align `python_version` to 3.12 there if it is still 3.9.
2. **target-gcs** (`loaders/target-gcs/pyproject.toml`)
   - Lint `select` already includes `"UP"`; verify that UP006, UP007, UP045 are in the effective rule set (they are part of UP). If the project uses a subset of UP, add UP006, UP007, UP045 explicitly.
   - Ensure `target-version = "py312"` and mypy `python_version = "3.12"` (already present).
3. **Repo root** (if scripts have their own ruff/mypy config)
   - If `scripts/` or root has a ruff config, add the same UP rules and py312 target so script code is held to the same standard.
4. Run ruff and mypy after config changes to establish baseline; fix any violations introduced by turning on the new rules (or do so during the refactor phases).

### Phase 1: restful-api-tap

1. **streams.py** (`taps/restful-api-tap/restful_api_tap/streams.py`)
   - Replace `Dict`, `List`, `Optional`, `Union` with `dict`, `list`, `X | None`, `X | Y`.
   - Keep `Any`, `Generator`, `Iterable`, `cast` from `typing`.
   - Remove unused `typing` imports (e.g. `Union`, `Optional`, `Dict`, `List`).
   - Run: `uv run ruff check .` and `uv run mypy restful_api_tap` from `taps/restful-api-tap/`.

2. **pagination.py** (`taps/restful-api-tap/restful_api_tap/pagination.py`)
   - Replace `List[...]`, `Optional[...]` with `list[...]`, `... | None`.
   - Keep `Any`, `cast`.
   - Remove unused `typing` imports.
   - Re-run ruff and mypy.

3. **client.py** (`taps/restful-api-tap/restful_api_tap/client.py`)
   - Replace `Optional[...]` with `... | None`.
   - Keep `Any`, `Iterator`.
   - Clean imports; re-run ruff and mypy.

4. **tap.py** (`taps/restful-api-tap/restful_api_tap/tap.py`)
   - Replace `List[...]`, `Optional[...]` with `list[...]`, `... | None`.
   - Keep `Any`; leave `singer_sdk.typing as th` unchanged.
   - Clean imports; re-run ruff and mypy.

5. **utils.py** (`taps/restful-api-tap/restful_api_tap/utils.py`)
   - Replace `Optional[...]` with `... | None`; keep `Any`.
   - Clean imports; re-run ruff and mypy.

6. **auth.py**
   - No change (only `Any` from typing).

7. **Tap tests** (`taps/restful-api-tap/tests/`)
   - In `test_streams.py`, `test_is_sorted.py`, and any other test files that use `Optional`/`Union`/`Dict`/`List` in annotations, apply the same replacement rules.
   - Run full test suite: `uv run pytest` from `taps/restful-api-tap/`.

### Phase 2: target-gcs

1. **target.py** — No change (uses only `singer_sdk.typing as th`).
2. **sinks.py** — No change (only `Any`; already uses `Callable[...] | None`).
3. **Tests** (`loaders/target-gcs/tests/`)
   - In `test_core.py` (and any other test file with old-style hints), ensure only `Any`, `cast` (or other kept symbols) are used; convert any `Optional`/`Union`/generic usage to 3.12 style.
   - Run: `uv run pytest`, `uv run ruff check .`, `uv run mypy target_gcs` from `loaders/target-gcs/`.

### Phase 3: Repo-root scripts

1. **scripts/list_packages.py**
   - Already uses `from __future__ import annotations`; replace any `typing.Dict`/`List`/`Optional`/`Union` with built-ins and `|`.
   - Run script tests from repo root (or as defined in CI).
2. **scripts/tests/test_list_packages.py**
   - Same replacement rules for type hints in tests.
   - Re-run script test suite.

## Files to Modify (Summary)

| Path | Actions |
|------|--------|
| `taps/restful-api-tap/pyproject.toml` | Add Ruff UP006, UP007, UP045 (or UP group); ensure py312 + mypy 3.12 |
| `taps/restful-api-tap/mypy.ini` | Set `python_version = 3.12` if currently 3.9 |
| `loaders/target-gcs/pyproject.toml` | Confirm UP rules include UP006/UP007/UP045; py312 already set |
| (root/scripts ruff config if any) | Add same UP rules and py312 for scripts |
| `taps/restful-api-tap/restful_api_tap/streams.py` | Dict/List/Optional/Union → built-ins and \| ; keep Any, Generator, Iterable, cast |
| `taps/restful-api-tap/restful_api_tap/pagination.py` | List/Optional → list, \| None ; keep Any, cast |
| `taps/restful-api-tap/restful_api_tap/client.py` | Optional → \| None ; keep Any, Iterator |
| `taps/restful-api-tap/restful_api_tap/tap.py` | List/Optional → list, \| None ; keep Any |
| `taps/restful-api-tap/restful_api_tap/utils.py` | Optional → \| None ; keep Any |
| `taps/restful-api-tap/tests/*.py` | Same rules where type hints exist |
| `loaders/target-gcs/tests/test_core.py` (and others if needed) | Any Optional/Union/generics → 3.12 style |
| `scripts/list_packages.py` | typing generics → built-ins and \| |
| `scripts/tests/test_list_packages.py` | Same |

## Code Organization and Structure

- No new files or modules.
- No change to package layout or public API surface; only annotation text and imports change.
- Preserve existing style (e.g. Ruff formatting); run `ruff format` after edits if the project uses it.

## Dependency Injection and Non-Determinism

No change. This refactor does not alter dependency injection or use of time/date/external clients; type hints only.

## Implementation Dependencies and Order

- Tap can be done first and verified in isolation.
- Target has no code dependency on tap; can be done second.
- Scripts are independent; can be done last.
- Within tap: `streams.py` and `pagination.py` have the most edits; order within the tap is flexible (e.g. streams then pagination then client, tap, utils, then tests).
