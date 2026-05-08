"""V1 message endpoints: message_add, message_delete."""
from __future__ import annotations

from typing import Any

from ac_builder.api.v1_client import ACV1Client


def message_add(
    client: ACV1Client,
    *,
    subject: str,
    fromemail: str,
    fromname: str,
    reply2: str,
    html: str,
    text: str,
    list_ids: list[int] | list[str],
    priority: int = 3,
    encoding: str = "quoted-printable",
    charset: str = "utf-8",
) -> int:
    """Create a new message via V1 message_add. Returns the new message ID."""
    params: dict[str, Any] = {
        "format": "mime",
        "subject": subject,
        "fromemail": fromemail,
        "fromname": fromname,
        "reply2": reply2,
        "priority": str(priority),
        "charset": charset,
        "encoding": encoding,
        # 'external' was documented in the AC reference but means 'fetch from
        # external URL' - AC mangles inline HTML over ~1KB to literal 'fetch:'
        # in that mode. 'html' preserves the inline body verbatim. Verified
        # 2026-04-29 with the LPIS E1 27KB HTML payload.
        "htmlconstructor": "html",
        "html": html,
        "textconstructor": "html",
        "text": text,
    }
    for list_id in list_ids:
        params[f"p[{list_id}]"] = "1"

    response = client.call("message_add", params)
    msg_id = response.get("id")
    if msg_id is None:
        raise ValueError(f"message_add returned no id: {response}")
    return int(msg_id)


def message_delete(client: ACV1Client, *, message_id: int | str) -> None:
    """Delete a message by ID."""
    client.call("message_delete", {"id": str(message_id)})
