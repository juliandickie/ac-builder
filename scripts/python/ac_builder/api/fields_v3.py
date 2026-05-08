"""Custom contact field operations."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ac_builder.api.v3_client import ACClient


def list_custom_fields(client: ACClient) -> Iterator[dict[str, Any]]:
    """Iterate through every custom contact field in the account."""
    return client.paginate("fields", "fields")


def get_custom_field(client: ACClient, field_id: int | str) -> dict[str, Any]:
    """Fetch one custom field by ID."""
    return client.get(f"fields/{field_id}")
