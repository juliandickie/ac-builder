"""Campaign operations.

Phase 1: list, get (read-only).
Phase 2: duplicate, update, delete (stubs below, marked TODO until verified
against AC's actual endpoint shapes).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ac_builder.api.v3_client import ACClient


def list_campaigns(
    client: ACClient,
    **filters: Any,
) -> Iterator[dict[str, Any]]:
    """Iterate through every campaign in the account.

    Filters can include any of AC's documented filter params, e.g.:
        type="single", status="1,2,3", name="LPIS"
    Pass them as keyword arguments and they'll be wired into the query string
    as filters[type]=single etc., per AC's filter-params convention.
    """
    # AC uses filters[X]=Y query param style. Translate kwargs.
    params: dict[str, Any] = {}
    for k, v in filters.items():
        params[f"filters[{k}]"] = v
    return client.paginate("campaigns", "campaigns", params=params)


def get_campaign(client: ACClient, campaign_id: int | str) -> dict[str, Any]:
    """Fetch one campaign by ID. Returns the full response (campaign + linked objects)."""
    return client.get(f"campaigns/{campaign_id}")


# ---------------------------------------------------------------------------
# Phase 2 - Campaign CRUD. Verified 2026-04-27 against live AC instance.
# Findings during verification:
#   - duplicate uses POST /campaigns/{id}/copy (NOT /campaign/clones)
#     and returns {"succeeded","message","newCampaignId"} (NOT nested campaign)
#   - delete uses DELETE /campaigns/{id}/delete (action-style, NOT REST-standard)
#   - update uses PUT /campaigns/{id} with {"campaign": {fields}} - REST-standard
#   - Campaigns INSIDE active automations cannot be copied via API
#     (returns 400 "not allowed to copy this campaign"). For the master-and-edit
#     workflow, build masters as standalone drafts, copy them, then attach
#     duplicates to automation Send Email steps via the AC UI.
# See docs/superpowers/specs/2026-04-27-ac-builder-phase-2-and-plugin-design.md.
# ---------------------------------------------------------------------------


def duplicate_campaign(
    client: ACClient,
    campaign_id: int | str,
    new_name: str,
) -> dict[str, Any]:
    """Duplicate a campaign and rename it. Returns enriched response.

    The duplicate inherits the master's HTML template, styling, from-name,
    from-email, reply-to, and message structure. Subject lines and body
    content are also copied verbatim - typically updated via update_message()
    after duplication.

    **Two-step operation under the hood** (because AC's copy endpoint ignores
    the name parameter and always uses "<original> (Copy)"):
      1. POST /api/3/campaigns/{id}/copy with empty body -> creates duplicate
      2. PUT /api/3/campaigns/{newId} -> renames it to new_name

    **Important:** the source campaign cannot be inside an active automation.
    AC's API returns 400 "not allowed to copy this campaign" for campaigns
    that belong to an automation flow. Tim's master campaigns must be
    standalone (not yet wired into an automation Send Email step) for
    duplication to work. After duplication and content edits, the duplicates
    can be added to automation steps via the AC UI.

    Returns:
        Enriched dict: {"succeeded": bool, "message": str, "newCampaignId": int,
                        "renamed_to": str}

    Verified 2026-04-27 against live AC instance.
    """
    # Step 1: Copy. AC ignores the name param so we send empty body.
    copy_response = client.post(f"campaigns/{campaign_id}/copy", json={})
    new_id = copy_response.get("newCampaignId")
    if not copy_response.get("succeeded") or not new_id:
        # Copy failed - return the raw response for the caller to handle
        return {**copy_response, "renamed_to": None}

    # Step 2: Rename via update_campaign.
    update_campaign(client, new_id, name=new_name)

    return {**copy_response, "renamed_to": new_name}


def update_campaign(
    client: ACClient,
    campaign_id: int | str,
    *,
    name: str | None = None,
    fromname: str | None = None,
    fromemail: str | None = None,
    reply2: str | None = None,
    analytics_campaign_name: str | None = None,
    addressid: int | str | None = None,
    public: int | bool | None = None,
    basemessageid: int | str | None = None,
) -> dict[str, Any]:
    """Update top-level campaign metadata. Sends only fields that are not None.

    For changing email content (subject, preview, body HTML), use
    messages.update_message() instead - that operates on the message, not
    the campaign.

    Args:
        analytics_campaign_name: Sets the Google Analytics utm_campaign value.
            Per the AC Specs, this should be the sequence's campaign-name slug
            (e.g., "implant-pathway-2026-aunz").
        addressid: ID of the physical mailing address shown in the email
            footer (CAN-SPAM compliance). Use list_addresses() to find IDs.
            Default is account-dependent.
        public: Campaign archive visibility. 0 = private (default for the iDD
            launch), 1 = public.
        basemessageid: Reference to a "starting template" message. Generally
            set by AC's UI when a campaign is initialized; rarely needed via API.

    Endpoint: PUT /api/3/campaigns/{id}
    Payload: {"campaign": {<changed-fields>}}

    Verified 2026-04-27 - all three settings (analytics_campaign_name, addressid,
    public) confirmed via PUT against campaign 3409.
    """
    fields: dict[str, Any] = {}
    if name is not None:
        fields["name"] = name
    if fromname is not None:
        fields["fromname"] = fromname
    if fromemail is not None:
        fields["fromemail"] = fromemail
    if reply2 is not None:
        fields["reply2"] = reply2
    if analytics_campaign_name is not None:
        fields["analytics_campaign_name"] = analytics_campaign_name
    if addressid is not None:
        fields["addressid"] = str(addressid)
    if public is not None:
        # Coerce bool to int for AC's preferred shape
        fields["public"] = int(public) if isinstance(public, bool) else public
    if basemessageid is not None:
        fields["basemessageid"] = str(basemessageid)

    if not fields:
        raise ValueError(
            "update_campaign requires at least one field to change."
        )

    return client.put(f"campaigns/{campaign_id}", json={"campaign": fields})


def delete_campaign(client: ACClient, campaign_id: int | str) -> dict[str, Any]:
    """Delete a campaign. Destructive - the campaign is unrecoverable after this.

    The CLI layer requires an explicit --yes flag before invoking this function.

    AC quirk: the delete endpoint is action-style at /campaigns/{id}/delete,
    NOT the REST-standard /campaigns/{id}. Returns a confirmation object.

    Endpoint: DELETE /api/3/campaigns/{id}/delete
    Response: {"succeeded": bool, "message": str}

    Verified 2026-04-27 against live AC instance.
    """
    return client.delete(f"campaigns/{campaign_id}/delete")


def get_campaign_links(client: ACClient, campaign_id: int | str) -> list[dict[str, Any]]:
    """Retrieve all tracked links for a campaign.

    AC assigns link IDs only after a campaign is created and the message HTML
    is parsed. Caller should sleep ~3s after campaign_create before calling this.
    """
    response = client.get(f"campaigns/{campaign_id}/links")
    return response.get("links", [])
