"""Pagination helpers for streams that request paged data from a REST API source and yield records (RECORD messages)."""

from typing import Any, List, Optional, cast
from urllib.parse import parse_qs, urlparse

import requests
from dateutil.parser import parse
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import (
    BaseOffsetPaginator,
    BasePageNumberPaginator,
    HeaderLinkPaginator,
)

from restful_api_tap.utils import unnest_dict


class RestAPIBasePageNumberPaginator(BasePageNumberPaginator):
    """Page-number paginator used by a stream to determine whether more pages of records exist from the source."""

    def __init__(self, *args, jsonpath=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._jsonpath = jsonpath

    def has_more(self, response: requests.Response):
        """Return True if there are more pages to fetch.

        Args:
            response: The most recent response from the source (API response).

        Returns:
            Whether there are more pages of records to fetch.

        """
        if self._jsonpath:
            return next(extract_jsonpath(self._jsonpath, response.json()), None)
        else:
            return response.json().get("hasMore", None)


class RestAPIOffsetPaginator(BaseOffsetPaginator):
    """Offset paginator used by a stream for paged records from the source."""

    def __init__(
        self, *args, jsonpath=None, pagination_total_limit_param: str, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.jsonpath = jsonpath
        self.pagination_total_limit_param = pagination_total_limit_param

    def has_more(self, response: requests.Response):
        """Return True if there are more pages to fetch.

        Args:
            response: The most recent response from the source (API response).

        Returns:
            Whether there are more pages of records to fetch.

        """
        if self.jsonpath:
            pagination = next(extract_jsonpath(self.jsonpath, response.json()), None)
        else:
            pagination = response.json().get("pagination", None)
        if pagination:
            pagination = unnest_dict(pagination)

        if pagination and all(x in pagination for x in ["offset", "limit"]):
            record_limit = pagination.get(self.pagination_total_limit_param, 0)
            records_read = pagination["offset"] + pagination["limit"]
            if records_read <= record_limit:
                return True

        return False


class SimpleOffsetPaginator(BaseOffsetPaginator):
    """Offset/size paginator used by a stream to paginate records from the source."""

    def __init__(
        self,
        *args,
        offset_records_jsonpath=None,
        pagination_page_size: int = 25,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._offset_records_jsonpath = offset_records_jsonpath
        self._pagination_page_size = pagination_page_size

    def has_more(self, response: requests.Response):
        """Return True if there are more pages to fetch.

        Args:
            response: The most recent response from the source (API response).

        Returns:
            Whether there are more pages of records to fetch.

        """
        if self._offset_records_jsonpath:
            extracted: List[Any] = cast(
                List[Any],
                next(
                    extract_jsonpath(self._offset_records_jsonpath, response.json()),
                    [],
                ),
            )
            return len(extracted) == self._pagination_page_size

        return len(response.json()) == self._pagination_page_size


class RestAPIHeaderLinkPaginator(HeaderLinkPaginator):
    """Header-link paginator used by a stream when the source uses Link headers for next-page URLs; yields paged records."""

    def __init__(
        self,
        *args,
        pagination_page_size: int = 25,
        pagination_results_limit: Optional[int] = None,
        use_fake_since_parameter: Optional[bool] = False,
        replication_key: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pagination_page_size = pagination_page_size
        self.pagination_results_limit = pagination_results_limit
        self.use_fake_since_parameter = use_fake_since_parameter
        self.replication_key = replication_key

    def get_next_url(self, response: requests.Response) -> Optional[Any]:
        """Return next page parameter(s) for the stream.

        Returns next-page parameters for the next page of records, or None if no more pages.
        Logic based on https://github.com/MeltanoLabs/tap-github

        Args:
            response: The most recent response from the source.
            pagination_page_size: Limit on records per page. Default=25.
            pagination_results_limit: Limit on the number of pages returned.
            use_fake_since_parameter: Workaround for GitHub endpoints. default=False.
            replication_key: Replication key for INCREMENTAL sync (bookmarks).

        Returns:
            Page parameters for the next page of records if more pages exist, else None.

        """
        # Exit if the record limit is reached.
        if (
            self._page_count
            and self.pagination_results_limit
            and (
                cast(int, self._page_count) * self.pagination_page_size
                >= self.pagination_results_limit
            )
        ):
            return None

        # Leverage header links returned by the source (e.g. GitHub API).
        if "next" not in response.links.keys():
            return None

        # Exit early if there is no URL in the next links.
        if not response.links.get("next", {}).get("url"):
            return None

        resp_json = response.json()
        if isinstance(resp_json, list):
            results = resp_json
        else:
            results = resp_json.get("items")

        # Exit early if the response has no records.
        if not results:
            return None

        # Some source endpoints (e.g. /starred, /stargazers, /events, /pulls) do not
        # support the "since" parameter. Workaround: sort by descending dates and
        # paginate back in time until we reach records before the bookmark (fake_since).
        if self.replication_key and self.use_fake_since_parameter:
            request_parameters = parse_qs(str(urlparse(response.request.url).query))
            # parse_qs interprets "+" as a space, revert this to keep an aware datetime
            try:
                since = (
                    request_parameters["fake_since"][0].replace(" ", "+")
                    if "fake_since" in request_parameters
                    else ""
                )
            except IndexError:
                return None

            direction = (
                request_parameters["direction"][0]
                if "direction" in request_parameters
                else None
            )

            # commit_timestamp is a constructed replication key not present in the raw response.
            replication_date = (
                results[-1][self.replication_key]
                if self.replication_key != "commit_timestamp"
                else results[-1]["commit"]["committer"]["date"]
            )
            # Exit early if replication_date is before the bookmark (since).
            if (
                since
                and direction == "desc"
                and (parse(replication_date) < parse(since))
            ):
                return None

        # Use header links from the source response to return the query parameters.
        parsed_url = urlparse(response.links["next"]["url"])

        if parsed_url.query:
            return parsed_url.query

        return None
