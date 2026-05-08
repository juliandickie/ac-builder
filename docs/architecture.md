# Architecture

Contributor-facing internals overview for ac-builder. If you are looking for how to *use* the tool, start with `README.md` or the user-facing skills under `skills/`. This doc explains how the pieces fit together so you can navigate the code, extend it, or fork it.

## How a build flows

```
Source MD (.md file)
  -> parser.py (parse_md_file_with_metadata)
  -> EmailDef objects with code, subject, preview, body_md
  -> theme_loader.py resolves theme JSON (project > user > examples chain)
  -> compose.py: ComposeRequest -> Jinja2 templates + theme + body_md -> MJML source
  -> mjml_runner.py shells out to MJML CLI -> bulletproof HTML
  -> validate/pre_send.py runs checks -> ERROR / WARN findings
  -> if PASS: V1 API (campaigns_v1.py + messages_v1.py) creates campaign
  -> manifest.py records build to .build-manifests/YYYY-MM-DD/<sequence>-<HHMMSS>.json
```

Each step is a single responsibility module. `builder.py` is the orchestrator that wires them together; everything else can be exercised in isolation, which is how the test suite under `scripts/python/tests/` operates.

The same flow runs for both create and update paths. The branching point is in `_build_one()` after validation: if a campaign with the target name already exists, the code takes the V3 PUT path; otherwise it takes the V1 from-scratch creation path.

## V1 vs V3 API split

ActiveCampaign has two parallel APIs. We use both, deliberately, for different jobs.

### V1 used for

- Campaign creation. The atomic flow is `message_add` (V1) -> `campaign_create` (V1) -> link via `campaign_message_id`. This is the one path AC documents as the supported way to create a campaign with custom HTML.
- Setting `htmlconstructor=html` on creation so AC treats our HTML as the authoritative source rather than trying to fetch from a URL.

### V3 used for

- Read operations: `list_campaigns`, `get_campaign`, `get_message`, `list_tags`, etc.
- Updates on existing campaigns and messages: `PUT /campaigns/{id}` for metadata, `PUT /messages/{id}` for content tweaks.
- Tags, lists, automations, contacts, addresses, custom fields, link-id and click-action operations - all the granular stuff.
- Setting `preheader_text` after V1 message creation, because V1 `message_add` silently drops that field.

### Why split

V1's campaign creation is the documented happy path and produces messages that the modern editor cannot silently break (see `ed-version-gotcha.md`). V3 is more granular and ergonomic for everything else. The Phase 4 design (April 2026) replaced an earlier Phase 1-3 V3 master-and-edit pattern - that pattern fought AC's modern editor html/text reversion and was abandoned in favour of V1 from-scratch creation. The legacy V3 master-and-edit code is preserved under `legacy/` in the iDD project repo for archival reference.

## Why MJML

Cross-client HTML email is genuinely hard. Outlook (Word renderer), Gmail web, Gmail mobile, iOS Mail, Outlook web, Apple Mail desktop, Outlook for Mac, and dark mode in any of them all behave differently. Hand-writing tables, conditional comments, VML buttons, dark mode meta tags, and inlined CSS for every email is a non-trivial maintenance burden.

MJML compiles to HTML that handles all of this:

- Ghost tables for Outlook column rendering
- VML-fallback buttons for Outlook
- Dark mode meta tags
- Inlined CSS via `juice` (built into MJML)
- Mobile-responsive without media-query gymnastics

We invoke the MJML CLI via `render/mjml_runner.py` rather than a Python port, because the JS implementation is the upstream reference and ports lag. Node 20+ is a hard prerequisite for v0.5; users install it once. MJML CLI version is detected at runtime and recorded in the build manifest, so manifests are reproducible if you pin the same MJML version in your fork.

## Why Jinja2 on top of MJML

MJML doesn't natively support per-theme color tokens. We need `{{ theme.colors.primary }}` style placeholders so a single MJML template renders differently for LPIS vs ASIMR vs IIDF.

The `render/compose.py` flow:

1. Parse the email's body markdown into MJML body fragments (`md_to_mjml_body.py` - sections, paragraphs, mj-buttons, mj-images).
2. Load the chosen theme JSON via `theme_loader.py`.
3. Render the chosen template (e.g. `promo.mjml`) with Jinja2, substituting `{{ theme.* }}`, `{{ subject }}`, `{{ preheader }}`, `{{ body_mjml }}`, and footer/header context.
4. Compile the resulting MJML source string with the MJML CLI to final HTML.

Each theme JSON populates a single render context object: theme + email + body_md. Templates stay theme-agnostic; themes stay template-agnostic. To add a new theme, you write a JSON file. To add a new template, you write an `.mjml` file with `{{ }}` placeholders.

## Why uv run vs pip

The plugin shells out to the Python interpreter via `uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ...`. Reasons:

- **uv handles venv creation transparently.** First invocation creates the venv and installs dependencies; subsequent invocations are near-instant. No manual `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` ritual.
- **No bootstrap script needed inside the plugin.** Skills can call `uv run` directly without sniffing for an existing venv or installer state.
- **10x faster than pip.** Resolves and installs in seconds.
- **Hard prerequisite for v0.5.** Users install `uv` once via the documented curl one-liner; everything else is automatic.

If you're contributing and prefer pip, you can still `cd scripts/python && pip install -e .[dev]` into your own venv - the project metadata is plain `pyproject.toml`. The `uv run` wrapping is only how skills invoke the CLI; tests and ad-hoc scripts work with any standard Python venv setup.

## File responsibilities

Top-level modules under `scripts/python/ac_builder/`:

| Module | Purpose |
|---|---|
| `parser.py` | Source MD parsing. Extracts `EmailDef`s (code, subject, preview, body_md, metadata) and `SequenceMetadata` from a single `.md` file. |
| `builder.py` | High-level orchestration. `build_sequence()` is the entry point for the `building-sequences` skill; idempotent create-or-update per email. |
| `cli.py` | argparse entry point. Subcommands include `verify`, `build-sequence`, plus listing/inspection helpers. |
| `manifest.py` | Build manifest writing. Records source MD fingerprint, theme, template version, MJML version, ac-builder version, and per-email outcomes to `.build-manifests/YYYY-MM-DD/<sequence>-<HHMMSS>.json`. |
| `text_renderer.py` | HTML to plaintext fallback for the `text` field. AC requires both html and text on every campaign. |
| `config.py` | Layered credential resolution: env vars > project `.env` > user `.env` > shell environment. |
| `api/` | V1 + V3 client wrappers + endpoint helpers. See split below. |
| `render/` | MJML pipeline: compose, theme_loader, md_to_mjml_body, mjml_runner. |
| `validate/` | Pre-send validator: compliance tokens, alt text on images, http(s) image URLs, subject length, color contrast. ERROR findings block the build; WARN findings get logged in the manifest. |

### `api/` subpackage

| File | Purpose |
|---|---|
| `v1_client.py` | `ACV1Client` - thin wrapper around `requests` for V1 endpoints (`/admin/api.php?api_action=...`). |
| `v3_client.py` | `ACClient` - wrapper for V3 endpoints (`/api/3/...`). Reads credentials via `config.py`. |
| `campaigns_v1.py` | `campaign_create()` - V1 atomic campaign creation. |
| `messages_v1.py` | `message_add()` - V1 message creation. |
| `campaigns_v3.py` | `list_campaigns`, `get_campaign`, `update_campaign`, `delete_campaign`. |
| `messages_v3.py` | `get_message`, `update_message`. **Note: `update_message` does not pre-check `ed_version` - the caller is responsible.** See `ed-version-gotcha.md`. |
| `tags_v3.py` | `list_tags`, `get_tag`, `create_tag`. |
| `lists_v3.py` | `list_lists`, `get_list`. |
| `automations_v3.py` | `list_automations`, `get_automation`. POST is not supported on this account (returns 405); link-action automations are configured via UI templates captured by the `capturing-link-actions` skill. |
| `addresses_v3.py` | `list_addresses` for resolving the `addressid` required by AC for compliance. |
| `fields_v3.py` | `list_fields` for inspecting custom contact fields. |

### `render/` subpackage

| File | Purpose |
|---|---|
| `compose.py` | `ComposeRequest` -> compiled HTML. Wires together theme, template, body, header, footer. |
| `theme_loader.py` | Resolves a theme name into a loaded theme dict. Search order: project `themes/<name>.json` > user `~/.ac-builder/themes/<name>.json` > examples bundled with the package. |
| `md_to_mjml_body.py` | Renders body markdown into MJML body fragments (`<mj-section>`, `<mj-text>`, `<mj-button>`, etc.). Theme-aware - reads color tokens from the theme. |
| `mjml_runner.py` | Shells out to the `mjml` CLI. Captures version for the manifest. |

### `validate/` subpackage

| File | Purpose |
|---|---|
| `pre_send.py` | `run_checks()` - top-level validator. Returns a report with ERROR / WARN findings. |
| `_checks_compliance.py` | Required compliance tokens in footers (unsubscribe link, physical address). |
| `_checks_accessibility.py` | Alt text on images, color contrast vs theme CTA tokens. |
| `_checks_stylistic.py` | Subject length, http(s) image protocol, etc. |
| `mjml_lint.py` | Optional MJML-output structural linting. |

## Testing

`scripts/python/tests/` contains pytest tests. Run via `uv run --directory scripts/python pytest`. Fixtures under `scripts/python/ac_builder/fixtures/` include sample source MD, sample theme JSON, and captured automation JSON used by the `capturing-link-actions` skill.

The smoke-test suite (`tests/test_smoke.py` style) covers the parser -> compose -> validate path with no AC API calls. The integration-test suite (separate) hits a sandbox AC account; not run in CI.

## Extending

- **New theme:** drop a JSON file under `themes/` matching the schema in `docs/theme-schema.md`.
- **New template (e.g. for a new email type):** add an `.mjml` file under `scripts/python/ac_builder/templates/` and register it in `_template_for_footer_mode()` in `builder.py`.
- **New skill:** scaffold under `skills/<skill-name>/SKILL.md`. The skill description is what the model sees when deciding whether to load you - keep it tight and trigger-rich. See existing skills for the pattern.
- **New AC endpoint:** add a thin function to the appropriate `api/*_v3.py` file. Avoid adding fields to `ACClient` itself; helpers stay free functions that take a client.