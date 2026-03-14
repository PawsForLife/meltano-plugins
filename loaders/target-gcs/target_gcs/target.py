"""Singer target implementation that reads Singer messages from stdin and loads data into Google Cloud Storage (GCS) as the destination. Configuration is supplied via a config file; the target may participate in state file handling per the Singer spec."""

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_gcs.sinks import GCSSink


class GCSTarget(Target):
    """Singer target (data loader) for GCS as the destination. Uses a config file for settings and may use or emit state file data per the Singer spec."""

    name = "target-gcs"

    def __init__(self, *, config=None, **kwargs):
        """Initialize the target and set _storage_client for optional injection (e.g. tests)."""
        super().__init__(config=config, **kwargs)
        self._storage_client = None

    config_jsonschema = th.PropertiesList(
        th.Property("bucket_name", th.StringType, required=True),
        th.Property("key_prefix", th.StringType, required=False),
        th.Property(
            "max_records_per_file",
            th.IntegerType,
            required=False,
            description="Maximum records per GCS object; 0 or unset = no chunking.",
        ),
        th.Property(
            "hive_partitioned",
            th.BooleanType,
            required=False,
            default=False,
            description="When true, enable Hive partitioning from stream schema (x-partition-fields) or current date.",
        ),
    ).to_dict()
    default_sink_class = GCSSink

    def get_sink(self, stream_name, *, record=None, schema=None, key_properties=None):
        """Return a sink for the stream; create one with storage_client when needed."""
        _ = record
        if schema is None:
            return self._sinks_active[stream_name]

        existing_sink = self._sinks_active.get(stream_name, None)
        if not existing_sink:
            return self._add_sink_with_client(stream_name, schema, key_properties)

        if (
            existing_sink.original_schema != schema
            or existing_sink.key_properties != key_properties
        ):
            self.logger.info(
                "Schema or key properties for '%s' stream have changed. "
                "Initializing a new '%s' sink...",
                stream_name,
                stream_name,
            )
            self._sinks_to_clear.append(self._sinks_active.pop(stream_name))
            return self._add_sink_with_client(stream_name, schema, key_properties)

        return existing_sink

    def _add_sink_with_client(self, stream_name, schema, key_properties):
        """Create a sink with storage_client and register it (used by get_sink)."""
        sink_class = self.get_sink_class(stream_name=stream_name)
        sink = sink_class(
            target=self,
            stream_name=stream_name,
            schema=schema,
            key_properties=key_properties,
            storage_client=self._storage_client,
        )
        sink.setup()
        self._sinks_active[stream_name] = sink
        return sink
