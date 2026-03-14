from datetime import date, datetime

from dateutil import parser as dateutil_parser

from target_gcs.constants import DEFAULT_PARTITION_DATE_FORMAT


def date_as_partition(field_name: str, field_value: str) -> str:

    if isinstance(field_value, (datetime, date)):
        date_value = field_value
    elif isinstance(field_value, str):
        date_value = dateutil_parser.parse(field_value)
    return date_value.strftime(DEFAULT_PARTITION_DATE_FORMAT)


def string_as_partition(field_name: str, field_value: str) -> str:
    return f"{field_name}={str(field_value).replace('/', '_')}"
