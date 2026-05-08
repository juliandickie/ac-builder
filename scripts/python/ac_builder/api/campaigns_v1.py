"""V1 campaign endpoints: campaign_create, campaign_send, message_template_add."""
from __future__ import annotations

from typing import Any

from ac_builder.api.v1_client import ACV1Client


def campaign_create(
    client: ACV1Client,
    *,
    name: str,
    message_id: int | str,
    list_ids: list[int] | list[str],
    sdate: str | None = None,
    status: int = 0,
    track_links: str = "all",
    track_link_domain: str | None = None,
    track_reads: bool = True,
    track_replies: bool = False,
    address_id: int | str = 0,
    public: bool = True,
    type: str = "single",
    segment_id: int | str = 0,
    message_percentage: int = 100,
) -> int:
    """Create a campaign via V1 campaign_create. Returns the new campaign ID."""
    params: dict[str, Any] = {
        "type": type,
        "name": name,
        "status": str(status),
        "public": "1" if public else "0",
        "tracklinks": track_links,
        "trackreads": "1" if track_reads else "0",
        "trackreplies": "1" if track_replies else "0",
        "segmentid": str(segment_id),
        "addressid": str(address_id),
        f"m[{message_id}]": str(message_percentage),
    }
    if sdate:
        params["sdate"] = sdate
    if track_link_domain:
        params["tracklinkurl"] = track_link_domain

    for list_id in list_ids:
        params[f"p[{list_id}]"] = "1"

    response = client.call("campaign_create", params)
    cid = response.get("id")
    if cid is None:
        raise ValueError(f"campaign_create returned no id: {response}")
    return int(cid)


def campaign_send(
    client: ACV1Client,
    *,
    email: str,
    campaign_id: int | str,
    message_id: int | str,
    type: str = "html",
    action: str = "send",
) -> dict[str, Any]:
    """One-off campaign send to a single email address."""
    return client.call("campaign_send", {
        "email": email,
        "campaignid": str(campaign_id),
        "messageid": str(message_id),
        "type": type,
        "action": action,
    })


def message_template_add(
    client: ACV1Client,
    *,
    name: str,
    html: str,
    template_scope: str = "all",
    tags: list[str] | None = None,
) -> int:
    """Create a reusable HTML template. Returns the template ID."""
    params: dict[str, Any] = {
        "name": name,
        "html": html,
        "template_scope": template_scope,
    }
    for i, tag in enumerate(tags or []):
        params[f"tags[{i}]"] = tag

    response = client.call("message_template_add", params)
    tid = response.get("id")
    if tid is None:
        raise ValueError(f"message_template_add returned no id: {response}")
    return int(tid)
