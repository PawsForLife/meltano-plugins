# tap-braze

Singer SDK tap for Braze campaign and canvas **details** (the descriptive
attributes: type, schedule, channels, messages, tags, timestamps) from the
Braze REST API.

Streams: `campaigns` and `canvases` (list parents) plus `campaign_details` and
`canvas_details` (details children). All streams are full-table.

## Parent-child fan-out

The Braze details endpoints (`/campaigns/details`, `/canvas/details`) take a
single id per call, so the generic REST tap cannot source them from a list. This
tap models each details stream as a Singer SDK child of its list stream
(`parent_stream_type` + `get_child_context`): every id emitted by a parent list
stream fans out exactly one details request. The details payload does not echo
the id, so each record's primary key (`campaign_id` / `canvas_id`) is injected
from the parent context.

Because the SDK parent-child mechanism requires the parent stream to live in the
same tap, `tap-braze` defines its own `campaigns` / `canvases` list parent
streams rather than consuming the config-only list output landed by DNA-10408
(`restful-api-tap`); a config-only list cannot serve as an SDK parent. The list
endpoints, Bearer auth, and REST base URL are kept consistent with that config.

## Meltano

```yaml
plugins:
  extractors:
    - name: tap-braze
      namespace: tap_braze
      pip_url: git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=taps/tap-braze
      config:
        api_url: ${BRAZE_REST_URL}
        api_key: ${BRAZE_REST_API_KEY}
```

`api_url` is the Braze REST instance endpoint (e.g. `https://rest.iad-07.braze.com`);
`api_key` is a Braze REST API key with campaign/canvas export permissions, sent as
`Authorization: Bearer <api_key>`. Do not set `variant` for this custom extractor.
The tap supports Singer `--discover`, `--catalog`, and standard JSONL output for
loaders such as `target-gcs`.

## Development

```bash
./install.sh
```
