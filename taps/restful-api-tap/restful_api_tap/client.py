"""REST API stream base class and request handling.

Provides RestApiStream: base for streams that read from a REST API source
and yield records (emitted as RECORD messages for the stream).
"""

from pathlib import Path
from typing import Any, Iterator, Optional

import requests
from singer_sdk.streams import RESTStream

from restful_api_tap.auth import get_authenticator

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class RestApiStream(RESTStream):
    """REST API stream base class.

    Base for streams that request records from a REST API source and support
    end-of-stream when a next-page request returns 404.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_auth = None
        self._authenticator = getattr(self, "assigned_authenticator", None)

    def _request(
        self,
        prepared_request: requests.PreparedRequest,
        context: Optional[dict],
    ) -> requests.Response:
        """Send the request and validate the response.

        When _is_next_page_request is True and the response is 404, return the
        response without raising so request_records can treat it as end-of-stream,
        stop without yielding further records, and return only records already fetched.
        """
        authenticated_request = self.authenticator(prepared_request)
        response = self.requests_session.send(
            authenticated_request,
            timeout=self.timeout,
            allow_redirects=self.allow_redirects,
        )
        self._write_request_duration_log(
            endpoint=self.path,
            response=response,
            context=context,
            extra_tags={"url": authenticated_request.path_url}
            if self._LOG_REQUEST_METRIC_URLS
            else None,
        )
        # 404 on a next-page request is treated as end-of-stream, not fatal.
        if response.status_code == 404 and getattr(
            self, "_is_next_page_request", False
        ):
            return response
        self.validate_response(response)
        return response

    def request_records(self, context: Optional[dict]) -> Iterator[dict]:
        """Request records with pagination; 404 on next-page is end-of-stream.

        Records are streamed (yielded one-by-one) and become RECORD messages
        for the stream. The tap does not retain records after passing them to
        the target. Each page's response is eligible for GC once all its
        records have been yielded.

        When a paginated next-page request returns 404, pagination stops and
        only records from previous pages are yielded. 404 on the initial
        request remains fatal (validate_response raises).
        """
        paginator = self.get_new_paginator() or self._get_single_page_paginator()
        decorated_request = self.request_decorator(self._request)  # type: ignore[arg-type]
        pages = 0

        with self.get_http_request_counter() as request_counter:
            request_counter.with_context(context)

            while not paginator.finished:
                next_page_token = paginator.current_value
                self._is_next_page_request = next_page_token is not None

                prepared_request = self.prepare_request(
                    context,
                    next_page_token=next_page_token,
                )
                resp = decorated_request(prepared_request, context)
                request_counter.increment()
                self.update_sync_costs(prepared_request, resp, context)

                # 404 on next-page: treat as end-of-stream, stop without yielding.
                if resp.status_code == 404:
                    break

                records = iter(self.parse_response(resp))
                try:
                    first_record = next(records)
                except StopIteration:
                    if paginator.continue_if_empty(resp):
                        paginator.advance(resp)
                        continue
                    self.log(
                        "Pagination stopped after %d pages because no records were "
                        "found in the last response",
                        pages,
                    )
                    break
                yield first_record
                yield from records
                pages += 1
                paginator.advance(resp)

    def _get_single_page_paginator(self):
        """Return the SDK single-page paginator (used when get_new_paginator is None)."""
        from singer_sdk.pagination import SinglePagePaginator

        return SinglePagePaginator()

    @property
    def url_base(self) -> Any:
        """Return the base URL for requests to the REST API source.

        Configurable via the config file.

        Returns:
            The base URL for API requests.

        """
        return self.config["api_url"]

    @property
    def authenticator(self) -> Any:
        """Call an appropriate SDK Authentication method.

        Calls an appropriate SDK Authentication method based on auth_method,
        which is set via the config file. If an authenticator (auth_method) is
        not specified, REST-based taps pass `http_headers` as defined in the
        tap and stream classes.

        Note 1: Each auth method requires certain configuration in the config
        file; see README.md for each auth method's requirements.

        Note 2: Singleton pattern on the authenticator for caching, with a
        check if an OAuth token has expired and needs refreshing.

        Raises:
            ValueError: if the auth_method is unknown.

        Returns:
            An SDK Authenticator or APIAuthenticatorBase if no auth_method
            supplied.

        """
        # Obtaining authenticator to authenticate requests to the source.
        get_authenticator(self)

        return self._authenticator
