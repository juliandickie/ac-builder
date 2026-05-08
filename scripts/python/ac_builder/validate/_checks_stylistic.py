"""Stylistic / length / contrast checks for pre_send."""
from __future__ import annotations

import re

from ac_builder.validate.pre_send import CheckFinding, PreSendInputs, register_check


@register_check
def check_subject_length(inp: PreSendInputs) -> list[CheckFinding]:
    if len(inp.subject) > 33:
        return [CheckFinding(
            code="subject-mobile-truncation",
            severity="WARN",
            message=f"Subject is {len(inp.subject)} chars; mobile preview shows ~33",
        )]
    return []


@register_check
def check_preview_length(inp: PreSendInputs) -> list[CheckFinding]:
    if len(inp.preview) > 85:
        return [CheckFinding(
            code="preview-too-long",
            severity="WARN",
            message=f"Preview text is {len(inp.preview)} chars; iOS visibility caps at ~85",
        )]
    return []


@register_check
def check_cta_contrast(inp: PreSendInputs) -> list[CheckFinding]:
    if not inp.theme_cta_bg or not inp.theme_cta_text:
        return []
    ratio = _contrast_ratio(inp.theme_cta_bg, inp.theme_cta_text)
    if ratio < 4.5:
        return [CheckFinding(
            code="cta-low-contrast",
            severity="WARN",
            message=f"CTA contrast ratio {ratio:.2f}:1 below WCAG AA (4.5:1) for {inp.theme_cta_text} on {inp.theme_cta_bg}",
        )]
    return []


_FIRSTNAME_BARE_RE = re.compile(r"%FIRSTNAME%(?!\|)")


@register_check
def check_firstname_modifier(inp: PreSendInputs) -> list[CheckFinding]:
    if _FIRSTNAME_BARE_RE.search(inp.html):
        return [CheckFinding(
            code="firstname-missing-modifier",
            severity="WARN",
            message="Bare %FIRSTNAME% found - convention is %FIRSTNAME|TITLECASE% to normalize casing",
        )]
    return []


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance formula."""
    def _channel(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = (_channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(bg_hex: str, fg_hex: str) -> float:
    """WCAG contrast ratio between two hex colors."""
    l1 = _relative_luminance(_hex_to_rgb(bg_hex))
    l2 = _relative_luminance(_hex_to_rgb(fg_hex))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)
