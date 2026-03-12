from datetime import date, datetime


def get_partition_path_from_record(
    record: dict,
    partition_date_field: str,
    partition_date_format: str,
    fallback_date: datetime,
) -> str:
    """Resolve partition path string from the record's date field.

    Reads the record field named by partition_date_field. Parses as date/datetime
    (ISO via fromisoformat, then fallback %Y-%m-%d). If the field is missing or
    unparseable, returns fallback_date formatted with partition_date_format.
    Callers may use DEFAULT_PARTITION_DATE_FORMAT for Hive-style paths.

    Args:
        record: Record dict containing the partition date field.
        partition_date_field: Key in record for the date/datetime value.
        partition_date_format: strftime format for the returned path segment.
        fallback_date: Date used when field is missing or unparseable.

    Returns:
        Partition path string (e.g. "year=2024/month=03/day=11").
    """
    value = record.get(partition_date_field)
    if value is None:
        return fallback_date.strftime(partition_date_format)
    if isinstance(value, (datetime, date)):
        return value.strftime(partition_date_format)
    if not isinstance(value, str):
        return fallback_date.strftime(partition_date_format)
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.strftime(partition_date_format)
    except (ValueError, TypeError):
        pass
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
        return parsed.strftime(partition_date_format)
    except (ValueError, TypeError):
        pass
    return fallback_date.strftime(partition_date_format)
