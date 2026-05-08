"""ac-builder CLI entry point.

Subcommands:
  - render <md> [--email E1] --out <path>  to render to HTML file (no AC calls)
  - check <html-file>                       to run pre-send validator standalone
  - build-sequence <md> [opts] [--apply]    to run full build pipeline
  - capture-automation <id> --out <json>    to capture template automation
  - list-builds [--since 7d]                to query build manifests
  - send-test <campaign-id> --to <email>    to send V1 campaign_send one-off test
  - verify                                  to check API + Node + MJML versions
  - list-campaigns / get-campaign / delete-campaign / etc. (passthroughs)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ac-builder", description="iDD AC email pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    _add_render_parser(sub)
    _add_check_parser(sub)
    _add_build_parser(sub)
    _add_capture_parser(sub)
    _add_list_builds_parser(sub)
    _add_send_test_parser(sub)
    _add_verify_parser(sub)
    _add_list_campaigns_parser(sub)
    _add_get_campaign_parser(sub)
    _add_delete_campaign_parser(sub)
    _add_list_tags_parser(sub)
    _add_list_automations_parser(sub)
    _add_list_addresses_parser(sub)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return args.func(args) or 0


# --- render ---------------------------------------------------------------

def _add_render_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("render", help="Render a source MD email to HTML (no AC calls)")
    p.add_argument("md", type=Path)
    p.add_argument("--email", help="Single email code to render (default: first)")
    p.add_argument("--theme", default="auto")
    p.add_argument("--footer-mode", default="auto", choices=["launch", "onboarding", "transactional", "auto"])
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(func=_cmd_render)


def _cmd_render(args: argparse.Namespace) -> int:
    from ac_builder.parser import parse_md_file_with_metadata
    from ac_builder.render.compose import ComposeRequest, compose_email
    from ac_builder.render.theme_loader import infer_theme_from_path, load_theme

    _, emails = parse_md_file_with_metadata(args.md)
    if args.email:
        emails = [e for e in emails if e.code == args.email]
    if not emails:
        print(f"No emails matched in {args.md}", file=sys.stderr)
        return 2
    email = emails[0]

    theme_name = args.theme
    if theme_name == "auto":
        theme_name = email.metadata.get("theme") or infer_theme_from_path(args.md) or "lpis"
    theme = load_theme(theme_name)

    footer_mode = args.footer_mode
    if footer_mode == "auto":
        footer_mode = _infer_footer_mode(args.md)

    template_name = {
        "launch": "promo.mjml",
        "onboarding": "onboarding.mjml",
        "transactional": "transactional.mjml",
    }.get(footer_mode, "promo.mjml")

    composed = compose_email(ComposeRequest(
        email=email,
        theme=theme,
        template_name=template_name,
        footer_mode=footer_mode,
    ))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(composed.html)
    print(f"Rendered {email.code} -> {args.out} ({len(composed.html):,} bytes)")
    return 0


def _infer_footer_mode(md_path: Path) -> str:
    s = str(md_path)
    if "emails-onboarding" in s:
        return "onboarding"
    return "launch"


# --- check ---------------------------------------------------------------

def _add_check_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("check", help="Run pre-send validator on a standalone HTML file")
    p.add_argument("html_file", type=Path)
    p.add_argument("--subject", default="(unknown)")
    p.add_argument("--preview", default="")
    p.add_argument("--footer-mode", default="launch", choices=["launch", "onboarding", "transactional"])
    p.set_defaults(func=_cmd_check)


def _cmd_check(args: argparse.Namespace) -> int:
    from ac_builder.validate.pre_send import PreSendInputs, run_checks

    html = args.html_file.read_text()
    report = run_checks(PreSendInputs(
        html=html,
        subject=args.subject,
        preview=args.preview,
        footer_mode=args.footer_mode,
    ))
    for f in report.findings:
        prefix = "ERROR" if f.severity == "ERROR" else "WARN "
        print(f"  [{prefix}] {f.code}: {f.message}")
    print(f"\n{report.error_count} error(s), {report.warning_count} warning(s)")
    return 1 if report.has_errors else 0


# --- build-sequence ------------------------------------------------------

def _add_build_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("build-sequence", help="Build all emails from a source MD")
    p.add_argument("md", type=Path)
    p.add_argument("--list-id", type=int, action="append", dest="list_ids",
                   help="AC list ID to scope messages to. Defaults to AC_DEFAULT_LIST_ID env var. List scope is for compliance footer rendering only - the automation flow determines actual recipients. Repeat flag for multi-list.")
    p.add_argument("--from-name", help="Defaults to AC_DEFAULT_FROM_NAME env var.")
    p.add_argument("--from-email", help="Defaults to AC_DEFAULT_FROM_EMAIL env var.")
    p.add_argument("--reply-to", help="Defaults to AC_DEFAULT_REPLY_TO env var, then --from-email.")
    p.add_argument("--theme", default="auto")
    p.add_argument("--track-link-domain")
    p.add_argument("--footer-mode", default="auto", choices=["launch", "onboarding", "transactional", "auto"])
    p.add_argument("--header-image-url")
    p.add_argument("--header-image-alt")
    p.add_argument("--header-image-link")
    p.add_argument("--utm-campaign")
    p.add_argument("--address-id", type=int, help="Sender physical address ID. Defaults to AC_DEFAULT_ADDRESS_ID env var, then 0 (account default).")
    p.add_argument("--archive", choices=["public", "private"], default="private")
    p.add_argument("--emails", help="Comma-separated email codes to filter")
    p.add_argument("--no-check", action="store_true")
    p.add_argument("--apply", action="store_true", help="Commit changes (default is dry-run)")
    p.set_defaults(func=_cmd_build_sequence)


def _cmd_build_sequence(args: argparse.Namespace) -> int:
    import os
    from dotenv import load_dotenv

    from ac_builder.builder import BuildOptions, build_sequence

    load_dotenv()

    only_codes = [c.strip() for c in args.emails.split(",")] if args.emails else None
    footer_mode = args.footer_mode
    if footer_mode == "auto":
        footer_mode = _infer_footer_mode(args.md)

    # Resolve list_ids: CLI flag > env > error
    list_ids = args.list_ids
    if not list_ids:
        env_list = os.getenv("AC_DEFAULT_LIST_ID")
        if env_list:
            list_ids = [int(env_list)]
    if not list_ids:
        print("ERROR: --list-id is required and AC_DEFAULT_LIST_ID is not set in .env", file=sys.stderr)
        return 2

    # Resolve from-name, from-email, reply-to
    from_name = args.from_name or os.getenv("AC_DEFAULT_FROM_NAME")
    from_email = args.from_email or os.getenv("AC_DEFAULT_FROM_EMAIL")
    reply_to = args.reply_to or os.getenv("AC_DEFAULT_REPLY_TO") or from_email

    if not from_name:
        print("ERROR: --from-name is required and AC_DEFAULT_FROM_NAME is not set in .env", file=sys.stderr)
        return 2
    if not from_email:
        print("ERROR: --from-email is required and AC_DEFAULT_FROM_EMAIL is not set in .env", file=sys.stderr)
        return 2

    address_id = args.address_id
    if address_id is None:
        address_id = int(os.getenv("AC_DEFAULT_ADDRESS_ID", "0"))

    options = BuildOptions(
        from_email=from_email,
        from_name=from_name,
        reply_to=reply_to,
        list_ids=list_ids,
        theme_name=args.theme,
        footer_mode=footer_mode,
        track_link_domain=args.track_link_domain,
        address_id=address_id,
        archive_public=(args.archive == "public"),
        utm_campaign_override=args.utm_campaign,
        header_image_url=args.header_image_url,
        header_image_alt=args.header_image_alt,
        header_image_link=args.header_image_link,
        only_codes=only_codes,
        skip_validation=args.no_check,
        dry_run=not args.apply,
    )

    results = build_sequence(args.md, options)
    has_errors = False
    for r in results:
        suffix = ""
        if r.error:
            suffix = f" - ERROR: {r.error}"
            has_errors = True
        print(f"  [{r.action:>8}] {r.email_code:<6} {r.target_name}{suffix}")

    # When AC copies a draft into an automation Send Email step, the copy keeps
    # subject/preheader/body but NOT the Google Analytics Campaign Name. Print
    # the value so Tim can paste it onto each automation copy.
    if args.apply and not has_errors:
        ga_name = _resolve_utm_campaign(args.md, args.utm_campaign)
        if ga_name:
            print()
            print(f"NOTE: when adding these campaigns to automation Send Email steps, AC")
            print(f"creates a COPY that keeps subject/preheader/body but DROPS the Google")
            print(f"Analytics Campaign Name. Set it manually on each copy:")
            print(f"  Google Analytics Campaign Name: {ga_name}")

    return 1 if has_errors else 0


def _resolve_utm_campaign(md_path: Path, override: str | None) -> str | None:
    """Read the source MD's Campaign name field, honoring CLI override."""
    if override:
        return override
    try:
        from ac_builder.parser import parse_md_file_with_metadata
        meta, _ = parse_md_file_with_metadata(md_path)
        return meta.campaign_name or None
    except Exception:  # noqa: BLE001
        return None


# --- capture-automation, list-builds, send-test, verify ------------------

def _add_capture_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("capture-automation", help="Capture an automation as a template fixture")
    p.add_argument("automation_id", type=int)
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(func=_cmd_capture)


def _cmd_capture(args: argparse.Namespace) -> int:
    from ac_builder.api.automations_v3 import get_automation
    from ac_builder.api.v3_client import ACClient
    from ac_builder.fixtures.automations._capture_helper import save_template

    client = ACClient()
    response = get_automation(client, args.automation_id)
    save_template(response.get("automation", response), args.out)
    print(f"Captured automation {args.automation_id} -> {args.out}")
    return 0


def _add_list_builds_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("list-builds", help="List recent build manifests")
    p.add_argument("--since", default="7d", help="Time window e.g. '7d', '30d'")
    p.set_defaults(func=_cmd_list_builds)


def _cmd_list_builds(args: argparse.Namespace) -> int:
    from ac_builder.manifest import list_manifests

    days_str = args.since.rstrip("d") if args.since.endswith("d") else args.since
    days = int(days_str) if days_str else 7
    paths = list_manifests(since_days=days)
    for p in paths:
        with p.open() as f:
            data = json.load(f)
        print(f"{data['started_at']:30} {data['theme']:8} {data['source_md']} ({len(data.get('results', []))} emails)")
    return 0


def _add_send_test_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("send-test", help="One-off test send via V1 campaign_send")
    p.add_argument("campaign_id", type=int)
    p.add_argument("--to", required=True)
    p.set_defaults(func=_cmd_send_test)


def _cmd_send_test(args: argparse.Namespace) -> int:
    from ac_builder.api.campaigns_v1 import campaign_send
    from ac_builder.api.campaigns_v3 import get_campaign
    from ac_builder.api.v1_client import ACV1Client
    from ac_builder.api.v3_client import ACClient

    v3 = ACClient()
    info = get_campaign(v3, args.campaign_id)
    message_id = info.get("campaign", {}).get("message_id")
    if not message_id:
        print(f"Campaign {args.campaign_id} has no message_id", file=sys.stderr)
        return 2

    v1 = ACV1Client()
    campaign_send(v1, email=args.to, campaign_id=args.campaign_id, message_id=int(message_id))
    print(f"Sent campaign {args.campaign_id} to {args.to}")
    return 0


def _add_verify_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("verify", help="Verify ac-builder pipeline (AC API, MJML, themes)")
    p.add_argument(
        "--themes-only",
        action="store_true",
        help="Skip AC API and MJML checks; only validate theme JSONs against schema.",
    )
    p.set_defaults(func=_cmd_verify)


def _cmd_verify(args: argparse.Namespace) -> int:
    from ac_builder import __version__
    from ac_builder.render.theme_loader import discover_theme_names, load_theme

    print(f"ac-builder {__version__}")

    if not args.themes_only:
        from ac_builder.api.v3_client import ACClient
        from ac_builder.render.mjml_runner import mjml_version

        try:
            print(f"mjml: {mjml_version()}")
        except Exception as exc:  # noqa: BLE001
            print(f"mjml: ERROR - {exc}")
            return 1

        try:
            client = ACClient()
            client.get("users/me")
            print(f"AC API: OK ({client.api_url})")
        except Exception as exc:  # noqa: BLE001
            print(f"AC API: ERROR - {exc}")
            return 1

    # Theme validation runs in both modes. Discover themes from the active
    # themes directory (honours AC_BUILDER_THEMES_DIR). An empty directory
    # produces 0 themes validated and is not a failure.
    theme_names = discover_theme_names()
    if not theme_names:
        print("themes: 0 found (nothing to validate)")
    else:
        for name in theme_names:
            try:
                load_theme(name)
                print(f"theme {name}: OK")
            except Exception as exc:  # noqa: BLE001
                print(f"theme {name}: ERROR - {exc}")
                return 1
    return 0


# --- inspection passthroughs ---------------------------------------------

def _add_list_campaigns_parser(sub):
    p = sub.add_parser("list-campaigns")
    p.add_argument("--name")
    p.add_argument("--type")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=_cmd_list_campaigns)


def _cmd_list_campaigns(args):
    from ac_builder.api import campaigns_v3
    from ac_builder.api.v3_client import ACClient
    client = ACClient()
    filters: dict[str, Any] = {}
    if args.name:
        filters["name"] = args.name
    if args.type:
        filters["type"] = args.type
    for i, c in enumerate(campaigns_v3.list_campaigns(client, **filters)):
        if i >= args.limit:
            break
        print(f"  {c['id']:>6}  {c.get('name', '(no name)')}")


def _add_get_campaign_parser(sub):
    p = sub.add_parser("get-campaign")
    p.add_argument("campaign_id", type=int)
    p.set_defaults(func=_cmd_get_campaign)


def _cmd_get_campaign(args):
    from ac_builder.api import campaigns_v3
    from ac_builder.api.v3_client import ACClient
    client = ACClient()
    print(json.dumps(campaigns_v3.get_campaign(client, args.campaign_id), indent=2))


def _add_delete_campaign_parser(sub):
    p = sub.add_parser("delete-campaign")
    p.add_argument("campaign_id", type=int)
    p.add_argument("--yes", action="store_true", required=True, help="Confirmation flag")
    p.set_defaults(func=_cmd_delete_campaign)


def _cmd_delete_campaign(args):
    from ac_builder.api import campaigns_v3
    from ac_builder.api.v3_client import ACClient
    client = ACClient()
    response = campaigns_v3.delete_campaign(client, args.campaign_id)
    print(json.dumps(response, indent=2))


def _add_list_tags_parser(sub):
    p = sub.add_parser("list-tags")
    p.add_argument("--search")
    p.set_defaults(func=_cmd_list_tags)


def _cmd_list_tags(args):
    from ac_builder.api.v3_client import ACClient
    client = ACClient()
    params = {"search": args.search} if args.search else {}
    for tag in client.paginate("tags", "tags", params=params):
        print(f"  {tag['id']:>6}  {tag.get('tag', '(no name)')}")


def _add_list_automations_parser(sub):
    p = sub.add_parser("list-automations")
    p.set_defaults(func=_cmd_list_automations)


def _cmd_list_automations(args):
    from ac_builder.api import automations_v3
    from ac_builder.api.v3_client import ACClient
    client = ACClient()
    for a in automations_v3.list_automations(client):
        print(f"  {a['id']:>6}  {a.get('name', '(no name)')}  status={a.get('status')}")


def _add_list_addresses_parser(sub):
    p = sub.add_parser("list-addresses")
    p.set_defaults(func=_cmd_list_addresses)


def _cmd_list_addresses(args):
    from ac_builder.api import addresses_v3
    from ac_builder.api.v3_client import ACClient
    client = ACClient()
    for addr in addresses_v3.list_addresses(client):
        print(f"  {addr['id']:>6}  {addr.get('company', '')} - {addr.get('address_1', '')}, {addr.get('city', '')}")


if __name__ == "__main__":
    sys.exit(main())
