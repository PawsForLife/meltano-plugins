# Possible Solutions — split-path-filename

## Summary

The feature is an internal refactor: move from config-driven key templates to fixed constants. Research focused on whether external libraries can provide path/filename template expansion or Hive partitioning.

---

## Option 1: Internal Solution (str.format)

**Approach:** Use Python `str.format()` with path and filename constants. Path templates use `{stream}`, `{date}`, `{hive_path}`; filename uses `{timestamp}`.

**Pros:**
- No new dependencies.
- Simple, explicit, matches current pattern.
- Full control over token semantics.
- Aligns with feature spec (constants in `constants.py`).

**Cons:**
- None for this scope.

---

## Option 2: google.api_core.path_template

**Source:** [google-api-core path_template](https://googleapis.dev/python/google-api-core/latest/_modules/google/api_core/path_template.html)

**Approach:** Use `PathTemplate.expand()` for API-style path templates.

**Pros:**
- Google-maintained; matches GCS ecosystem.
- Supports `*` and `**` wildcards.

**Cons:**
- Designed for API URLs (e.g. `/resource/{id}/sub/{name}`), not GCS object keys.
- Template syntax differs from our `{stream}/{date}/{timestamp}.jsonl`; would require mapping.
- Adds dependency on `google-api-core` (or `google-cloud-storage`).
- Overkill for simple string substitution.

**Verdict:** Not suitable for this use case.

---

## Option 3: PyArrow HivePartitioning

**Source:** [pyarrow.dataset.HivePartitioning](https://arrow.apache.org/docs/8.0/python/generated/pyarrow.dataset.HivePartitioning.html)

**Approach:** Use PyArrow to discover and parse Hive-style directory structures.

**Pros:**
- Standard for reading partitioned datasets.

**Cons:**
- **Parsing only:** Builds partition info from existing paths; does not generate paths.
- We need path generation; PyArrow is for consumption.
- Adds heavy dependency (PyArrow).

**Verdict:** Not applicable.

---

## Option 4: Jinja2 / Custom Templating

**Approach:** Use Jinja2 or similar for path/filename templates.

**Pros:**
- Flexible template syntax.

**Cons:**
- Adds dependency.
- Overkill for simple `{token}` substitution.
- Feature spec requires constants.

**Verdict:** Not recommended.

---

## Recommendation

**Internal solution (Option 1)** is the preferred approach. The feature is a refactor to constants; `str.format()` is sufficient and keeps the codebase simple.
