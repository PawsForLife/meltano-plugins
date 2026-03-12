# Architecture: Python 3.12 Typing Standards

## System Design and Structure

This feature does not change system architecture. It updates **type annotations** only within existing modules. Component boundaries, data flow, and entry points (tap CLI, target CLI, scripts) remain unchanged. The following describes how the refactor fits into the current structure.

## Component Breakdown and Responsibilities

### restful-api-tap (`taps/restful-api-tap/`)

| Component        | Role in refactor |
|-----------------|------------------|
| `restful_api_tap/streams.py`   | Replace `Dict`, `List`, `Optional`, `Union` with built-ins and `\|`; keep `Any`, `Generator`, `Iterable`, `cast`. |
| `restful_api_tap/pagination.py`| Replace `List[...]`, `Optional[...]`; keep `Any`, `cast`. |
| `restful_api_tap/client.py`   | Replace `Optional[...]` with `... \| None`; keep `Any`, `Iterator`. |
| `restful_api_tap/tap.py`      | Replace `List[...]`, `Optional[...]`; keep `Any`. Leave `singer_sdk.typing as th` unchanged. |
| `restful_api_tap/utils.py`    | Replace `Optional[...]`; keep `Any`. |
| `restful_api_tap/auth.py`     | `typing`: `Any` only — no replacement. |
| `tests/*.py`                  | Minimal or no change where only `Any` is used; update any `Optional`/`Union`/generic usage to 3.12 style. |

### target-gcs (`loaders/target-gcs/`)

| Component        | Role in refactor |
|-----------------|------------------|
| `target_gcs/target.py`  | Uses `singer_sdk.typing as th` only — no change. |
| `target_gcs/sinks.py`   | `typing`: `Any` only; already uses `Callable[[], float] \| None` — no replacement. |
| `tests/test_core.py`    | Keep `Any`, `cast`; ensure no old-style generics. |
| `tests/test_sinks.py`, `tests/test_partition_key_generation.py` | Already 3.12-style; confirm no regressions. |

### Scripts (repo root)

| Component        | Role in refactor |
|-----------------|------------------|
| `scripts/list_packages.py` | Uses `from __future__ import annotations`; convert any `typing` generics to built-ins and `\|`. |
| `scripts/tests/test_list_packages.py` | Same as above. |

## Data Flow and Interactions

Unchanged. Tap reads config and optional state/Catalog; emits Singer JSONL to stdout. Target reads Singer JSONL from stdin; writes to GCS. Scripts run independently. Type hints affect only static analysis and readability; no runtime data flow changes.

## Design Patterns and Principles

- **Consistency**: Apply the same replacement rules in every affected file (see [selected-solution](../../planning/selected-solution.md)).
- **Minimal surface**: Remove redundant `typing` imports; keep only `Any`, `Callable`, `Iterator`, `Generator`, `Iterable`, `cast` (and reserve `TypedDict`, `Protocol`, `TypeVar`).
- **No new patterns**: Follow existing project patterns (see `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md`): parameters and return types remain annotated; validation and behaviour are unchanged.
- **Refactor order**: Tap first (highest impact), then target, then root scripts, to allow incremental validation and to avoid merge conflicts.

## References

- Planning: [impacted-systems.md](../../planning/impacted-systems.md), [selected-solution.md](../../planning/selected-solution.md).
- Project: [AI_CONTEXT_REPOSITORY.md](../../../../docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md), [AI_CONTEXT_PATTERNS.md](../../../../docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md).
