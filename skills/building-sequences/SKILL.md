---
name: building-sequences
description: Use when the user wants to build an email sequence in ActiveCampaign from a markdown source file. The Phase 4 MJML pipeline takes a source MD plus list ID and from-address, renders each email through theme-aware MJML, runs pre-send validation, and creates campaigns via the V1 API. Idempotent by name (existing campaigns get V3 PUT updates, new ones get V1 creates). Default is dry-run for safety; pass --apply to commit. Click-action automations are captured separately via the capturing-link-actions skill and wired manually in the AC UI for v0.5.
allowed-tools: Bash, Read
argument-hint: "<md-file> --list-id <int> --from-name '...' --from-email '...' [--theme auto] [--emails E1,E2] [--apply]"
---

# Building an email sequence from a markdown source file

This is the main ac-builder workflow. The orchestrator loops through a source markdown file, renders each email through the MJML pipeline, runs pre-send validation, and creates one populated AC campaign per email via the V1 API. Re-running is safe: campaigns matched by name get V3 PUT updates, new ones get V1 creates. Default is dry-run; pass `--apply` to commit.

## When to use

Use this skill when the user has a markdown source file containing one or more emails and wants those emails created in ActiveCampaign as draft campaigns. This skill drives the full source-MD-to-AC-campaign pipeline.

Typical inputs:

- One source MD file with multiple emails as `## E1`, `## E2`, ... sections
- An AC list ID (for compliance footer rendering)
- A from-name and from-email
- Optional: a theme name (auto-inferred from filename when possible)
- Optional: a link-actions map for click-action automation wiring

Typical outputs:

- One AC draft campaign per email in the source MD
- A build manifest at `.build-manifests/YYYY-MM-DD/*.json`
- A printed table summarising what was created or updated per email

## Workflow

The recommended pattern is to render and dry-run before committing. This catches theme issues, validation failures, and merge-field typos before they reach AC.

### Step 1: Render a single email locally

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder render path/to/sequence.md --email E1 --out /tmp/e1.html
```

No AC writes. Open the HTML in a browser to eyeball layout, theme colours, banner image, body content, and footer. See `references/render-and-check.md`.

### Step 2: Dry-run for one email

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder build-sequence path/to/sequence.md \
  --list-id 1 \
  --from-name "Your Name | Your Brand" \
  --from-email "hello@yourdomain.com" \
  --emails E1
```

No `--apply`. Prints the dry-run table including validation results. Confirms parsing, theme resolution, and validator behaviour without touching AC.

### Step 3: Apply for one email

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder build-sequence path/to/sequence.md \
  --list-id 1 \
  --from-name "Your Name | Your Brand" \
  --from-email "hello@yourdomain.com" \
  --emails E1 \
  --apply
```

Creates the E1 draft campaign in AC. Open it in the AC campaign editor. Confirm the subject, preview text, sender details, content, and footer all look right. If they do, the rest of the sequence is safe to apply.

### Step 4: Apply for the full sequence

Drop the `--emails E1` filter and re-run with `--apply`:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder build-sequence path/to/sequence.md \
  --list-id 1 \
  --from-name "Your Name | Your Brand" \
  --from-email "hello@yourdomain.com" \
  --apply
```

E1 already exists in AC, so the orchestrator finds it by name and routes to a V3 PUT update path (no duplicate). E2-En get V1 from-scratch creates. See `references/idempotency.md`.

### Step 5: Verify the manifest

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder list-builds --since 7d
```

Or use the `/ac-builder:verifying-setup` skill. Each `--apply` writes a manifest entry recording every campaign create/update for audit.

## Source MD format

The orchestrator expects a single markdown file with a top-level header (sequence title plus metadata fields) and one `## E<n>` section per email. Each email section has:

- Subject line options (numbered list, first one wins)
- Preview text (in quotes)
- Email body (markdown)

Optional per-email metadata fields like `**Send date:**`, `**Theme:**` modify behaviour. Body content supports AC merge fields (`%FIRSTNAME|TITLECASE%`, `%CONTACTID%`), conditional blocks (`%IF%...%/IF%`), and explicit CTA buttons (`[[button:Label|URL]]`).

Full spec, including split-send sections and auto-detected CTAs, is in `references/source-md-format.md`.

## Theme resolution

`--theme auto` (the default behaviour when not passed explicitly) infers the theme from the source MD filename. Otherwise an explicit name like `--theme lpis` resolves through this chain (first match wins):

1. Project-local `./themes/<name>.json`
2. User-level `~/.config/ac-builder/themes/<name>.json`
3. Plugin-bundled examples `${CLAUDE_PLUGIN_ROOT}/themes/examples/<name>.json`

A path with `/` or `.` in it is treated as an explicit file path. Full resolution rules and the filename inference table are in `references/theme-resolution.md`.

## Idempotency

Campaign names are the match key. The orchestrator GETs existing AC campaigns by name before each build:

- **Existing match found** -> V3 PUT updates the message and campaign metadata
- **No match** -> V1 from-scratch create (campaign + message + link)

Re-running `--apply` after editing the source MD updates the AC campaign in place. Manual edits to the campaign in the AC UI get clobbered on re-run, so build via API first and polish in the UI last. Renaming a campaign in AC means the orchestrator can no longer find it; the next run will create a fresh copy and you'll need to clean up the renamed one manually. See `references/idempotency.md`.

## Link-action automations

Optional `--link-actions <map.json>` wires AC click-action automations to specific links inside each email. The map is a JSON file with per-email-code mappings of URL patterns to captured automation template names. Capture the template once (`ac-builder capture-automation <id>`) then reference it from the map. See `references/link-actions.md` for the full flow and known limitations of this feature.

## Required flags

| Flag | What |
|---|---|
| `--list-id <int>` | AC list ID. Used for compliance footer rendering only - the automation flow that includes the campaign determines actual recipients. Defaults to `AC_DEFAULT_LIST_ID` env var if set. |
| `--from-name '...'` | Sender display name shown in the inbox. Defaults to `AC_DEFAULT_FROM_NAME` env var if set. |
| `--from-email '...'` | Sender email address. Defaults to `AC_DEFAULT_FROM_EMAIL` env var if set. |

## Optional flags

The full reference for every flag is in `references/build-flags.md`. Highlights:

- `--theme {auto|<name>|<path.json>}` - default auto-infer
- `--emails E1,E2` - filter to specific email codes
- `--reply-to <email>` - Reply-To header override
- `--utm-campaign <slug>` - overrides "Campaign name:" from MD
- `--address-id <int>` - sender physical address library ID
- `--archive {public|private}` - archive privacy
- `--track-link-domain <domain>` - custom click-tracking domain
- `--footer-mode {launch|onboarding|transactional|auto}` - footer template
- `--header-image-url <url>` - banner override
- `--no-check` - skip pre-send validation (use sparingly)
- `--apply` - commit changes; default is dry-run

## Output table

A row per email with these columns:

| Column | Meaning |
|---|---|
| `code` | Source code (E1, E2, ...) |
| `action` | `created` (V1 path) / `updated` (V3 path) / `dry-run` / `error` |
| `campaign_id` | New or existing AC campaign ID |
| `message_id` | Message ID inside the campaign |
| `name` | Full AC campaign name |
| `validation` | `PASS` / `WARN` / `FAIL` summary |

Each `--apply` also writes a build manifest to `.build-manifests/YYYY-MM-DD/`. Inspect with `ac-builder list-builds`.

## Validation

Before each `--apply`, every email passes through the validator:

- **ERROR** findings (compliance tokens missing, image alt text missing, non-https image URLs, etc.) abort the apply
- **WARN** findings (subject length, contrast, role=presentation hints) print and proceed
- Bypass entirely with `--no-check`

To run the validator on a standalone HTML file (useful when you've manually edited an export), use `ac-builder check`. See `references/render-and-check.md`.
