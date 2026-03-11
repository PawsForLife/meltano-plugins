# Master Plan — Documentation: Stream-level `is_sorted` config

**Feature:** restful-api-tap is_sorted stream config

---

## Documentation to Create or Update

### 1. Plugin definition (meltano.yml)

- **What:** The new `is_sorted` setting is self-explanatory from the name and `kind: boolean`. Optionally add a short comment or description in the plugin’s custom docs if the project maintains them; the plan does not require a change to meltano.yml beyond the new entry.
- **User-facing:** Meltano UI may show the setting name; documenting in README (see below) covers behaviour for users editing config by hand.

### 2. README (taps/restful-api-tap/README.md)

- **Update:** Add a short subsection (e.g. under stream configuration or incremental replication) describing:
  - **Option:** `is_sorted` (stream-level, boolean, default `False`).
  - **When to set:** When the source API returns records ordered by the replication key (e.g. `sequence_id`, `created_at`).
  - **Effect:** When `true`, the stream is declared sorted so that interrupted syncs are resumable (in-run resume); the source API must actually return records ordered by the replication key.
- **Placement:** Near other stream-level options (e.g. `replication_key`, `source_search_field`, `source_search_query`). Keep concise; link to SDK incremental replication docs if desired.

### 3. Code documentation (docstrings)

- **tap.py:** The new `th.Property("is_sorted", ...)` is self-documenting via `description`. No separate function docstring change required for `discover_streams()` if the existing docstring describes “builds DynamicStream from config”; optionally add one line: “Resolves stream-level `is_sorted` (default False) and passes to DynamicStream.”
- **streams.py:** In `DynamicStream.__init__`, add `is_sorted` to the `Args` section of the docstring (see [implementation.md](implementation.md)): purpose and default value. No new module-level docstring required.

---

## What Not to Document as Code

- Do not add comments that duplicate the SDK’s incremental replication docs; a single sentence that “when true, enables resumable state if the sync is interrupted” is sufficient.
- Do not update docs based on assumed behaviour; after implementation, ensure README and docstrings match the actual code (see [documentation.mdc](../../../.cursor/rules/documentation.mdc): “NEVER update code based on documentation; update documentation to reflect the code”).

---

## Summary

| Document           | Action |
|--------------------|--------|
| meltano.yml        | Add `is_sorted` setting; no extra prose required. |
| README.md          | Add stream-level `is_sorted` description (when to use, effect, default). |
| tap.py             | Property description suffices; optional one-line in discover_streams docstring. |
| streams.py         | Add `is_sorted` to `DynamicStream.__init__` Args in docstring. |
