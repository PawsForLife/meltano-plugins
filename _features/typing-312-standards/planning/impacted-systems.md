# Impacted systems: Python 3.12 typing standards

## Scope

Refactor only: no new behaviour. All impacted code is existing Python type hints and `typing` imports.

## Components

### Tap: restful-api-tap

| Module / path | Impact |
|---------------|--------|
| `restful_api_tap/auth.py` | `typing`: `Any` only — no replacement. |
| `restful_api_tap/client.py` | Replace `Optional[...]` with `... \| None`; keep `Any`, `Iterator`. |
| `restful_api_tap/pagination.py` | Replace `List[...]`, `Optional[...]`; keep `Any`, `cast`. |
| `restful_api_tap/streams.py` | Replace `Dict`, `List`, `Optional`, `Union` with built-ins and `\|`; keep `Any`, `Generator`, `Iterable`, `cast`. |
| `restful_api_tap/tap.py` | Replace `List[...]`, `Optional[...]`; keep `Any`. Uses `singer_sdk.typing as th` — unchanged. |
| `restful_api_tap/utils.py` | Replace `Optional[...]`; keep `Any`. |
| `tests/test_streams.py`, `tests/test_is_sorted.py` | `Any` only — minimal or no change. |

### Loader: target-gcs

| Module / path | Impact |
|---------------|--------|
| `target_gcs/target.py` | Uses `singer_sdk import typing as th` only — no change. |
| `target_gcs/sinks.py` | `typing`: `Any` only; already uses `Callable[[], float] \| None` style — no replacement. |
| `tests/test_core.py` | Keep `Any`, `cast`. |
| `tests/test_sinks.py`, `tests/test_partition_key_generation.py` | Use `Callable[...] \| None` — already 3.12-style; no change. |

### Scripts (repo root)

| Module / path | Impact |
|---------------|--------|
| `scripts/list_packages.py` | Uses `from __future__ import annotations`; review for any `typing` generics to convert. |
| `scripts/tests/test_list_packages.py` | Same as above. |

## Interfaces

- **Public function and method signatures**: Parameter and return type hints only; no runtime behaviour change.
- **No API or config changes**: Singer/Meltano tap and target interfaces unchanged.

## Summary

- **Heaviest impact**: `restful_api_tap/streams.py` and `restful_api_tap/pagination.py` (multiple `Optional`, `List`, `Dict`, `Union`).
- **Light impact**: `client.py`, `tap.py`, `utils.py` (mostly `Optional`).
- **No or minimal impact**: `auth.py`, target-gcs runtime code (already modern), scripts (already use `__future__` annotations).
