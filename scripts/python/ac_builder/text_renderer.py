"""Convert AC-bound HTML to a plain-text version for the multipart MIME message.

Handles email-content conventions:
  - Links: "text (url)" inline; "text: url" if the link is a CTA-style block
  - Headings: uppercase, blank line above
  - Lists: "- item" prefix
  - AC merge fields (%FOO%, %FIRSTNAME|TITLECASE%) preserved verbatim
  - Style/script tags stripped entirely
  - Multiple blank lines collapsed
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString


def html_to_text(html: str) -> str:
    """Convert HTML to a plain-text version suitable for the multipart message."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["style", "script", "head"]):
        tag.decompose()

    parts: list[str] = []
    _walk(soup.body or soup, parts)
    text = "\n".join(parts)

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip() + "\n"


def _walk(node, out: list[str]) -> None:
    if isinstance(node, NavigableString):
        s = str(node).strip()
        if s:
            out.append(s)
        return

    if not hasattr(node, "name") or node.name is None:
        for child in getattr(node, "children", []):
            _walk(child, out)
        return

    tag = node.name.lower()

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        text = node.get_text(" ", strip=True)
        if text:
            out.append("")
            out.append(text.upper())
            out.append("")
        return

    if tag == "p":
        text = _inline_text(node)
        if text:
            out.append(text)
            out.append("")
        return

    if tag in ("ul", "ol"):
        for i, li in enumerate(node.find_all("li", recursive=False), start=1):
            prefix = f"{i}." if tag == "ol" else "-"
            li_text = _inline_text(li)
            if li_text:
                out.append(f"{prefix} {li_text}")
        out.append("")
        return

    if tag == "br":
        out.append("")
        return

    if tag == "hr":
        out.append("")
        out.append("---")
        out.append("")
        return

    if tag == "a":
        href = node.get("href", "")
        text = node.get_text(" ", strip=True)
        if href and text:
            if _looks_like_button_anchor(node):
                out.append(text)
                out.append(href)
            else:
                out.append(f"{text} ({href})")
        else:
            out.append(text)
        return

    for child in node.children:
        _walk(child, out)


def _inline_text(node) -> str:
    """Render the inline content of a block-level node, preserving link URLs."""
    fragments: list[str] = []
    for child in node.descendants:
        if isinstance(child, NavigableString):
            if child.parent and child.parent.name == "a":
                continue
            fragments.append(str(child))
        elif getattr(child, "name", None) == "a":
            href = child.get("href", "")
            text = child.get_text(" ", strip=True)
            if href and text:
                if _looks_like_button_anchor(child):
                    fragments.append(f"{text}: {href}")
                else:
                    fragments.append(f"{text} ({href})")
            else:
                fragments.append(text)
        elif getattr(child, "name", None) == "br":
            fragments.append("\n")
    text = "".join(fragments).strip()
    text = re.sub(r"[ \t]+", " ", text)
    return text


def _looks_like_button_anchor(a_tag) -> bool:
    """Heuristic: does this <a> look like an MJML button (block/CTA style)?"""
    style = (a_tag.get("style") or "").lower()
    return "background-color" in style and "padding" in style
