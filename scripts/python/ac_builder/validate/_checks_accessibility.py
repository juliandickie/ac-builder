"""Accessibility checks for pre_send."""
from __future__ import annotations

from bs4 import BeautifulSoup

from ac_builder.validate.pre_send import CheckFinding, PreSendInputs, register_check


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


@register_check
def check_image_alt_text(inp: PreSendInputs) -> list[CheckFinding]:
    soup = _soup(inp.html)
    findings: list[CheckFinding] = []
    for img in soup.find_all("img"):
        if "alt" not in img.attrs:
            src = img.get("src", "(no src)")
            findings.append(CheckFinding(
                code="missing-alt-text",
                severity="ERROR",
                message=f"Image missing alt attribute: {src}",
                location=src,
            ))
    return findings


@register_check
def check_html_lang(inp: PreSendInputs) -> list[CheckFinding]:
    soup = _soup(inp.html)
    html_tag = soup.find("html")
    if html_tag is None or not html_tag.get("lang"):
        return [CheckFinding(
            code="missing-html-lang",
            severity="WARN",
            message="<html> tag missing lang attribute. VoiceOver in non-English locales will mispronounce content.",
        )]
    return []


@register_check
def check_title(inp: PreSendInputs) -> list[CheckFinding]:
    soup = _soup(inp.html)
    title = soup.find("title")
    if title is None or not title.get_text(strip=True):
        return [CheckFinding(
            code="missing-title",
            severity="WARN",
            message="<title> tag missing or empty. Used by 'View in browser' and screen readers.",
        )]
    return []


@register_check
def check_layout_tables_role(inp: PreSendInputs) -> list[CheckFinding]:
    """Layout tables without role=presentation cause screen readers to announce
    rows/columns. Heuristic: if a table has no <th>, no summary attr, and no
    role=presentation, flag it."""
    soup = _soup(inp.html)
    findings: list[CheckFinding] = []
    for table in soup.find_all("table"):
        role = table.get("role", "").lower()
        if role == "presentation":
            continue
        if table.get("summary"):
            continue
        if table.find("th"):
            continue
        findings.append(CheckFinding(
            code="table-missing-role",
            severity="WARN",
            message="Layout <table> without role=\"presentation\" - screen readers will announce row/col counts",
        ))
        break  # one finding per email is enough
    return findings
