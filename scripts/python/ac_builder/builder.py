"""Phase 4 build orchestrator: source MD + theme to AC campaign drafts.

Per-email flow:
  1. Parse source MD to EmailDef
  2. Resolve theme (CLI flag, per-email **Theme:**, or filename inference)
  3. Compose: md_to_mjml_body to Jinja to MJML CLI to final HTML
  4. Pre-send validate
  5. Render plain text
  6. Idempotency: search existing campaigns by name
  7a. UPDATE path: V3 PUT message + campaign metadata
  7b. CREATE path: V1 message_add to V1 campaign_create
  8. Record manifest entry

Returns a list of BuildResult, one per email. Click-action automations are
NOT created by this pipeline - AC's V3 API does not support POST /automations
on this account (returns 405). Configure click actions manually per campaign
in AC UI; see ac_builder/fixtures/automations/_AC_API_LIMITATIONS.md for the
investigation and link-action-maps/ for which tags to apply per link.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ac_builder import __version__
from ac_builder.api import campaigns_v3, messages_v3
from ac_builder.api.campaigns_v1 import campaign_create
from ac_builder.api.messages_v1 import message_add
from ac_builder.api.v1_client import ACV1Client
from ac_builder.api.v3_client import ACClient
from ac_builder.manifest import BuildManifest, EmailBuildRecord, ManifestStore
from ac_builder.parser import EmailDef, parse_md_file_with_metadata
from ac_builder.render.compose import ComposeRequest, compose_email
from ac_builder.render.theme_loader import infer_theme_from_path, load_theme
from ac_builder.text_renderer import html_to_text
from ac_builder.validate.pre_send import PreSendInputs, run_checks

logger = logging.getLogger(__name__)


@dataclass
class BuildOptions:
    from_email: str
    from_name: str
    reply_to: str
    list_ids: list[int]
    theme_name: str = "auto"
    footer_mode: str = "launch"
    track_link_domain: str | None = None
    address_id: int = 0
    archive_public: bool = False
    utm_campaign_override: str | None = None
    header_image_url: str | None = None
    header_image_alt: str | None = None
    header_image_link: str | None = None
    only_codes: list[str] | None = None
    skip_validation: bool = False
    dry_run: bool = True
    template_name_override: str | None = None


@dataclass
class BuildResult:
    email_code: str
    target_name: str
    action: str
    campaign_id: int | None = None
    message_id: int | None = None
    error: str | None = None
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    automations_created: list[dict[str, Any]] = field(default_factory=list)
    html_size_bytes: int = 0


def build_sequence(source_md: str | Path, options: BuildOptions) -> list[BuildResult]:
    """Build (create-or-update) all emails from a source MD."""
    source_path = Path(source_md)
    sequence_metadata, emails = parse_md_file_with_metadata(source_path)
    if options.only_codes:
        wanted = set(options.only_codes)
        emails = [e for e in emails if e.code in wanted]

    utm_campaign = options.utm_campaign_override or sequence_metadata.campaign_name

    sequence_theme_name = options.theme_name
    if sequence_theme_name == "auto":
        inferred = infer_theme_from_path(source_path)
        if inferred:
            sequence_theme_name = inferred

    template_name = options.template_name_override or _template_for_footer_mode(options.footer_mode)

    if options.dry_run:
        return [
            BuildResult(email_code=e.code, target_name=e.full_name, action="dry-run")
            for e in emails
        ]

    v3 = ACClient()
    v1 = ACV1Client()

    manifest = BuildManifest(
        source_md=str(source_path),
        theme=sequence_theme_name,
        template_used=template_name,
        template_version=_read_template_version(),
        mjml_version=_safe_mjml_version(),
        ac_builder_version=__version__,
        footer_mode=options.footer_mode,
        command_line=" ".join(["ac-builder", "build-sequence", str(source_path)]),
    )
    manifest.fingerprint_source(source_path)

    existing_by_name: dict[str, dict[str, Any]] = {}
    for c in campaigns_v3.list_campaigns(v3):
        if name := c.get("name"):
            existing_by_name[name] = c

    results: list[BuildResult] = []
    for email in emails:
        try:
            result = _build_one(
                email=email,
                source_path=source_path,
                options=options,
                template_name=template_name,
                sequence_theme_name=sequence_theme_name,
                utm_campaign=utm_campaign,
                v3=v3,
                v1=v1,
                existing_by_name=existing_by_name,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Build failed for %s", email.code)
            result = BuildResult(
                email_code=email.code,
                target_name=email.full_name,
                action="error",
                error=str(exc),
            )
        results.append(result)
        manifest.add_result(_to_manifest_record(email, result))

    ManifestStore().write(manifest)
    return results


def _template_for_footer_mode(footer_mode: str) -> str:
    return {
        "launch": "promo.mjml",
        "onboarding": "onboarding.mjml",
        "transactional": "transactional.mjml",
    }.get(footer_mode, "promo.mjml")


def _read_template_version() -> str:
    path = Path(__file__).resolve().parent.parent / "templates" / "_version.txt"
    return path.read_text().strip() if path.exists() else "0.0.0"


def _safe_mjml_version() -> str:
    try:
        from ac_builder.render.mjml_runner import mjml_version
        return mjml_version()
    except Exception:  # noqa: BLE001
        return "unknown"


def _build_one(
    *,
    email: EmailDef,
    source_path: Path,
    options: BuildOptions,
    template_name: str,
    sequence_theme_name: str,
    utm_campaign: str,
    v3: ACClient,
    v1: ACV1Client,
    existing_by_name: dict[str, dict[str, Any]],
) -> BuildResult:
    """Build (create-or-update) one email."""
    theme_name = email.metadata.get("theme") or sequence_theme_name
    theme = load_theme(theme_name)

    request = ComposeRequest(
        email=email,
        theme=theme,
        template_name=template_name,
        footer_mode=options.footer_mode,
        header_image_url=options.header_image_url,
        header_image_alt=options.header_image_alt,
        header_image_link=options.header_image_link,
    )
    composed = compose_email(request)

    validation_errors: list[str] = []
    validation_warnings: list[str] = []
    if not options.skip_validation:
        report = run_checks(PreSendInputs(
            html=composed.html,
            subject=composed.subject,
            preview=composed.preheader,
            footer_mode=options.footer_mode,
            theme_cta_bg=theme.colors.get("cta_bg"),
            theme_cta_text=theme.colors.get("cta_text"),
        ))
        if report.has_errors:
            return BuildResult(
                email_code=email.code,
                target_name=email.full_name,
                action="error",
                error=f"pre-send validation failed: {report.error_count} errors",
                validation_errors=[f"{f.code}: {f.message}" for f in report.errors],
                validation_warnings=[f"{f.code}: {f.message}" for f in report.warnings],
                html_size_bytes=len(composed.html.encode("utf-8")),
            )
        validation_errors = [f"{f.code}: {f.message}" for f in report.errors]
        validation_warnings = [f"{f.code}: {f.message}" for f in report.warnings]

    plain_text = html_to_text(composed.html)

    target_name = email.full_name
    existing = existing_by_name.get(target_name)

    if existing:
        campaign_id = int(existing["id"])
        message_id_raw = existing.get("message_id")
        if not message_id_raw:
            full = campaigns_v3.get_campaign(v3, campaign_id)
            message_id_raw = full.get("campaign", {}).get("message_id")
        message_id = int(message_id_raw) if message_id_raw else None

        if message_id:
            messages_v3.update_message(
                v3,
                message_id,
                subject=composed.subject,
                preheader_text=composed.preheader,
                html=composed.html,
                text=plain_text,
            )
        try:
            campaigns_v3.update_campaign(
                v3,
                campaign_id,
                analytics_campaign_name=utm_campaign,
                addressid=options.address_id,
                public=int(options.archive_public),
            )
        except Exception:  # noqa: BLE001
            pass
        action = "updated"
    else:
        message_id = message_add(
            v1,
            subject=composed.subject,
            fromemail=options.from_email,
            fromname=options.from_name,
            reply2=options.reply_to,
            html=composed.html,
            text=plain_text,
            list_ids=options.list_ids,
        )
        # V1 message_add silently drops preheader_text. Set it via V3 PUT.
        if composed.preheader:
            try:
                messages_v3.update_message(v3, message_id, preheader_text=composed.preheader)
            except Exception:  # noqa: BLE001
                logger.warning("Could not set preheader on new message %s", message_id)
        campaign_id = campaign_create(
            v1,
            name=target_name,
            message_id=message_id,
            list_ids=options.list_ids,
            track_links="all",
            track_link_domain=options.track_link_domain,
            address_id=options.address_id,
            public=options.archive_public,
        )
        if utm_campaign:
            try:
                campaigns_v3.update_campaign(v3, campaign_id, analytics_campaign_name=utm_campaign)
            except Exception:  # noqa: BLE001
                pass
        action = "created"

    return BuildResult(
        email_code=email.code,
        target_name=target_name,
        action=action,
        campaign_id=campaign_id,
        message_id=message_id,
        validation_errors=validation_errors,
        validation_warnings=validation_warnings,
        html_size_bytes=len(composed.html.encode("utf-8")),
    )


def _to_manifest_record(email: EmailDef, result: BuildResult) -> EmailBuildRecord:
    return EmailBuildRecord(
        email_code=email.code,
        campaign_name=result.target_name,
        campaign_id=result.campaign_id,
        message_id=result.message_id,
        action=result.action,
        html_size_bytes=result.html_size_bytes,
        error=result.error,
        validation_errors=result.validation_errors,
        validation_warnings=result.validation_warnings,
        automations_created=result.automations_created,
    )
