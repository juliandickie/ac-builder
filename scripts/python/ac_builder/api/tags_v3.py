"""Tag operations."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ac_builder.api.v3_client import ACClient


def list_tags(
    client: ACClient,
    search: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Iterate through every tag in the account.

    Args:
        search: Optional contains-match on tag name.
    """
    params: dict[str, Any] = {}
    if search:
        # AC's /tags endpoint accepts ?search=foo for contains-matching
        params["search"] = search
    return client.paginate("tags", "tags", params=params)


def get_tag(client: ACClient, tag_id: int | str) -> dict[str, Any]:
    """Fetch one tag by ID."""
    return client.get(f"tags/{tag_id}")


def create_tag(
    client: ACClient,
    name: str,
    tag_type: str = "contact",
    description: str = "",
) -> dict[str, Any]:
    """Create a tag.

    Args:
        name: Tag name (e.g., "PROMO: LPIS 2026").
        tag_type: "contact" (default) or "template".
        description: Optional description.

    Returns:
        Newly created tag data including its ID.
    """
    payload = {
        "tag": {
            "tag": name,
            "tagType": tag_type,
            "description": description,
        }
    }
    return client.post("tags", json=payload)
