"""AC Message operations.

A Campaign in AC owns one or more Messages. Subject lines, preview text, and
HTML body content live on the Message, not the Campaign. To edit content of a
duplicated campaign, you operate on its message(s).

For split-test campaigns, a campaign has multiple messages (one per variant).
"""

from __future__ import annotations

from typing import Any

from ac_builder.api.v3_client import ACClient


def get_message(client: ACClient, message_id: int | str) -> dict[str, Any]:
    """Fetch one message by ID. Returns subject, preheader text, html, text + metadata.

    Use this to inspect a message's structure before editing - particularly to
    capture the current subject line, preview text, and body HTML so updates
    can be partial (only changing what you intend to change).

    Endpoint: GET /api/3/messages/{id}
    """
    return client.get(f"messages/{message_id}")


def update_message(
    client: ACClient,
    message_id: int | str,
    *,
    subject: str | None = None,
    preheader_text: str | None = None,
    html: str | None = None,
    text: str | None = None,
    fromname: str | None = None,
    fromemail: str | None = None,
    reply2: str | None = None,
) -> dict[str, Any]:
    """Update specific fields on a message. Sends only fields that are not None.

    Args:
        message_id: Message ID to update
        subject: New subject line
        preheader_text: New preview/preheader text (shown in inbox preview)
        html: New full HTML body
        text: New plain-text version
        fromname: New from-name
        fromemail: New from-email
        reply2: New reply-to address

    Returns:
        The updated message data.

    Endpoint: PUT /api/3/messages/{id}
    Payload: {"message": {<changed-fields>}}
    """
    fields: dict[str, Any] = {}
    if subject is not None:
        fields["subject"] = subject
    if preheader_text is not None:
        fields["preheader_text"] = preheader_text
    if html is not None:
        fields["html"] = html
    if text is not None:
        fields["text"] = text
    if fromname is not None:
        fields["fromname"] = fromname
    if fromemail is not None:
        fields["fromemail"] = fromemail
    if reply2 is not None:
        fields["reply2"] = reply2

    if not fields:
        raise ValueError(
            "update_message requires at least one field to change. "
            "Pass subject=, preheader_text=, html=, etc."
        )

    return client.put(f"messages/{message_id}", json={"message": fields})
