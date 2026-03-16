from collections.abc import Callable
from typing import Any

from .string_functions import date_as_partition, string_as_partition
from .validators import is_date_field


def get_hive_path_generator(
    partition_fields: list[str], schema: dict[str, Any]
) -> list[tuple[str, Callable[[str, str], str]]]:
    hive_path: list[tuple[str, Callable[[str, str], str]]] = []
    for partition_field in partition_fields:
        if is_date_field(schema.get("properties", {}).get(partition_field)):
            hive_path.append((partition_field, date_as_partition))
        else:
            hive_path.append((partition_field, string_as_partition))
    return hive_path
