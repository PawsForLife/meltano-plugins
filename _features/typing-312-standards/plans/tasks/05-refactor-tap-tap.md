# Task Plan: 05-refactor-tap-tap

## Overview

This task refactors `restful_api_tap/tap.py` to Python 3.12 typing conventions within the typing-312-standards feature. The file defines `RestfulApiTap`, its config schema (`th`), `discover_streams`, and `get_schema`. All `List[...]` and `Optional[...]` annotations are replaced with `list[...]` and `... | None`; `typing` imports are reduced to `Any` only. Usage of `singer_sdk.typing as th` is unchanged. No behaviour or public API changes; Ruff (UP006, UP045) and mypy enforce style and type correctness after Task 01 configuration.

## Files to Create/Modify

| File | Action |
|------|--------|
| `taps/restful-api-tap/restful_api_tap/tap.py` | Modify |

**Changes in `tap.py`:**

- **Imports:** Replace `from typing import Any, List, Optional` with `from typing import Any`. Remove `List` and `Optional`.
- **Class attribute:** Change `_authenticator: Optional[APIAuthenticatorBase] = None` to `_authenticator: APIAuthenticatorBase | None = None`.
- **Method return type:** Change `discover_streams(self) -> List[DynamicStream]` to `discover_streams(self) -> list[DynamicStream]` (retain existing `# type: ignore` if present for SDK compatibility).
- **Leave unchanged:** All `th.*` usage (e.g. `th.PropertiesList`, `th.Property`, `th.StringType`); `get_schema` parameters that already use built-in `list`, `dict` in the signature.
- No new files. No changes to other modules.

## Test Strategy

- **No new test files or test cases.** This is a refactor-only change; existing tests remain the behavioural specification.
- **TDD:** Not applicable for new behaviour; existing tests are run before and after edits to guard against regressions.
- **Order:** Run the tap test suite from `taps/restful-api-tap/` before making changes to establish a passing baseline; after edits, re-run pytest to confirm no regressions.
- **Static checks:** Ruff (with UP006, UP007, UP045 from Task 01) and mypy act as the typing-style and type-correctness gate. Fix any new violations introduced by the refactor (e.g. unused `List`/`Optional` imports removed; annotations must remain valid).

## Implementation Order

1. From `taps/restful-api-tap/`, run `uv run pytest`, `uv run ruff check .`, and `uv run mypy restful_api_tap` to confirm a clean baseline (Task 01 must be complete so UP006/UP045 are enabled).
2. In `restful_api_tap/tap.py`:
   - Update the `typing` import: remove `List` and `Optional`; keep `Any`.
   - Replace `_authenticator: Optional[APIAuthenticatorBase] = None` with `_authenticator: APIAuthenticatorBase | None = None`.
   - Replace `def discover_streams(self) -> List[DynamicStream]:` with `def discover_streams(self) -> list[DynamicStream]:` (preserve any `# type: ignore` comment on that line if present).
3. Run `uv run ruff check .` and `uv run ruff format .` (if the project uses format); fix any issues.
4. Run `uv run mypy restful_api_tap`; fix any type errors.
5. Run `uv run pytest`; all tests must pass (no regressions).

## Validation Steps

1. **Ruff:** From `taps/restful-api-tap/`, `uv run ruff check .` exits 0 with no violations in `restful_api_tap/tap.py` (no `List`, `Optional`, or old-style generics).
2. **mypy:** From `taps/restful-api-tap/`, `uv run mypy restful_api_tap` exits 0 with no type errors.
3. **Tests:** From `taps/restful-api-tap/`, `uv run pytest` passes in full; no failing tests unless explicitly marked as expected failure.
4. **Inspection:** Open `tap.py` and confirm only `Any` is imported from `typing`; all former `Optional[...]` and `List[...]` usages are `... | None` and `list[...]`; `th` (singer_sdk.typing) is unchanged.

## Documentation Updates

- **No doc or README changes** are required for this task. Type hints are internal to the module; public behaviour and config contracts are unchanged.
- If the project's AI context or conventions doc explicitly describe typing in `tap.py`, they can be updated in a later pass to state that the tap uses 3.12-style hints; this task does not mandate that change.
