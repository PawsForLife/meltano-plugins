# Possible solutions: Python 3.12 typing standards

## Options

### 1. Internal (stdlib / language) — **recommended**

Use Python 3.12 built-in generics (PEP 585) and union pipe syntax (PEP 604):

- **Replace**: `Union[X, Y]` → `X | Y`; `Optional[X]` → `X | None`; `Dict`, `List`, `Set`, `Tuple` → `dict`, `list`, `set`, `tuple`.
- **Keep**: `typing` symbols with no built-in equivalent: `Any`, `Callable`, `TypeVar`, `TypedDict`, `Protocol`, `Iterator`, `Generator`, `Iterable`, `cast`, etc.
- **Pros**: No dependencies; matches language and PEP standards; better readability; no version pin beyond 3.12.
- **Cons**: None for this codebase (already 3.12+).

### 2. External typing helper library

Use a third-party library (e.g. `typing_extensions`) to backport or normalize hints.

- **Pros**: Can support older Python if ever needed.
- **Cons**: Unnecessary for 3.12-only; adds dependency; feature explicitly states no external lib needed.

### 3. Hybrid (keep `typing` only where required)

Same as option 1, with explicit rule: remove all `typing` imports that become redundant; keep only `Any`, `Callable`, `Iterator`, `Generator`, `Iterable`, `cast`, and future use of `TypedDict`, `Protocol`, `TypeVar`.

- **Pros**: Minimal surface; clear convention.
- **Cons**: None.

## Recommendation

**Option 1 / 3 (internal, hybrid).** Use built-in types and pipe unions; keep `typing` only for symbols that have no built-in equivalent. No external library.
