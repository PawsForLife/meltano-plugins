"""Singer target implementation that reads Singer messages from stdin and loads data into Google Cloud Storage (GCS) as the destination. Configuration is supplied via a config file; the target may participate in state file handling per the Singer spec."""

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from gcs_target.sinks import GCSSink


class GCSTarget(Target):
    """Singer target (data loader) for GCS as the destination. Uses a config file for settings and may use or emit state file data per the Singer spec."""

    name = "target-gcs"
    config_jsonschema = th.PropertiesList(
        th.Property("bucket_name", th.StringType, required=True),
        th.Property("key_prefix", th.StringType, required=False),
        th.Property("key_naming_convention", th.StringType, required=False),
        th.Property(
            "max_records_per_file",
            th.IntegerType,
            required=False,
            description="Maximum records per GCS object; 0 or unset = no chunking.",
        ),
    ).to_dict()
    default_sink_class = GCSSink
