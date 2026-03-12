# Interfaces: Python 3.12 Typing Standards

## Scope of Interface Changes

Only **type annotations** on public and internal functions/methods and variables are updated. No changes to:

- Singer/Meltano interfaces (config file, state file, Catalog, stream definitions).
- CLI arguments or entry points.
- Method signatures (parameter names, default values, or return behaviour).
- Public API contracts of tap or target beyond the type hints themselves.

## Replacement Rules (Contract for Annotations)

| Old annotation           | New annotation   |
|--------------------------|------------------|
| `Union[X, Y]`            | `X \| Y`         |
| `Optional[X]`            | `X \| None`      |
| `Dict[K, V]`             | `dict[K, V]`      |
| `List[T]`                | `list[T]`        |
| `Set[T]`                 | `set[T]`         |
| `Tuple[A, B, ...]`       | `tuple[A, B, ...]` |

Apply in:

- Function and method parameter types.
- Return types.
- Local or class-level type annotations (e.g. instance attributes where used).

## Typing Symbols to Keep

Keep imports from `typing` (or use via `from typing import ...`) only for:

- **`Any`** — no built-in equivalent.
- **`Callable`** — e.g. `Callable[[], float]`, `Callable[..., None]`.
- **`Iterator`**, **`Generator`**, **`Iterable`** — used in tap client/streams.
- **`cast`** — for type-narrowing where needed.

Reserve for future use (do not remove if present; do not add unless needed): **`TypedDict`**, **`Protocol`**, **`TypeVar`**.

Do **not** use for type hints after refactor: `Union`, `Optional`, `Dict`, `List`, `Set`, `Tuple` (replace with built-ins and `|` as above).

## Singer SDK Typing

`singer_sdk.typing` (commonly imported as `th`) is used for **config and schema definitions** (e.g. `th.Property`, `th.StringType`, `th.ArrayType`). This is **unchanged**. The refactor applies to application code type hints (e.g. variables, function parameters, return types), not to SDK schema construction.

## `from __future__ import annotations`

- **Do not add** in tap or target code unless required for forward references or circular imports.
- **Scripts** that already use `from __future__ import annotations` (e.g. `scripts/list_packages.py`) keep it; ensure any remaining `typing` generics are still converted to built-ins and `|` for consistency.

## Interface Contracts and Expected Behaviour

- **Behaviour**: Identical before and after. Tests assert observable behaviour; type hints do not change it.
- **Config/state/Catalog**: No schema or key changes; no new required or optional keys.
- **Public entry points**: Same CLI commands and same call patterns; only type information in source code changes.

## Dependencies Between Interfaces

No new dependencies. Tap and target remain independent; scripts remain independent. Shared contract is only the consistent use of 3.12-style type hints across the codebase.
