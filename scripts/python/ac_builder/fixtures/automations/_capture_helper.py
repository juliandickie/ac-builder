"""Helper functions for capturing and sanitizing AC automation JSON.

Used by `ac-builder capture-automation` CLI command. Substitutes specific
campaign/link/tag IDs with placeholder strings so the captured JSON can serve
as a template at build time.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PLACEHOLDER_MAP = {
    ("click", "campaignid"): "__CAMPAIGN_ID__",
    ("click", "linkid"): "__LINK_ID__",
    ("tagAdd", "tag"): "__TAG_ID__",
    ("automation", "automation"): "__AUTOMATION_ID__",
}


def sanitize_automation(automation: dict[str, Any]) -> dict[str, Any]:
    """Replace specific IDs with placeholders so the JSON serves as a template."""
    sanitized = json.loads(json.dumps(automation))  # deep copy

    for trigger in sanitized.get("triggers", []):
        ttype = trigger.get("type", "")
        params = trigger.get("params", {})
        for key in list(params.keys()):
            placeholder = _PLACEHOLDER_MAP.get((ttype, key))
            if placeholder:
                params[key] = placeholder

    for action in sanitized.get("actions", []):
        atype = action.get("type", "")
        params = action.get("params", {})
        for key in list(params.keys()):
            placeholder = _PLACEHOLDER_MAP.get((atype, key))
            if placeholder:
                params[key] = placeholder

    for field_to_strip in ("id", "userid", "cdate", "mdate", "rev_count"):
        sanitized.pop(field_to_strip, None)

    return sanitized


def save_template(automation: dict[str, Any], out_path: Path) -> None:
    """Sanitize and write to a fixture file."""
    sanitized = sanitize_automation(automation)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(sanitized, f, indent=2)
