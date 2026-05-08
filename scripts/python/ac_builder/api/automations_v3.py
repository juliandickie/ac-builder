"""V3 automation endpoints.

GET, POST, PATCH for automation flows. The automation JSON schema is partly
undocumented - the recommended pattern is to capture an existing automation's
JSON via GET, save as a fixture, and substitute IDs at runtime.

See: docs/superpowers/specs/2026-04-28-ac-builder-phase-4-mjml-pipeline-design.md
section 6 for the link-action workaround pattern.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ac_builder.api.v3_client import ACClient


def list_automations(client: ACClient, **filters: Any) -> Iterator[dict[str, Any]]:
    """Iterate over all automations."""
    params = {f"filters[{k}]": v for k, v in filters.items()}
    return client.paginate("automations", "automations", params=params)


def get_automation(client: ACClient, automation_id: int | str) -> dict[str, Any]:
    """Fetch a single automation including triggers and actions."""
    return client.get(f"automations/{automation_id}")


def create_automation(client: ACClient, automation: dict[str, Any]) -> dict[str, Any]:
    """Create a new automation. Pass the full automation dict (without the outer 'automation' wrapper)."""
    return client.post("automations", json={"automation": automation})


def activate_automation(client: ACClient, automation_id: int | str) -> dict[str, Any]:
    """Set automation status to 1 (active)."""
    return client.patch(
        f"automations/{automation_id}",
        json={"automation": {"status": "1"}},
    )


def deactivate_automation(client: ACClient, automation_id: int | str) -> dict[str, Any]:
    """Set automation status to 0 (inactive/draft). For cleanup post-send-window."""
    return client.patch(
        f"automations/{automation_id}",
        json={"automation": {"status": "0"}},
    )
