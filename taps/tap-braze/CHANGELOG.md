# Changelog

## [0.1.0] - 2026-09-29

### Added

- Initial `tap-braze` Singer tap for Braze campaign and canvas details.
  - `campaigns` and `canvases` full-table list parent streams (`/campaigns/list`,
    `/canvas/list`) with Braze 0-indexed page-number pagination. The lists request
    `include_archived=true` so archived campaigns/canvases reach their details
    call. Each page is loaded into a Pydantic envelope model that requires the
    records key and rejects a non-object row, so a missing key or malformed page
    is rejected rather than mistaken for an empty final page.
  - `campaign_details` and `canvas_details` full-table child streams
    (`/campaigns/details`, `/canvas/details`) that fan out one details request per
    parent id via the Singer SDK `parent_stream_type` + `get_child_context`
    mechanism. The details payload does not echo the id, so `campaign_id` /
    `canvas_id` is injected from the parent context as the primary key. Each
    payload is validated through a Pydantic model before it is emitted, so a
    malformed attribute is rejected rather than passed through.
  - Bearer authentication with a configurable REST base URL (`api_url`) and API
    key (`api_key`), and Retry-After backoff that honours both delta-seconds and
    HTTP-date values, consistent with the DNA-10408 Braze list config.
