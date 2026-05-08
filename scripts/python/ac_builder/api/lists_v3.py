"""V3 list operations: GET /lists, resolve list names → IDs."""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ac_builder.api.v3_client import ACClient


def list_lists(client: ACClient, **filters: Any) -> Iterator[dict[str, Any]]:
    """Iterate over all lists in the account."""
    params = {f"filters[{k}]": v for k, v in filters.items()}
    return client.paginate("lists", "lists", params=params)


def get_list_id_by_name(client: ACClient, name: str) -> int | None:
    """Find a list ID by exact name match. Returns None if not found."""
    for lst in list_lists(client):
        if lst.get("name") == name:
            return int(lst["id"])
    return None
