# Copying from examples - worked walkthroughs

Concrete walkthroughs of copying each starter and editing it for a new brand. Use these as templates when scaffolding your own.

## Walkthrough 1: copying `lpis` for a dental-practice client

**Scenario:** A dental practice client called "Smile Architects" wants to launch a 3-day implant course. Their brand color is forest green (`#166534`). They have a banner photo of the lead dentist mid-procedure.

### Diff from the starter

```jsonc
{
  "name": "smile-architects-implants",          // was "lpis"
  "display_name": "Smile Architects Implant Course 2026",  // was "Live Patient Implant Surgery Mini-Residency"

  "colors": {
    "primary": "#166534",                       // was "#0a3d62"
    "primary_dark": "#1f7d3f",                  // was "#1a4d72" - hand-picked lighter green
    "secondary": "#84cc16",                     // was "#1d7d8e" - lime accent
    "cta_bg": "#166534",                        // was "#0a3d62"
    "cta_text": "#ffffff",                      // unchanged
    "body_text": "#222222",                     // unchanged
    "body_text_dark": "#eaeaea",                // unchanged
    "bg": "#f5f5f5",                            // unchanged
    "bg_dark": "#121212",                       // unchanged
    "card_bg": "#ffffff",                       // unchanged
    "card_bg_dark": "#1e1e1e",                  // unchanged
    "muted": "#888888",                         // unchanged
    "accent": "#84cc16"                         // updated to lime
  },

  "fonts": {
    "body": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    "headings": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
  },                                            // unchanged

  "branding": {
    "banner_url": "https://content.app-us1.com/SmileArchitects/2026/05/10/banner.jpg",
    "banner_alt": "Smile Architects Implant Course 2026 - Dr Marcus Hou demonstrating osteotomy",
    "banner_width_px": 600,                     // unchanged
    "banner_height_px": 180                     // unchanged
  },

  "urls": {
    "sales_page": "https://smilearchitects.com/implant-course/?cid=%CONTACTID%",
    "not_interested": "https://smilearchitects.com/not-interested/?cid=%CONTACTID%"
  },

  "cta_patterns": [
    "Register now",
    "Reserve your spot",
    "Apply for the course",                     // was "Apply for the residency"
    "Hold my seat",
    "Yes, count me in",
    "Book the call",
    "Continue to checkout",
    "Tell me more"
  ],

  "tags": {
    "interest": "INTEREST: Smile Architects Implants 2026 - Engaged",
    "not_interested": "NOT INTERESTED: Smile Architects Implants 2026"
  }
}
```

### What changed and why

- `name`, `display_name`, `tags.*` - brand-specific identifiers
- `colors.primary`, `colors.cta_bg`, `colors.accent` - brand greens replacing iDD blues. Dark-mode tokens unchanged because the iDD ones work fine for any brand.
- `branding.banner_url`, `branding.banner_alt` - new banner uploaded to AC content library, descriptive alt text
- `urls.*` - brand domain plus the `?cid=%CONTACTID%` query parameter for tracking
- `cta_patterns` - one phrase changed ("course" instead of "residency"); the rest of the iDD course CTA vocabulary fits the use-case

### What stayed

- All fonts (system stack works for any brand)
- Dark-mode color palette (works for any near-black background)
- `banner_width_px`/`banner_height_px` (assuming the new banner is also 600x180)
- Most of `cta_patterns` (the iDD course vocabulary fits a course product)

## Walkthrough 2: copying `corporate-blue` for a B2B SaaS

**Scenario:** A B2B SaaS called "Linear Insights" sells analytics dashboards to revenue teams. Their brand is electric purple (`#7c3aed`). They use a wordmark-on-gradient banner.

### Diff from the starter

```jsonc
{
  "name": "linear-insights",                    // was "corporate-blue"
  "display_name": "Linear Insights Q2 Pipeline Outreach",

  "colors": {
    "primary": "#7c3aed",                       // was "#1e40af"
    "cta_bg": "#7c3aed",                        // was "#1e40af"
    "cta_text": "#ffffff",                      // unchanged
    "body_text": "#1f2937",                     // unchanged - dark grey is brand-agnostic
    "body_text_dark": "#e5e7eb",                // unchanged
    "bg": "#ffffff",                            // unchanged
    "bg_dark": "#0f172a",                       // unchanged
    "card_bg": "#f9fafb",                       // unchanged
    "card_bg_dark": "#1e293b"                   // unchanged
  },

  "fonts": {
    "body": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    "headings": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
  },                                            // changed from system stack to Inter for brand consistency

  "branding": {
    "banner_url": "https://cdn.linearinsights.com/email/q2-launch-banner.png",
    "banner_alt": "Linear Insights - revenue dashboards built for revops teams",
    "banner_width_px": 1200,
    "banner_height_px": 300
  },

  "urls": {
    "sales_page": "https://linearinsights.com/get-started/?cid=%CONTACTID%",
    "not_interested": "https://linearinsights.com/not-interested/?cid=%CONTACTID%"
  },

  "cta_patterns": [
    "Schedule a demo",
    "Book a 15-min call",                       // brand-specific phrase
    "Try Linear Insights",                      // brand-specific phrase
    "See it in action",
    "Talk to sales",
    "Learn more"
  ],

  "tags": {
    "interest": "INTEREST: Linear Insights Q2 Pipeline",
    "not_interested": "NOT INTERESTED: Linear Insights",
    "purchase": "PURCHASE: Linear Insights Annual Plan"
  }
}
```

### What changed and why

- `name`, `display_name`, `tags.*` - brand-specific identifiers
- `colors.primary`, `colors.cta_bg` - electric purple replacing corporate blue. Body text and dark-mode unchanged.
- `fonts.body` and `fonts.headings` - prefixed `'Inter'` (a popular SaaS font) ahead of the system stack. Email clients fall back to the system stack if Inter isn't available.
- `branding.*` - new banner served from the brand's own CDN
- `urls.*` - brand domain
- `cta_patterns` - replaced the corporate generic with brand-specific phrases. The brand voice is "decisive, low-pressure" - "Book a 15-min call" reflects that better than "Get started".

## Pro tip: keep CTA patterns when copying

The starter's `cta_patterns` array is usually pretty good. Unless you specifically know you'll be using different CTA wording across your emails, keep the inherited patterns. You can always add more phrases later by editing the JSON; the array doesn't have a maximum length.

## Pro tip: hot-swap colors only if everything else fits

The fastest way to get a usable theme: change `display_name`, `colors.primary`, `colors.cta_bg`, `branding.*`, `urls.*`, `tags.*` and leave everything else unchanged. This is what 90% of new-brand setups should do.

If your brand needs custom fonts, exotic dark-mode colors, or a unique CTA vocabulary, those are second-pass refinements. Get the basic theme working first, send a test email, see how it looks, then refine.

## Validation after editing

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder verify --themes-only
```

Should print `theme <slug>: OK`. If it doesn't, the error line names the broken field. See `theme-schema.md` for common validation errors.

## Render before sending

After validation passes, do a quick render-only check before any AC writes:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder render path/to/sequence.md \
  --email E1 \
  --theme <slug> \
  --out /tmp/e1.html
```

Open `/tmp/e1.html` in a browser. Confirm:

- Banner renders (or alt text shows clearly if blocked)
- Body text contrasts with background
- CTA buttons are styled with the brand color
- Footer still works (footer is theme-independent but worth eyeballing)

If anything looks off, edit the theme JSON and re-render. No AC writes happen at this stage; iterate freely.
