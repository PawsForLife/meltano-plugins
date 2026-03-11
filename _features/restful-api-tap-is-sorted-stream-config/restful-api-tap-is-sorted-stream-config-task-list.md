# Task list: restful-api-tap is_sorted stream config

**Feature:** restful-api-tap-is-sorted-stream-config
**Plan:** `_features/restful-api-tap-is-sorted-stream-config/plans/master/`
**Tasks:** `_features/restful-api-tap-is-sorted-stream-config/tasks/`

---

## Execution order

| # | Task file | Summary | Dependencies |
|---|-----------|---------|--------------|
| 1 | 01-add-is-sorted-tests.md | Add black-box tests for discovered stream `is_sorted` (true, omitted, false, multi-stream) | None |
| 2 | 02-add-is-sorted-plugin-schema.md | Add `is_sorted` (boolean) to meltano.yml plugin settings | None |
| 3 | 03-add-is-sorted-common-properties.md | Add `is_sorted` property to common_properties in tap.py | None |
| 4 | 04-add-is-sorted-to-dynamic-stream.md | Add `is_sorted` param and `self.is_sorted` to DynamicStream in streams.py | None |
| 5 | 05-wire-is-sorted-in-discover-streams.md | Resolve `is_sorted` in discover_streams() and pass to DynamicStream | 03, 04 |
| 6 | 06-update-is-sorted-documentation.md | Update README and optional docstrings for is_sorted | 01–05 |

---

## Interface requirements

- **Config:** Stream-level `is_sorted` (boolean, default False). Validated via SDK schema (common_properties).
- **Tap → Stream:** `discover_streams()` reads `stream.get("is_sorted", False)` and passes to `DynamicStream(..., is_sorted=is_sorted)`.
- **Stream:** `DynamicStream` exposes `self.is_sorted` for SDK resumability; no other modules depend on it directly.

---

## Development practices

- TDD: Tests (01) written first; they fail until 05 is done.
- Black-box: Assert on `stream.is_sorted` only; no log or call-count assertions.
- No new dependencies; no new modules. Touchpoints: meltano.yml, tap.py (common_properties + discover_streams), streams.py (DynamicStream).
