# ac-builder

Build ActiveCampaign email sequences from markdown via MJML, exposed as Claude Code skills.

> Author your emails as markdown. Render them through theme-aware MJML for cross-client compatibility. Create AC campaigns via the V1 API. All from inside a Claude Code session.

## What it does

Given a markdown file describing an email sequence, `ac-builder`:

1. Parses each H2 section as one email (subject options, preview text, body markdown, send metadata)
2. Renders the body through a Jinja2 + MJML pipeline using a brand theme JSON (colors, fonts, banner image, CTA styling)
3. Validates the result against pre-send checks (compliance tokens, alt text, image protocol, subject length, contrast)
4. Creates one AC campaign per email via the V1 API, idempotent by name
5. Provides supporting skills for inspecting AC state, editing campaigns, sending tests, and capturing link-action automation templates

## Prerequisites

- **Python 3.11+** with [`uv`](https://docs.astral.sh/uv/) installed (hard requirement, no fallback to plain pip)
- **Node 20+** (for MJML)
- **An ActiveCampaign account** with API access (any tier)
- **Claude Code** (CLI, desktop, or web)

If you don't have `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If you don't have Node 20+:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 20
```

## Install

```bash
# 1. Add the marketplace (if you haven't already)
/plugin marketplace add juliandickie/plugins

# 2. Install ac-builder
/plugin install ac-builder@juliandickie-plugins

# 3. Set up credentials (one-time)
mkdir -p ~/.config/ac-builder
cat > ~/.config/ac-builder/config.env <<EOF
AC_API_URL=https://your-account.api-us1.com
AC_API_KEY=your-api-key
AC_DEFAULT_LIST_ID=1
AC_DEFAULT_FROM_NAME=Your Name | Your Brand
AC_DEFAULT_FROM_EMAIL=hello@yourdomain.com
AC_DEFAULT_REPLY_TO=hello@yourdomain.com
EOF

# Get AC_API_URL and AC_API_KEY from AC > Settings > Developer

# 4. Verify
/ac-builder:verifying-setup
```

## Five-minute first build

Once `verifying-setup` passes, build your first campaign from a sample MD file:

```bash
# Render a sample email locally to preview (no AC writes)
mkdir -p /tmp/ac-builder-demo && cd /tmp/ac-builder-demo
cat > welcome.md <<'EOF'
# My First Sequence

**Campaign name:** my-first-sequence

## E1 - Welcome

### Subject Line Options

1. **Welcome to the team**

### Preview Text

"Glad you're here."

### Email Body

Hi %FIRSTNAME|TITLECASE%,

Welcome to our list. Here's what to expect.

Cheers,
Your Name
EOF

# Render preview locally (no AC writes)
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder render welcome.md --email E1 --theme corporate-blue --out preview.html
open preview.html  # or use your preferred browser
```

Then trigger the full build via the skill:

```
/ac-builder:building-sequences welcome.md --list-id 1 --from-name "Your Name" --from-email hello@yourdomain.com --theme corporate-blue --emails E1
```

(Default is dry-run. Add `--apply` once you've verified the dry-run output.)

## Skills available

| Skill | Purpose |
|---|---|
| `/ac-builder:verifying-setup` | Health check + first-run setup walkthrough |
| `/ac-builder:building-sequences` | Build N campaigns from a markdown source file |
| `/ac-builder:inspecting-ac-state` | Look up campaigns, tags, custom fields, automations (read-only) |
| `/ac-builder:editing-campaigns` | Mutate an existing campaign or message |
| `/ac-builder:cleanup-and-testing` | Send tests; delete probe campaigns |
| `/ac-builder:capturing-link-actions` | Capture an AC automation as a click-action template |
| `/ac-builder:creating-themes` | Author a new brand theme JSON |

## Themes

`ac-builder` ships with 7 example themes:

- `corporate-blue` (B2B / professional)
- `friendly-startup` (SaaS / friendly tone)
- `bold-startup` (high-contrast launch / pre-order)
- `minimal-mono` (editorial / newsletter)
- `lpis`, `iidf`, `asimr` (Institute of Digital Dentistry products - real production examples)

To author your own theme, run `/ac-builder:creating-themes` and pick one of the examples to start from. Themes you create live at `~/.config/ac-builder/themes/<your-brand>.json` and override the bundled examples when names collide.

For multi-brand setups (an agency managing multiple clients), put per-project themes in `./themes/<client>.json` next to your source MD files. They take precedence over `~/.config/ac-builder/themes/`.

See [`docs/theme-schema.md`](docs/theme-schema.md) for the full theme schema reference.

## Source markdown format

```markdown
# Sequence Title

**Campaign name:** sequence-slug-2026

**Voice:** First-person, conversational

## E1 - Email Title

**Send date:** Mon Apr 27, 2026
**Theme:** corporate-blue            # optional; otherwise inferred from filename

### Subject Line Options

1. **First subject (recommended)**
2. **Second option**

### Preview Text

"Preview text here"

### Email Body

Hi %FIRSTNAME|TITLECASE%,

Body markdown content. Supports merge fields (%FIRSTNAME|TITLECASE%, %CONTACTID%),
conditional content (%IF !empty($SPECIALTY)%...%/IF%), and explicit CTA buttons:

[[button:Hold my seat|https://example.com/?cid=%CONTACTID%]]

Auto-detected CTAs match theme.cta_patterns (e.g., "Schedule a demo" gets styled
as a primary button automatically).
```

See [`docs/source-md-format.md`](docs/source-md-format.md) for the full spec.

## Architecture

The plugin bundles the `ac-builder` Python tool in `scripts/python/`. Skills shell out to it via:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder <subcommand> [args...]
```

`uv` handles venv creation and dependency installation transparently on first invocation. See [`docs/architecture.md`](docs/architecture.md) for details.

## Status

v0.5.0 is the first public release. Roadmap:

- **v0.6:** Richer `creating-themes` UX (interview-style prompting, contrast checks, banner upload helpers)
- **v0.7:** Modern email design refresh (gradients, Material-inspired polish, dark-mode tokens)

## Contributing

PRs welcome for new themes, skill improvements, and bug fixes. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT (c) 2026 Julian Dickie
