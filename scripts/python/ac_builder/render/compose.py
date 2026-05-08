"""End-to-end email composition: EmailDef + theme to final HTML.

Pipeline:
  1. md_to_mjml_body(email.body_md, theme) -> MJML body fragment
  2. Jinja2 renders templates/<template_name> with body fragment + theme + meta
  3. mjml_runner.compile_mjml(...) -> final HTML

Returns ComposeResult containing .html plus metadata recorded into the build
manifest (template name, theme name, template version, mjml version, preheader,
subject).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ac_builder.parser import EmailDef
from ac_builder.render.md_to_mjml_body import md_to_mjml_body
from ac_builder.render.mjml_runner import compile_mjml, mjml_version
from ac_builder.render.theme_loader import ThemeData

AC_BUILDER_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = AC_BUILDER_ROOT / "templates"


def pick_banner_for_email(email_code: str, banner_urls: list[str]) -> str:
    """Deterministically pick one banner URL for an email based on its code.

    Cycles through banners by extracting the first numeric run from the code:
    E1 -> banner_urls[0], E2 -> banner_urls[1], E3 -> banner_urls[2], E4 -> banner_urls[0], ...
    LPIS-OB-1 -> banner_urls[0], LPIS-OB-2 -> banner_urls[1], etc.
    Codes without a number fall back to a stable hash.
    """
    if not banner_urls:
        raise ValueError("banner_urls cannot be empty")
    if len(banner_urls) == 1:
        return banner_urls[0]
    m = re.search(r"(\d+)", email_code)
    if m:
        idx = (int(m.group(1)) - 1) % len(banner_urls)
    else:
        idx = abs(hash(email_code)) % len(banner_urls)
    return banner_urls[idx]


def _resolve_banner_url(req_header_url: str | None, theme: ThemeData, email_code: str) -> str | None:
    """Pick the banner for this email: explicit override > theme.banner_urls rotation > theme.banner_url."""
    if req_header_url:
        return req_header_url
    banner_urls = theme.branding.get("banner_urls")
    if isinstance(banner_urls, list) and banner_urls:
        return pick_banner_for_email(email_code, banner_urls)
    return theme.branding.get("banner_url")


@dataclass
class ComposeRequest:
    """Inputs to compose_email()."""
    email: EmailDef
    theme: ThemeData
    template_name: str  # e.g. "promo.mjml"
    footer_mode: str    # "launch" | "onboarding" | "transactional"
    header_image_url: str | None = None
    header_image_alt: str | None = None
    header_image_link: str | None = None


@dataclass
class ComposeResult:
    """Outputs from compose_email()."""
    html: str
    subject: str
    preheader: str
    template_name: str
    template_version: str
    theme_name: str
    mjml_version: str
    warnings: list[str] = field(default_factory=list)


def _read_template_version() -> str:
    path = TEMPLATES_DIR / "_version.txt"
    if path.exists():
        return path.read_text().strip()
    return "0.0.0"


def _jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def compose_email(req: ComposeRequest) -> ComposeResult:
    """Render an EmailDef + theme into final HTML.

    Raises:
        MjmlError: if the MJML fails to compile (e.g., template syntax error).
    """
    body_mjml = md_to_mjml_body(req.email.body_md, theme=req.theme)

    # Resolve banner: explicit override wins; otherwise rotate through theme.banner_urls
    # by email code so a 20-email sequence cycles through the 3 banners.
    resolved_banner = _resolve_banner_url(req.header_image_url, req.theme, req.email.code)

    env = _jinja_env()
    tmpl = env.get_template(req.template_name)

    rendered_mjml = tmpl.render(
        theme={
            "name": req.theme.name,
            "fonts": req.theme.fonts,
            "colors": req.theme.colors,
            "branding": req.theme.branding,
            "urls": req.theme.urls,
        },
        title=f"{req.email.code} - {req.email.title}",
        preheader_text=req.email.preview_text or "",
        body_mjml=body_mjml,
        footer_mode=req.footer_mode,
        header_image_url=resolved_banner,
        header_image_alt=req.header_image_alt,
        header_image_link=req.header_image_link,
    )

    result = compile_mjml(rendered_mjml, validate=True)

    return ComposeResult(
        html=result.html,
        subject=req.email.primary_subject or req.email.title,
        preheader=req.email.preview_text or "",
        template_name=req.template_name,
        template_version=_read_template_version(),
        theme_name=req.theme.name,
        mjml_version=mjml_version(),
        warnings=result.warnings,
    )
