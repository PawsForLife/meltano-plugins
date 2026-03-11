# New systems: `is_sorted` stream config

**Feature:** Stream-level `is_sorted` config for resumable incremental syncs  
**Plugin:** restful-api-tap

---

## Summary

This feature does **not** introduce new modules, packages, or external systems. It adds a single stream-level configuration option and wires it through existing tap and stream code so the Meltano Singer SDK’s existing resumability behaviour is honoured when the source API returns records ordered by the replication key.

---

## New configuration surface

- **Config key:** `is_sorted` (stream-level only).
- **Type:** Boolean; optional; default `False`.
- **Where:** In `config.streams[]` (and thus in Meltano project config under `config.streams[].is_sorted`).
- **Effect:** When `True`, the tap sets `stream.is_sorted = True` on the corresponding `DynamicStream` instance so the SDK treats the stream as sorted by the replication key and allows resumable state if a sync is interrupted.

No new environment variables, CLI arguments, or API endpoints are added.

---

## New code surface (minimal)

- **tap.py:** One new property in `common_properties`; one new variable and one new keyword argument in `discover_streams()`.
- **streams.py:** One new `__init__` parameter and one assignment (`self.is_sorted = is_sorted`).
- **meltano.yml:** One new stream-level setting entry.

No new files, classes, or functions are required.
