"""Braze tap entry point."""

from singer_sdk import Tap
from singer_sdk import typing as th

from tap_braze.streams import (
    BrazeStream,
    CampaignDetailsStream,
    CampaignsStream,
    CanvasDetailsStream,
    CanvasesStream,
)


class BrazeTap(Tap):
    """Extract campaign and canvas attributes from the Braze REST API."""

    name = "tap-braze"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_url",
            th.StringType(pattern=r"^https://"),
            required=True,
        ),
        th.Property(
            "api_key",
            th.StringType(min_length=1),
            required=True,
            secret=True,
        ),
    ).to_dict()

    def discover_streams(self) -> list[BrazeStream]:
        """Return the streams exposed by this tap.

        The two list streams are parents; the SDK invokes each details child
        once per id emitted by its parent, so all four are registered here.
        """
        return [
            CampaignsStream(self),
            CampaignDetailsStream(self),
            CanvasesStream(self),
            CanvasDetailsStream(self),
        ]


if __name__ == "__main__":
    BrazeTap.cli()
