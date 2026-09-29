# Changelog

## [0.1.0] - 2026-09-29

### Added

- Initial `tap-braze` Singer tap for Braze campaign and canvas details.
  - `campaigns` and `canvases` full-table list parent streams (`/campaigns/list`,
    `/canvas/list`) with Braze 0-indexed page-number pagination.
  - `campaign_details` and `canvas_details` full-table child streams
    (`/campaigns/details`, `/canvas/details`) that fan out one details request per
    parent id via the Singer SDK `parent_stream_type` + `get_child_context`
    mechanism. The details payload does not echo the id, so `campaign_id` /
    `canvas_id` is injected from the parent context as the primary key.
  - Bearer authentication with a configurable REST base URL (`api_url`) and API
    key (`api_key`), and Retry-After backoff, consistent with the DNA-10408 Braze
    list config.
