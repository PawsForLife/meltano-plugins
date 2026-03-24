# fix-medallia-duplicate-pagination-token

## Summary

Medallia `tap-medallia-sequence-id` failed with `RuntimeError: Loop detected in pagination` when the API returned the same last `sequence_id` on consecutive pages (cursor did not advance). The Meltano Singer SDK treats identical consecutive JSONPath tokens as an infinite loop.

## Change

- **restful-api-tap v1.7.1** — New config `pagination_stop_on_duplicate_token` (default `false`). When `true`, uses `DuplicateTokenStopsJSONPathPaginator` for `jsonpath_paginator` / `default` (and `simple_header_paginator` when a JSONPath token path is set), ending pagination instead of raising.
- Tests: unit tests for the paginator and mocked two-page tap sync (with and without the flag).
- Docs: README pagination section; `meltano.yml` setting; plugin `CHANGELOG.md`.

## Consumer action

In the Medallia Meltano project, set on `tap-medallia-sequence-id` config:

```yaml
pagination_stop_on_duplicate_token: true
```

Point `pip_url` at `restful-api-tap/v1.7.1` (or newer) after release.

## References

- Investigation: `_bugs/medallia-duplicate-pagination-token/` (removed after archive; this file is the handoff).
