"""V3 address operations: GET /addresses for sender physical addresses."""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ac_builder.api.v3_client import ACClient


def list_addresses(client: ACClient) -> Iterator[dict[str, Any]]:
    """Iterate over all sender physical address records."""
    return client.paginate("addresses", "addresses")
