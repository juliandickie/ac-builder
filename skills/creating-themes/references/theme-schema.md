# Theme schema reference

A theme JSON describes a single brand: its colors, fonts, banner image, sales URLs, CTA patterns, and AC tag names. Every theme is validated against `themes/_schema.json` at load time. This file is a quick orientation; the canonical detailed reference lives at `docs/theme-schema.md` (added in Task E3).

## The 8 top-level fields

| Field | Required | What |
|---|---|---|
| `name` | yes | Lowercase hyphen-separated slug. Must match the filename (`acme-implants` -> `acme-implants.json`). Pattern: `^[a-z][a-z0-9-]+$`. |
| `display_name` | yes | Human-readable label. Shown in the AC verify output and used as a fallback heading in some templates. |
| `colors` | yes | Object with 9 required hex color tokens (see `color-system.md`). Extra tokens are allowed via `additionalProperties`. |
| `fonts` | yes | Object with `body` (required) and optional `headings`. Standard CSS font-family stacks. |
| `branding` | yes | Banner image config. Requires `banner_url` and `banner_alt`; optional `banner_urls` (rotation), `banner_width_px`, `banner_height_px`. See `banner-images.md`. |
| `urls` | yes | Object with `sales_page` (required) and `not_interested` (required). Extra keyed URLs (e.g. `pricing`, `faq`) are allowed. |
| `cta_patterns` | yes | Array of strings. Plain-link text matching one of these (case-insensitive equals) is auto-promoted to a CTA button. Min 1 item. See `cta-patterns.md`. |
| `tags` | yes | Object with optional `interest`, `not_interested`, `purchase` keys. Extra keys allowed. |

## Required vs optional - quick table

```
Required at top level:    name, display_name, colors, fonts, branding, urls, cta_patterns, tags
Required inside colors:   primary, cta_bg, cta_text, body_text, body_text_dark,
                          bg, bg_dark, card_bg, card_bg_dark
Required inside fonts:    body
Required inside branding: banner_url, banner_alt
Required inside urls:     sales_page, not_interested
Required inside tags:     (none - the object can be empty {})
```

## Common validation errors

- **`name` field doesn't match filename.** A theme at `themes/foo.json` must have `"name": "foo"`. Mismatches fail at load time.
- **Hex colors aren't 6 digits.** `#000` is invalid; use `#000000`. The pattern `^#[0-9a-fA-F]{6}$` is enforced on every color token.
- **Missing required color token.** All 9 must be present. Even if you don't care about dark mode, copy the dark-mode tokens from a starter.
- **`banner_url` not a valid URI.** Must be a complete `https://...` URL. Use `https://placehold.co/1200x300/cccccc/000000?text=Brand` for testing.
- **Missing `cta_patterns` (array empty).** Min 1 item required. If you don't have a CTA pattern in mind, just keep one from the starter.
- **`additionalProperties: false` violations.** The top-level schema and `fonts` and `branding` blocks all set `additionalProperties: false`, meaning unknown keys fail validation. Stick to the keys above.

## How to validate

Run the bundled verifier:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder verify --themes-only
```

The output lists every theme JSON found and reports `OK` or `FAIL` per file. On `FAIL`, the error line names the JSON path that's wrong (e.g. `colors.cta_bg: '#FFF' does not match '^#[0-9a-fA-F]{6}$'`).

## Where the schema lives

- Canonical schema: `themes/_schema.json` in the plugin root
- Detailed reference doc (Task E3): `docs/theme-schema.md`

When in doubt, open `themes/_schema.json` directly. It's a JSON Schema 2020-12 doc and is the authoritative source.
