# Color system reference

A theme's `colors` object defines the palette the renderer uses for everything: CTA buttons, body text, page background, card sections, dark-mode equivalents. Nine tokens are required; the renderer falls over if any are missing.

## The 9 required tokens

| Token | What it controls | Light-mode example | Dark-mode counterpart |
|---|---|---|---|
| `primary` | Brand primary color. Used for some headings and as a fallback CTA color. Often the same as `cta_bg`. | `#0a3d62` | n/a |
| `cta_bg` | CTA button background. This is where the eye lands. | `#0a3d62` | n/a (buttons keep light styling in dark mode) |
| `cta_text` | CTA button text color. Must contrast strongly with `cta_bg`. Usually white. | `#ffffff` | n/a |
| `body_text` | Main body text in light mode. | `#222222` | - |
| `body_text_dark` | Main body text in dark mode. | - | `#eaeaea` |
| `bg` | Page/canvas background in light mode. | `#f5f5f5` | - |
| `bg_dark` | Page/canvas background in dark mode. | - | `#121212` |
| `card_bg` | Card or section background in light mode. Often pure white when `bg` is light grey. | `#ffffff` | - |
| `card_bg_dark` | Card or section background in dark mode. | - | `#1e1e1e` |

The schema also allows extra tokens via `additionalProperties`. The iDD `lpis` example has `primary_dark`, `secondary`, `muted`, `accent`. Renderer code may reference these in custom templates, so keeping them around when copying from `lpis` doesn't hurt; they're optional.

## How to pick colors

### Start with brand primary

If the brand has a known primary color (e.g. an existing logo color or marketing palette), set `primary` to it. The simplest approach is also to set `cta_bg = primary` so the brand color and the button color are identical. This is what `corporate-blue`, `friendly-startup`, and `lpis` do.

If the brand color is hard to read on a button (e.g. a pale yellow), use a contrasting accent for `cta_bg` instead. `bold-startup` does this: `primary` is hot pink (`#ec4899`) but `cta_bg` is black (`#000000`) for maximum tap-affordance.

### Body text and background

Body text should have strong contrast against the background. Default to:

- `body_text: #222222` on `bg: #ffffff` or `bg: #f5f5f5` (off-white) for warm/neutral feel
- `body_text: #1f2937` on `bg: #ffffff` for cooler/corporate feel
- `body_text: #000000` on `bg: #ffffff` for maximum-contrast minimalist

Avoid mid-grey body text (`#666666`-ish) on white. Looks elegant in mockups; fails accessibility on actual devices.

### Dark mode

Email clients increasingly respect dark-mode media queries. The renderer wires up `bg_dark`, `card_bg_dark`, `body_text_dark` automatically.

Simple guidance:

- `body_text_dark` should be light enough to read against `bg_dark`. `#eaeaea` against `#121212` works well.
- `bg_dark` is usually near-black but not pure black (`#121212` or `#0f172a`). Pure black creates eye strain on OLED.
- `card_bg_dark` should be slightly lighter than `bg_dark` to create visual separation. `#1e1e1e` against `#121212`, `#1e293b` against `#0f172a`.

If you don't care about dark mode, copy the dark-mode tokens from `corporate-blue` or `lpis` verbatim. They produce sensible defaults that won't look broken.

### CTA contrast

`cta_bg` and `cta_text` should hit WCAG AA contrast at minimum (4.5:1 for body text, 3:1 for large text/buttons). Common safe combinations:

- `cta_bg: #0a3d62` + `cta_text: #ffffff` (LPIS - ratio 11.7:1)
- `cta_bg: #1e40af` + `cta_text: #ffffff` (corporate-blue - ratio 8.6:1)
- `cta_bg: #10b981` + `cta_text: #ffffff` (friendly-startup - ratio 2.4:1, fails AA - acceptable for stylistic startup but not recommended)
- `cta_bg: #000000` + `cta_text: #ffffff` (bold-startup, minimal-mono - ratio 21:1, max contrast)

If you're picking custom colors and unsure, run them through https://webaim.org/resources/contrastchecker - aim for 4.5:1 or higher on the button.

## Hex format rules

The schema enforces `^#[0-9a-fA-F]{6}$`:

- Exactly 6 hex digits (no 3-digit shorthand)
- Lowercase preferred for consistency (uppercase still validates)
- Leading `#` required

Examples:

- `#000000` valid
- `#0a3d62` valid
- `#FFF` invalid (3-digit)
- `#0a3d62ff` invalid (8-digit RGBA)
- `rgb(0, 0, 0)` invalid (not hex)
- `black` invalid (not hex)

## Tools

- **Contrast checker:** https://webaim.org/resources/contrastchecker - paste two hex codes, get the WCAG ratio
- **Palette generator:** https://coolors.co or https://huemint.com if you don't have a brand color and need to pick one
- **Dark-mode tester:** https://www.litmus.com/blog/dark-mode-for-email - shows how various clients render dark mode (some just invert, some use the media query, some do neither)

## Worked example

Starting from `corporate-blue`, switching to a teal brand:

```json
{
  "colors": {
    "primary": "#0d9488",
    "cta_bg": "#0d9488",
    "cta_text": "#ffffff",
    "body_text": "#1f2937",
    "body_text_dark": "#e5e7eb",
    "bg": "#ffffff",
    "bg_dark": "#0f172a",
    "card_bg": "#f9fafb",
    "card_bg_dark": "#1e293b"
  }
}
```

Only the `primary` and `cta_bg` lines changed. Everything else inherits from the starter.
