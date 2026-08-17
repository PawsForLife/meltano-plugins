# Overview

**Fork notice:** This repository is a fork of [Widen/tap-rest-api-msdk](https://github.com/Widen/tap-rest-api-msdk). We maintain it with changes specific to our needs and comply with the original project’s license. The upstream source is [https://github.com/Widen/tap-rest-api-msdk](https://github.com/Widen/tap-rest-api-msdk). This repo or project may be renamed later; the fork relationship and attribution to the original source remain.

---

`restful-api-tap` is a Singer tap for generic REST APIs. The Python package is `restful_api_tap`. The tap emits Singer message types (SCHEMA, RECORD, STATE). The main differentiator is **schema auto-discovery**: stream schemas can be inferred from sample API responses.

This is particularly useful if you have a stream with a very large and complex schema or
a stream that outputs records with varying schemas for each record. Can also be used for
simpler more reliable streams.

There are many forms of Authentication supported by this tap. By default for legacy support, you can pass Authentication via headers. If you want to use the built in support for Authentication, this tap supports
- Basic Authentication
- API Key
- Bearer Token
- OAuth
- AWS

Please note that OAuthJWTAuthentication has not been developed. If you are interested in contributing this, please fork and make a pull request.

Built with the Meltano [SDK](https://gitlab.com/meltano/sdk) for Singer Taps.

**Requirements:** Python 3.14+.

### Memory and performance

The tap streams records and does not retain them after they are passed to the target; each page's response is eligible for garbage collection once its records have been yielded. `store_raw_json_message` increases per-record memory use (the raw message is stored by reference; downstream must not mutate it). Schema discovery issues one request per stream and holds the full response in memory; use `discovery_request_limit` when the API supports it to limit that response size.

Gratitude goes to [anelendata](https://github.com/anelendata/tap-rest-api) for inspiring this "SDK-ized" version of their tap.

[← Documentation index](index.md) · [Installation →](installation.md)
