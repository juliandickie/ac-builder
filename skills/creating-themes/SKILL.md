---
name: creating-themes
description: Use when the user wants to create a new brand theme JSON for use with building-sequences. Walks through brand colors, typography, banner image, CTA patterns, and footer details by copying a starter example and editing fields. Validates the result against themes/_schema.json. Use for new client onboarding (agency multi-brand setup), or first-time theme creation. Lean v0.5 implementation; v0.6 will add interview-style prompting and contrast checks.
allowed-tools: Read, Write, Bash
argument-hint: "[--from <example-theme>] [--out themes/<brand>.json]"
---

# Creating a new brand theme JSON

This skill scaffolds a new theme JSON for use with `building-sequences`. The lean v0.5 flow is: pick a starter example, ask the user for the brand-specific values (display name, primary color, banner URL, sales page URL, etc.), write the new theme to the user-level themes directory, and validate it against `themes/_schema.json`.

## When to use

- **New client onboarding** in an agency multi-brand setup (each client gets their own theme)
- **First-time theme creation** for a brand that doesn't yet have a JSON
- When `--theme <name>` resolution fails because no theme JSON exists yet
- Before running `building-sequences --theme <new-brand>` for the first time

If the user already has a theme JSON and just wants to tweak it, point them at the file directly (Read + Edit) rather than running this skill.

## What v0.5 gives you

- Lists `themes/examples/*.json` and helps pick a starter
- Asks for the 6 most important brand-specific values (display name, primary color, banner URL, banner alt text, from-address, sales page URL)
- Writes a complete theme JSON to `~/.config/ac-builder/themes/<slug>.json`
- Runs `ac-builder verify --themes-only` to confirm it loads

That's it. The skill copies most of the starter unchanged (fonts, dark-mode colors, CTA patterns) and lets you edit them later if needed.

## What v0.6 will add

- Interview-style prompting (one question at a time with smart defaults instead of a single batch)
- WCAG color contrast checks on `cta_bg`/`cta_text` and `body_text`/`bg`
- Banner image upload helper (push a local file to AC content library, return the canonical URL)
- Per-brand inference rules so `--theme auto` works for the new brand without explicit flags

For now, you get a working theme that validates and renders. UX polish comes later.

## Step-by-step workflow

### Step 1: Pick a starter

The skill lists the bundled examples and asks which to copy from:

```
Available starters in themes/examples/:
  - corporate-blue   (B2B / professional - blue and grey palette)
  - friendly-startup (SaaS / friendly - green and warm palette)
  - bold-startup     (high-contrast launch - hot pink and black)
  - minimal-mono     (editorial / newsletter - black and white)
  - lpis             (real iDD example - dental implant residency)
  - iidf             (real iDD example - intro-level dental course)
  - asimr            (real iDD example - online surgical course)

Which one feels closest to your brand? (default: corporate-blue)
```

Pick the one whose archetype matches yours. You'll edit the brand-specific fields next; the structural choices (fonts, dark-mode handling, layout) stay from the starter.

### Step 2: Read the starter

The skill uses the Read tool to pull the starter JSON's content into context, so it knows what to keep and what to override.

### Step 3: Ask for brand-specific values

The skill asks for these one at a time (or accepts them in a single batch if the user provides them upfront):

| Field | Example value | Notes |
|---|---|---|
| `display_name` | "Acme Implants 2026 Launch" | Human-readable product/sequence name |
| `colors.primary` | `#0066cc` | Hex format, 6-digit lowercase preferred |
| `branding.banner_url` | `https://content.app-us1.com/.../banner.jpg` | Full HTTPS URL, 4:1 aspect ratio recommended |
| `branding.banner_alt` | "Acme Implants 2026 - hands-on course" | Required for accessibility |
| `urls.sales_page` | `https://acme.com/course/?cid=%CONTACTID%` | Include `?cid=%CONTACTID%` for tracking |
| `urls.not_interested` | `https://acme.com/not-interested/?cid=%CONTACTID%` | Standard unsubscribe-but-stay-subscribed URL |

Other fields (`cta_bg`, `cta_text`, dark-mode colors, fonts, CTA patterns) inherit from the starter unless the user explicitly overrides. By default `cta_bg` is set equal to `colors.primary`. See `references/color-system.md` for guidance on overriding the dark-mode palette.

### Step 4: Write the new theme

Write the result to `~/.config/ac-builder/themes/<slug>.json` where `<slug>` is the lowercase-hyphen identifier (validated against `^[a-z][a-z0-9-]+$` per the schema). The slug becomes the value of the JSON's `name` field, must match the filename, and is what the user passes as `--theme <slug>` to `building-sequences`.

If the user doesn't suggest a slug, derive one from the display name (e.g. "Acme Implants 2026 Launch" -> `acme-implants-2026`).

### Step 5: Validate

Run the verifier in themes-only mode:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder verify --themes-only
```

The new theme appears in the output as `theme <slug>: OK`. If it shows `FAIL`, the error line names the field that's wrong; fix the JSON and re-run. See `references/theme-schema.md` for the schema rules and `references/copying-from-examples.md` for common edits.

### Step 6: Use the theme

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder build-sequence path/to/sequence.md \
  --list-id 1 \
  --from-name "Your Name | Acme" \
  --from-email "hello@acme.com" \
  --theme <slug>
```

The slug resolves through the standard chain (`./themes/`, `~/.config/ac-builder/themes/`, plugin examples). Since the file is in the user-level dir, every project on this machine sees it.

## Example dialogue

```
User: I'm setting up a new client called "Bright Dental". B2B, conservative.

Skill: Sure. Best starter is probably `corporate-blue` (B2B / professional). Sound right?

User: Yes.

Skill: [reads themes/examples/corporate-blue.json]

I need 6 values from you:
  1. Brand display name? (e.g. "Bright Dental Implant Course")
  2. Primary color in hex? (e.g. #0066cc)
  3. Banner image URL? (HTTPS, 1200x300 ideal)
  4. Banner alt text?
  5. Sales page URL? (include ?cid=%CONTACTID%)
  6. Not Interested URL?

User: 1. Bright Dental Implant Course 2026
      2. #2563eb
      3. https://content.app-us1.com/X1Y2Z3/2026/05/12/banner.jpg
      4. Bright Dental Implant Course 2026 banner
      5. https://brightdental.com/implant-course/?cid=%CONTACTID%
      6. https://brightdental.com/not-interested/?cid=%CONTACTID%

Skill: Slug `bright-dental` work for the filename? (used as --theme bright-dental)

User: Yes.

Skill: [writes ~/.config/ac-builder/themes/bright-dental.json]
       [runs ac-builder verify --themes-only]

theme bright-dental: OK

Done. Use --theme bright-dental on building-sequences.
```

## Validation

Validation happens in two places:

1. **Schema check** at write-time: the skill confirms the JSON has all required fields (`name`, `display_name`, `colors`, `fonts`, `branding`, `urls`, `cta_patterns`, `tags`) before writing. The 9 required color tokens must all be present and match `^#[0-9a-fA-F]{6}$`.
2. **Loader check** via `ac-builder verify --themes-only`: confirms the JSON parses, validates against `_schema.json`, and the loader can construct a `ThemeData` instance from it.

Common validation failures and fixes are in `references/theme-schema.md`. Color guidance is in `references/color-system.md`. Banner image rules are in `references/banner-images.md`. CTA pattern semantics (case-insensitive equals match) are in `references/cta-patterns.md`. Worked examples of copying-and-editing each starter are in `references/copying-from-examples.md`.

## Output location

Default write target: `~/.config/ac-builder/themes/<slug>.json`. This is the user-level override directory. It applies to every project on the machine.

If the user wants to commit the theme to a project repo instead, write to `./themes/<slug>.json` relative to the project root. The loader checks project-local first, so a project-level theme takes precedence over the user-level one of the same name. Pass `--out themes/<slug>.json` to override the default location.

## Limitations (v0.5)

- The skill does not check color contrast (WCAG AA/AAA). The user is responsible for picking accessible color pairs. See `references/color-system.md` for tool recommendations.
- The skill does not upload banner images. The user supplies an already-hosted HTTPS URL. See `references/banner-images.md` for hosting suggestions including AC's content library.
- The skill keeps the starter's `cta_patterns` array unchanged. If the new brand uses different CTA copy, the user edits the JSON afterwards. See `references/cta-patterns.md` for guidance on customising patterns.
- Filename inference rules are hard-coded for iDD (`LPIS`, `IIDF`, `ASIMR`). For other brands, always pass `--theme <slug>` explicitly.

These are acknowledged v0.5 limitations. v0.6 closes them.
