# Render and check reference

How to use the standalone `render` and `check` subcommands to debug locally before running `build-sequence --apply`.

## ac-builder render

Renders one email from a source MD to a local HTML file. No AC writes. Use to preview rendering, debug theme issues, and eyeball layout before committing to AC.

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder render path/to/sequence.md --email E1 --out /tmp/e1.html
```

Open `/tmp/e1.html` in a browser. You should see:

- The theme's banner image at the top
- The email body styled per the theme (colours, fonts, spacing)
- CTAs styled as buttons
- The compliance footer at the bottom (sender address, unsubscribe link)

### Render flags

| Flag | What |
|---|---|
| `--email <code>` | Single email code to render (default: first in MD) |
| `--theme <name>` | Override theme (otherwise filename inference) |
| `--footer-mode {launch|onboarding|transactional|auto}` | Footer template (default auto) |
| `--out <path>` | Output HTML file path (required) |

The render subcommand is intentionally minimal. It does not call AC. It does not run the validator. It produces an HTML file you can eyeball or send to email-rendering tools (Litmus, Email on Acid) for cross-client preview.

### Iteration loop

Editing themes or source MD content is easiest with this loop:

1. Edit the source MD or theme JSON
2. Re-run `ac-builder render <md> --email E1 --out /tmp/e1.html`
3. Refresh the browser tab on `/tmp/e1.html`
4. Repeat until happy
5. Then move on to dry-run / `--apply`

## ac-builder check

Runs the pre-send validator on a standalone HTML file. Useful when you've manually edited an export and want to confirm it still passes the same checks `build-sequence` would run before applying.

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT}/scripts/python ac-builder check /tmp/e1.html
```

### Check flags

| Flag | What |
|---|---|
| `--subject <text>` | Subject line to validate (length, casing) |
| `--preview <text>` | Preview text to validate (length) |
| `--footer-mode {launch|onboarding|transactional}` | Footer template the file is using (validator looks for the right tokens) |

If you don't pass `--subject` or `--preview`, those checks are skipped; the validator only inspects the HTML body.

### Validator severity

The validator emits findings at two severities:

- **ERROR** - aborts `--apply` in `build-sequence`. Fixable issues like missing alt text on images, non-https image URLs, missing compliance tokens (`%UNSUBSCRIBELINK%`, `%SENDER-INFO%`), missing footer mode marker.
- **WARN** - prints and proceeds. Issues like subject longer than 60 chars, low colour contrast, missing `role="presentation"` on layout tables, etc.

To bypass entirely, use `build-sequence --no-check`. Reserved for occasions where you've already validated externally and accept the WARN findings.

### Workflow integration

`build-sequence` runs the validator automatically on every email before each `--apply`. The output table's `validation` column summarises PASS / WARN / FAIL.

Use `ac-builder check` directly when:

- You've manually downloaded a campaign HTML from AC and edited it externally
- You want to validate an HTML produced by another tool (e.g. an MJML playground)
- You want to debug a single validator failure without re-running the full pipeline

## Recommended preview workflow

For each new sequence:

1. **Render E1 locally:** `ac-builder render sequence.md --email E1 --out /tmp/e1.html`
2. **Eyeball in a browser:** Check banner, body, CTAs, footer.
3. **Send to a render-testing tool:** (optional) Litmus, Email on Acid, or paste into your own gmail/outlook for visual confirmation.
4. **Run check on the rendered HTML:** `ac-builder check /tmp/e1.html` to confirm validator passes.
5. **Dry-run build-sequence:** `ac-builder build-sequence sequence.md --emails E1 --list-id 1 --from-name "..." --from-email "..."`
6. **Apply E1:** Add `--apply`. Verify in AC editor.
7. **Apply full sequence:** Drop `--emails`, keep `--apply`.

This catches theme problems, validation failures, and AC-specific quirks at the cheapest possible step rather than after pushing 20 campaigns.

## Common debugging scenarios

- **"My banner doesn't show"** -> render locally, inspect element. Likely a theme `branding.banner_url` issue or an unreachable URL.
- **"My CTAs aren't styled as buttons"** -> render and check whether they match the theme's `cta_patterns`. Either add the pattern to the theme or use explicit `[[button:Label|URL]]`.
- **"My merge field shows literally as %FIRSTNAME%"** -> AC merge field substitution happens at send-time, not render-time. Local renders show the literal token; that's expected.
- **"Validator complains about alt text"** -> the email body has an image without alt text. Add `![Alt text](url)` syntax in the MD or set the theme's `branding.banner_alt`.
