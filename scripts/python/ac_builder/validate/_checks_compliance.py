"""Compliance, size, and image-src checks for pre_send."""
from __future__ import annotations

import re

from ac_builder.validate.pre_send import CheckFinding, PreSendInputs, register_check

_HTML_SIZE_ERROR_BYTES = 100_000
_HTML_SIZE_WARN_BYTES = 85_000

_NOT_INTERESTED_URL_PATTERN = "/not-interested/"


@register_check
def check_unsubscribe_link(inp: PreSendInputs) -> list[CheckFinding]:
    if inp.footer_mode == "onboarding":
        if "%UNSUBSCRIBELINK%" not in inp.html:
            return [CheckFinding(
                code="missing-unsubscribe-link-warn",
                severity="WARN",
                message="No %UNSUBSCRIBELINK% token in onboarding email - AC will append default footer",
            )]
        return []
    if "%UNSUBSCRIBELINK%" not in inp.html:
        return [CheckFinding(
            code="missing-unsubscribe-link",
            severity="ERROR",
            message="No %UNSUBSCRIBELINK% token in HTML. AC will append default footer; CAN-SPAM and Yahoogle require explicit unsubscribe.",
        )]
    return []


@register_check
def check_sender_info(inp: PreSendInputs) -> list[CheckFinding]:
    if inp.footer_mode == "onboarding":
        if "%SENDER-INFO%" not in inp.html and "%SENDER-INFO-SINGLELINE%" not in inp.html:
            return [CheckFinding(
                code="missing-sender-info-warn",
                severity="WARN",
                message="No %SENDER-INFO% or %SENDER-INFO-SINGLELINE% token in onboarding email",
            )]
        return []
    if "%SENDER-INFO%" not in inp.html and "%SENDER-INFO-SINGLELINE%" not in inp.html:
        return [CheckFinding(
            code="missing-sender-info",
            severity="ERROR",
            message="No %SENDER-INFO% (or %SENDER-INFO-SINGLELINE%) token in HTML. CAN-SPAM requires sender physical address.",
        )]
    return []


@register_check
def check_html_size(inp: PreSendInputs) -> list[CheckFinding]:
    size = len(inp.html.encode("utf-8"))
    if size > _HTML_SIZE_ERROR_BYTES:
        return [CheckFinding(
            code="html-size-error",
            severity="ERROR",
            message=f"HTML size {size:,} bytes exceeds Gmail 100KB clip threshold",
        )]
    if size > _HTML_SIZE_WARN_BYTES:
        return [CheckFinding(
            code="html-size-warn",
            severity="WARN",
            message=f"HTML size {size:,} bytes is within 15KB of Gmail 100KB clip threshold",
        )]
    return []


_HTTP_SRC_RE = re.compile(r'<img[^>]*\bsrc\s*=\s*["\']http://', re.IGNORECASE)


@register_check
def check_http_image_src(inp: PreSendInputs) -> list[CheckFinding]:
    if _HTTP_SRC_RE.search(inp.html):
        return [CheckFinding(
            code="http-image-src",
            severity="ERROR",
            message="One or more <img> tags use http:// (not https://). Yahoo and Microsoft block insecure image sources.",
        )]
    return []


@register_check
def check_onboarding_has_not_interested(inp: PreSendInputs) -> list[CheckFinding]:
    """Per feedback_onboarding_no_opt_out.md: onboarding emails MUST NOT include the not-interested URL."""
    if inp.footer_mode == "onboarding" and _NOT_INTERESTED_URL_PATTERN in inp.html:
        return [CheckFinding(
            code="onboarding-has-not-interested",
            severity="ERROR",
            message="Onboarding email contains a /not-interested/ URL. Per project rule, paying customers do not receive Not Interested CTAs.",
        )]
    return []


@register_check
def check_launch_has_not_interested(inp: PreSendInputs) -> list[CheckFinding]:
    """Launch emails MUST contain the /not-interested/ opt-out link.

    That link is authored as the final element of every launch email body and is
    never injected by the template, so its absence from the rendered HTML means
    the body was cut short before render. This is the exact failure mode behind
    the E6/E7 truncation (an in-body '### ' heading silently ended body
    extraction). Erroring here aborts the build instead of pushing a half-email.
    """
    if inp.footer_mode == "launch" and _NOT_INTERESTED_URL_PATTERN not in inp.html:
        return [CheckFinding(
            code="launch-missing-not-interested",
            severity="ERROR",
            message=(
                "Launch email is missing the /not-interested/ opt-out link, which is "
                "always the final element of a launch body. Strong signal the body was "
                "truncated (e.g. an in-body '### ' heading ended the body during parsing)."
            ),
        )]
    return []
