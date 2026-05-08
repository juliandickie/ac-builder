# CTA pattern reference

The `cta_patterns` array in a theme JSON drives auto-detection of CTA buttons. When the markdown body contains a plain link whose text matches one of the patterns, the renderer promotes it to a styled button using `cta_bg` and `cta_text`. Inline links that don't match (e.g. "[FAQ](https://example.com/faq)") stay as plain text links.

## How matching works

The renderer's matching rule (in `scripts/python/ac_builder/render/md_to_mjml_body.py`) is:

> Strip trailing decorations (right-arrows, en-dashes, ellipses) from the link text, lowercase it, and check whether any pattern in `cta_patterns` lowercased equals the result.

It's a **case-insensitive equals match** with trailing-arrow tolerance, not a substring contains. Two consequences:

- **"Register now"** in `cta_patterns` matches a link whose text is `Register now`, `REGISTER NOW`, or `register now`. It does **not** match `Register today` or `Click to register now`.
- **"Register now ->"** in markdown matches the pattern `Register now` because the trailing arrow gets stripped.

A second condition: if the link's URL matches the theme's `urls.sales_page` (ignoring query string differences), it's auto-promoted regardless of link text. This is the "primary CTA always wins" fallback.

## What this means for your theme

You need to enumerate the **exact CTA phrases** your brand uses across the sequence. If the sequence has 12 emails and each one ends with "Hold my seat" or "Register now" or "Apply for the residency", those three phrases need to be in `cta_patterns` for the buttons to render correctly.

If a sentence in the body has a CTA phrase you forgot to add to `cta_patterns`, the link still works but renders as a plain hyperlink instead of a button. Easy to fix: add the phrase to the array, re-run `building-sequences --apply`, the campaign updates with the new styling.

## Example pattern arrays per archetype

### Corporate / B2B SaaS

```json
"cta_patterns": [
  "Get started",
  "Schedule a demo",
  "Talk to sales",
  "Book a meeting",
  "Learn more"
]
```

### Friendly startup / consumer SaaS

```json
"cta_patterns": [
  "Try it free",
  "Start your free trial",
  "Get my free account",
  "Show me how it works",
  "Sign up"
]
```

### Launch / pre-order / waitlist

```json
"cta_patterns": [
  "Claim your spot",
  "Join the waitlist",
  "Get early access",
  "I'm in",
  "Reserve my seat"
]
```

### Newsletter / editorial

```json
"cta_patterns": [
  "Read more",
  "Continue",
  "Subscribe",
  "Read the full post",
  "View"
]
```

### Course / education (iDD-style)

```json
"cta_patterns": [
  "Register now",
  "Reserve your spot",
  "Apply for the residency",
  "Hold my seat",
  "Yes, count me in",
  "Book the call",
  "Continue to checkout",
  "Tell me more"
]
```

(This is the actual `lpis` array.)

## Sizing the array

The optimum is "exactly the phrases that appear in your emails, no more". Practical guidance:

- **4-6 patterns** is typical for a single-product launch sequence
- **8-12 patterns** is fine if the sequence has varied CTAs across emails (pre-launch teaser, opening day, mid-cycle, final-day, last-chance)
- **20+ patterns** is a sign you're not standardising your CTA copy. Pick fewer phrases and use them consistently.

## Alternative: explicit button markers

If you don't want to rely on auto-detection, use explicit `[[button:Label|URL]]` markers in the markdown:

```markdown
Here's what to do next:

[[button:Hold my seat|https://example.com/checkout?cid=%CONTACTID%]]

If you'd rather chat first, just reply to this email.
```

Explicit markers always render as buttons regardless of `cta_patterns`. Use them when the CTA copy is one-off (e.g. a mid-email "Update your preferences" link that doesn't deserve to be in the global patterns).

`cta_patterns` is for the recurring CTAs that show up across the whole sequence. `[[button:...]]` is for the one-offs.

## When to override the starter's array

When you copy a starter (e.g. `corporate-blue`), you inherit its `cta_patterns`. Decision time:

- **Keep it as-is** if your CTA copy happens to overlap. No work needed.
- **Replace it entirely** if your brand voice is different. Erase the array and write your own.
- **Append to it** if you have additional patterns the starter doesn't cover. Appending is fine; the array just gets longer.

The matching is per-pattern, so a long array doesn't slow anything down. Optimise for "every CTA phrase you actually use is in here", not "the array is short".

## Debugging

If a button isn't rendering and you expected it to:

1. Run `ac-builder render <md-file> --email E1 --out /tmp/e1.html` and inspect the HTML
2. Look for the link in question - is it a plain `<a>` or a styled button block?
3. Check the link text in the markdown - exact characters, including any decoration?
4. Check `cta_patterns` in the theme - does the lowercased pattern equal the lowercased link text (after trailing-arrow strip)?
5. If still not matching: easiest fix is to use `[[button:Label|URL]]` to force it.

The renderer doesn't print warnings about unmatched links - they just stay plain. So visual inspection is the verification step.
