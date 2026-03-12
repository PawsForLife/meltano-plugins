# Selected solution: Python 3.12 typing standards

## Approach

Internal refactor using **Python 3.12 language/stdlib only**. No new dependencies.

## Replacements

| Old | New |
|-----|-----|
| `Union[X, Y]` | `X \| Y` |
| `Optional[X]` | `X \| None` |
| `Dict[K, V]` | `dict[K, V]` |
| `List[T]` | `list[T]` |
| `Set[T]` | `set[T]` |
| `Tuple[...]` | `tuple[...]` |

Apply consistently across taps, loaders, shared libs, and tests.

## Typing symbols to keep

Keep `typing` imports only for:

- **`Any`** — no built-in equivalent.
- **`Callable`** — e.g. `Callable[[], float]` (used in target-gcs).
- **`Iterator`, `Generator`, `Iterable`** — used in tap client/streams.
- **`cast`** — for type-narrowing where needed.
- **Reserve for future use**: `TypedDict`, `Protocol`, `TypeVar` (not currently used).

Do **not** keep: `Union`, `Optional`, `Dict`, `List`, `Set`, `Tuple` for type hints; use built-ins and `|` instead.

## `from __future__ import annotations`

- **Not required** for 3.12 in normal type hints (built-ins and `|` work at runtime in 3.10+).
- Add only if forward references or circular refs need deferred evaluation (e.g. scripts already using it in this repo).

## Ruff and mypy configuration

- **Ruff**: Enable pyupgrade rules so 3.12 style is required: **UP006** (PEP 585: use `list`, `dict`, etc.), **UP007** (PEP 604: use `X | Y`), **UP045** (use `X | None`). Add to `select` or `extend-select` in each plugin’s `pyproject.toml` (restful-api-tap currently has no UP rules; target-gcs already has `"UP"`).
- **mypy**: Set `python_version = "3.12"` everywhere (tap has both `pyproject.toml` and `mypy.ini` — align mypy.ini if it still says 3.9). Mypy does not enforce pipe-union vs `Union` style; Ruff is the style gate.

## Validation

- Existing test suite must pass (no behaviour change).
- Ruff and mypy must pass after config and code changes; Ruff will flag any remaining old-style hints.
