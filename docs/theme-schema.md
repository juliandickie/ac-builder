# Theme schema

Themes are brand-presentation JSON files that drive the look of every email rendered through ac-builder. One theme per product (or per visual identity). The pipeline reads a theme by name, applies its colors, fonts, banner, CTA styling, and tag hooks during MJML render, and validates the result against link checks and contrast rules.

This document is the canonical reference for theme JSON authors. The machine-readable contract lives in `themes/_schema.json` and is validated automatically by `ac-builder verify --themes-only`.

## Schema overview

A theme is a single JSON object with eight required top-level keys:

| Key | Purpose |
|---|---|
| `name` | Lowercase identifier (matches filename) |
| `display_name` | Human-readable product name (used in alt text, logs) |
| `colors` | Hex palette covering CTA, body text, background, card surfaces (light + dark) |
| `fonts` | Body and (optional) heading font stacks |
| `branding` | Banner image URL(s), alt text, dimensions |
| `urls` | Sales page + Not Interested URLs (more allowed) |
| `cta_patterns` | Phrases that auto-promote inline links to styled buttons |
| `tags` | Tag-name hooks for `INTEREST:`, `NOT INTERESTED:`, `PURCHASE:` automations |

`additionalProperties: false` at the top level: extra keys cause validation to fail. Extra keys inside `colors`, `fonts.body`/`fonts.headings`, `urls`, and `tags` are tolerated and accessible at render time.

### Working examples

Seven example themes ship in `themes/examples/`. Use these as the starting point for your own theme:

| File | Archetype | Use as starter when |
|---|---|---|
| `corporate-blue.json` | Conservative blue palette, system fonts | B2B SaaS, professional services, anything that needs to read as trustworthy |
| `bold-startup.json` | Pink primary, black CTA, Inter | Product launches, design-led brands, breaking out of category sameness |
| `friendly-startup.json` | Emerald green, warm cream background | Onboarding flows, free-trial conversion, "I'm here to help" voice |
| `minimal-mono.json` | Black-on-white, IBM Plex Mono headings | Newsletters, content products, editorial brands |
| `lpis.json` | iDD live course (deep navy + gold accents, banner rotation) | iDD live in-person courses |
| `iidf.json` | iDD live entry course | iDD live entry-level courses |
| `asimr.json` | iDD evergreen online course (deep red + banner rotation) | iDD evergreen online courses |

### Minimal valid theme

This is the smallest theme that passes schema validation. Every key shown is required; the only optional fields below are `fonts.headings`, `branding.banner_urls`, `branding.banner_width_px`, `branding.banner_height_px`, and entries in `tags`.

```json
{
  "name": "my-product",
  "display_name": "My Product",
  "colors": {
    "primary": "#1e40af",
    "cta_bg": "#1e40af",
    "cta_text": "#ffffff",
    "body_text": "#1f2937",
    "body_text_dark": "#e5e7eb",
    "bg": "#ffffff",
    "bg_dark": "#0f172a",
    "card_bg": "#f9fafb",
    "card_bg_dark": "#1e293b"
  },
  "fonts": {
    "body": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
  },
  "branding": {
    "banner_url": "https://example.com/banner.jpg",
    "banner_alt": "My Product launch banner"
  },
  "urls": {
    "sales_page": "https://example.com/product?cid=%CONTACTID%",
    "not_interested": "https://example.com/not-interested?cid=%CONTACTID%"
  },
  "cta_patterns": ["Get started"],
  "tags": {}
}
```

Patterns to remember:

- `name` is lowercase, hyphens-only, must match the filename (`my-product.json` -> `"name": "my-product"`)
- All colors are 6-digit hex (`#rrggbb`). 3-digit shorthand and rgba() are not accepted.
- All URLs are full HTTPS. Sales page and Not Interested URLs include `?cid=%CONTACTID%` so AC substitutes the contact ID at send time.
- `cta_patterns` is non-empty. Even one phrase is enough.

## `name`

What it controls
: The theme identifier. Used for filename lookup (`themes/<name>.json`), CLI flags (`ac-builder build --theme <name>`), and logs. Not displayed to recipients.

Required
: Yes.

Format
: Lowercase letters, digits, and hyphens only. Must start with a letter. Pattern: `^[a-z][a-z0-9-]+$`.

Example
: `"name": "lpis"`, `"name": "corporate-blue"`, `"name": "spring-launch-2026"`

How to choose a value
: Match the filename without `.json`. Pick something short and stable - this is the public handle for the theme across CLI, logs, and skill prompts. Avoid version numbers in the name unless you genuinely keep multiple parallel themes (better to update in place).

## `display_name`

What it controls
: Human-readable product name. Currently used internally in logs and (potentially) banner alt fallbacks. Not displayed in email body content.

Required
: Yes (minLength 1).

Format
: Any non-empty string.

Example
: `"display_name": "Live Patient Implant Surgery Mini-Residency"`

How to choose a value
: Use the full public name customers see on the sales page. Spelt out, no abbreviations - the abbreviation is what `name` is for.

## `colors`

What it controls
: The complete email palette. `colors.primary` colours headings and accents. `colors.cta_bg` + `colors.cta_text` paint every auto-detected and explicit CTA button. The `bg`/`bg_dark`, `card_bg`/`card_bg_dark`, `body_text`/`body_text_dark` pairs drive light-mode and dark-mode rendering.

Required
: Yes. Nine sub-keys are required: `primary`, `cta_bg`, `cta_text`, `body_text`, `body_text_dark`, `bg`, `bg_dark`, `card_bg`, `card_bg_dark`.

Additional properties
: Allowed. Extra keys (e.g. `accent`, `muted`, `secondary`, `primary_dark`) are accepted by the schema and available to advanced templates. Each must still be a 6-digit hex color.

Sub-field reference

| Key | What it controls | Required |
|---|---|---|
| `primary` | Heading text, link colour, primary brand accent | Yes |
| `cta_bg` | Button background fill | Yes |
| `cta_text` | Button label text | Yes |
| `body_text` | Body paragraph text in light mode | Yes |
| `body_text_dark` | Body paragraph text in dark mode | Yes |
| `bg` | Outer email background in light mode | Yes |
| `bg_dark` | Outer email background in dark mode | Yes |
| `card_bg` | Card / content surface in light mode | Yes |
| `card_bg_dark` | Card / content surface in dark mode | Yes |
| `accent` | Optional - secondary accent colour | No |
| `muted` | Optional - muted body text (footers, P.S.) | No |
| `secondary` | Optional - secondary brand colour | No |
| `primary_dark` | Optional - dark-mode primary | No |

Format
: Each value is a 6-digit hex color matching `^#[0-9a-fA-F]{6}$`. RGB triplets, rgba(), 3-digit shorthand, named colors, and HSL are all rejected.

Example

```json
"colors": {
  "primary": "#0a3d62",
  "cta_bg": "#0a3d62",
  "cta_text": "#ffffff",
  "body_text": "#222222",
  "body_text_dark": "#eaeaea",
  "bg": "#f5f5f5",
  "bg_dark": "#121212",
  "card_bg": "#ffffff",
  "card_bg_dark": "#1e1e1e",
  "accent": "#c7a200"
}
```

How to choose values
: Pull `primary`, `cta_bg`, `cta_text` from your brand guide. For the dark-mode pair, take the brand-guide dark colour palette if you have one; otherwise invert tone (light becomes dark, dark becomes light) keeping the same hue. The pre-send validator runs WCAG-style contrast checks on body-on-bg and CTA-text-on-CTA-bg pairs; aim for 4.5:1 contrast minimum on body text and 3:1 minimum for buttons. If unsure, copy from one of the seven example themes and tweak.

## `fonts`

What it controls
: The CSS font stacks rendered into MJML. `fonts.body` drives paragraphs; `fonts.headings` (if set) drives H1/H2/H3 within the email body.

Required
: Yes. `fonts.body` is required (minLength 1). `fonts.headings` is optional.

Additional properties
: Not allowed beyond `body` and `headings`.

Sub-field reference

| Key | What it controls | Required |
|---|---|---|
| `body` | Body / paragraph font stack | Yes |
| `headings` | Heading font stack (falls back to body if absent) | No |

Format
: Any CSS font-family string. Use system stacks for maximum compatibility, single quotes around multi-word names.

Example

```json
"fonts": {
  "body": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
  "headings": "'IBM Plex Mono', 'Courier New', monospace"
}
```

How to choose values
: Default to a system stack so emails render the same in Gmail, Outlook, Apple Mail without webfont fallback flicker. Use `headings` to inject a brand display face only when you genuinely have one. Avoid Google Fonts URL imports here; this string is rendered verbatim into the CSS font-family declaration.

## `branding`

What it controls
: The header banner image at the top of every email. Either a single banner (`banner_url`) or a pool of banners that the renderer rotates through (`banner_urls`).

Required
: Yes. Required sub-keys: `banner_url`, `banner_alt`.

Additional properties
: Not allowed beyond the documented set.

Sub-field reference

| Key | What it controls | Required |
|---|---|---|
| `banner_url` | Primary banner image URL. Used as the only banner unless `banner_urls` is set, in which case it should also be `banner_urls[0]`. | Yes |
| `banner_urls` | Optional array of 1+ banner URLs. The renderer rotates through these per email by index, so E1 uses `[0]`, E2 uses `[1]`, etc., wrapping when exhausted. | No |
| `banner_alt` | Alt text for screen readers and image-blocked clients. Surfaces in Gmail's "Show images" prompt. | Yes (minLength 1) |
| `banner_width_px` | Pixel width hint for renderer (100-1200) | No |
| `banner_height_px` | Pixel height hint for renderer (50-600) | No |

Format
: `banner_url` and `banner_urls` items are full HTTPS URLs (validated against `format: uri`). `banner_alt` is a non-empty string. `banner_width_px` and `banner_height_px` are integers in their respective ranges.

Example

```json
"branding": {
  "banner_url": "https://content.app-us1.com/.../banner-a.jpeg",
  "banner_urls": [
    "https://content.app-us1.com/.../banner-a.jpeg",
    "https://content.app-us1.com/.../banner-b.jpeg",
    "https://content.app-us1.com/.../banner-c.jpeg"
  ],
  "banner_alt": "Product launch banner",
  "banner_width_px": 600,
  "banner_height_px": 180
}
```

How to choose values
: Upload banners through ActiveCampaign's content library so they're served from `content.app-us1.com` (or your AC region equivalent). External CDNs work but AC banner URLs survive deliverability heuristics best. For `banner_alt`, write a real description ("Live Patient Implant Surgery Mini-Residency - Wellington"), not generic text ("banner image"). Set `banner_width_px` to 600 for typical 600-wide email designs; this prevents Outlook resizing artefacts. Use `banner_urls` when running a long sequence and you want visual variety per email; the renderer will rotate automatically.

## `urls`

What it controls
: The link destinations for the theme's primary CTA and Not Interested footer link. Plus any other named URLs you want to reuse across emails (e.g., a knowledge base, a webinar replay).

Required
: Yes. Required sub-keys: `sales_page`, `not_interested`.

Additional properties
: Allowed. Add as many named URLs as you need - each value must be a URI-reference.

Sub-field reference

| Key | What it controls | Required |
|---|---|---|
| `sales_page` | The product sales page URL. Inline links matching this URL auto-promote to styled CTA buttons during render (regardless of whether the link text matches a `cta_patterns` entry). | Yes |
| `not_interested` | Unsubscribe / Not Interested URL. Surfaces in the standard email footer where applicable. | Yes |
| Any other key | Reusable named URL (e.g., `webinar`, `knowledge_base`) | No |

Format
: Each value is a URI-reference (full HTTPS URL or relative path). Always include `?cid=%CONTACTID%` as the first query parameter so ActiveCampaign substitutes the contact ID at send time, enabling your `?cid=` analytics tracking.

Example

```json
"urls": {
  "sales_page": "https://example.com/product?cid=%CONTACTID%",
  "not_interested": "https://example.com/not-interested?cid=%CONTACTID%",
  "webinar": "https://example.com/webinar?cid=%CONTACTID%"
}
```

How to choose values
: For `sales_page`, use the canonical product URL. For `not_interested`, use a dedicated landing page that explains what "Not Interested" means and confirms the contact's preference. (Do not use `mailto:` here; use a web URL the AC link-action automation can match against.)

## `cta_patterns`

What it controls
: The phrases that get auto-detected as CTAs. When a markdown link's text matches one of these phrases (case-insensitive, after stripping trailing arrow decorations), the renderer promotes that link from inline anchor to styled `<mj-button>` using `colors.cta_bg` and `colors.cta_text`. The promotion algorithm also fires when the link URL matches `urls.sales_page` regardless of link text.

Required
: Yes (minItems 1, uniqueItems true).

Format
: An array of non-empty strings. Each entry is one phrase to match.

Example

```json
"cta_patterns": [
  "Register now",
  "Reserve your spot",
  "Hold my seat",
  "Yes, count me in",
  "Continue to checkout",
  "Tell me more"
]
```

How to choose values
: List every phrase you actually use as a CTA in your sequence. Match-by-text is case-insensitive and tolerates trailing arrows / right-pointing chars; e.g., `"Register now"` matches `"Register now ->"`, `"REGISTER NOW"`, `"register now »"`. The matching is exact-equality (after normalisation), not substring - "Register now today" will not match "Register now". Add common abbreviations and variations to the list rather than relying on partial matches.

## `tags`

What it controls
: ActiveCampaign tag names that link-action automations apply when contacts click the relevant CTAs. The captured automation JSON template (under `automations/templates/`) reads these tag names and applies them on click.

Required
: Yes (the key must exist), but the object can be empty (`{}`).

Sub-field reference

| Key | What it controls | Required |
|---|---|---|
| `interest` | Tag name applied when contact clicks any positive CTA (sales-page link, button, etc.) | No |
| `not_interested` | Tag name applied when contact clicks the Not Interested link | No |
| `purchase` | Tag name applied when purchase confirmation triggers the post-purchase automation | No |
| Any other key | Project-specific tag (e.g., `interest_branch_a`, `interest_pulse_point_1`) | No |

Format
: Each value is a string. By project convention: `PREFIX: Descriptor` (ALL CAPS prefix, colon, descriptive name).

Example

```json
"tags": {
  "interest": "INTEREST: LPIS 2026 - Engaged",
  "not_interested": "NOT INTERESTED: LPIS 2026"
}
```

How to choose values
: Mirror the iDD tag taxonomy: ALL CAPS category prefix, colon, then descriptor. Examples: `INTEREST: ASIMR - Engaged`, `NOT INTERESTED: ASIMR`, `PURCHASE: LPIS - Wellington - 2026-06-19`. Tags must already exist (or be creatable) in ActiveCampaign - the link-action automations don't auto-create them.

## Validation

Every theme is validated against `themes/_schema.json` whenever:

- `ac-builder verify` runs (full pipeline check including AC API + MJML)
- `ac-builder verify --themes-only` runs (skips AC + MJML, only checks theme JSONs)
- A skill loads a theme via `theme_loader.load_theme(name)` (loaded themes are validated on every render)

Run `ac-builder verify --themes-only` after editing a theme to catch errors before you build a campaign.

### Common validation failures

| Error | Likely cause |
|---|---|
| `'name' does not match '^[a-z][a-z0-9-]+$'` | Uppercase letters, underscores, or special characters in `name` |
| `'colors' is missing required property 'card_bg_dark'` | One of the 9 required color keys is absent |
| `'#FFF' does not match '^#[0-9a-fA-F]{6}$'` | 3-digit hex shortcut or non-hex format - use 6-digit form |
| `Additional properties are not allowed ('logo_url' was unexpected)` | Extra top-level key. The schema is closed at the top level. |
| `'banner_url' is a required property` | Missing inside `branding` |
| `[] is too short` | `cta_patterns` empty - add at least one phrase |
| `format 'uri' validation failed` | Banner or URL is not a full URI - usually missing `https://` prefix |

### Where to look first

1. The error message tells you the JSON path of the failure (e.g., `colors.cta_bg`).
2. Open the schema at `themes/_schema.json` to see the exact rule at that path.
3. Compare against a working example in `themes/examples/`.
4. Re-run `ac-builder verify --themes-only` to confirm the fix.
