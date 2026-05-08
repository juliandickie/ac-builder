# Source markdown format

The ac-builder parser reads a single markdown file as one email sequence. The H1 heading is the sequence title. Each H2 section is one email. H3 sections inside each email carry the structured fields the renderer needs (subject lines, preview text, body). This document is the canonical specification for that format.

The parser implementation is in `scripts/python/ac_builder/parser.py`. The patterns and rules below are extracted directly from the regex used at parse time, so a working source MD file should round-trip cleanly through `parse_md_file_with_metadata()`.

## Document structure

```
# Sequence Title                <-- H1 (one per file)

**Field:** value                <-- document-level metadata
**Other field:** value
...

## E1 - Email Title              <-- H2 starts an email section
**Send date:** ...               <-- per-email metadata
### Subject Line Options         <-- structured H3 sections
### Preview Text
### Email Body

## E2 - Next Email Title         <-- next H2 starts the next email
...
```

The parser sees the file as: a header (everything before the first H2), followed by one or more H2-delimited email sections. Each email section is parsed independently into an `EmailDef` object. The header is parsed once into a `SequenceMetadata` object.

## Document header

Everything before the first H2 is the document header. The parser extracts:

### H1 title

Becomes the sequence title (`SequenceMetadata.title`). Used in logs and skill prompts; not inserted into rendered emails.

### Document metadata

Every line matching `**field:** value` is captured into `SequenceMetadata.fields` as a key-value pair. Keys are lowercased and have spaces replaced with underscores at parse time.

```markdown
**Campaign name:** `implant-pathway-2026-aunz`
**Send dates:** April 27 - June 1, 2026
**Voice:** Dr Ahmad Al-Hassiny, first person, peer-to-peer
**Audience:** ~6,000 AU/NZ contacts
```

After parsing, `metadata.fields` holds:

```python
{
    "campaign_name": "implant-pathway-2026-aunz",
    "send_dates": "April 27 - June 1, 2026",
    "voice": "Dr Ahmad Al-Hassiny, first person, peer-to-peer",
    "audience": "~6,000 AU/NZ contacts",
}
```

### Special: the `Campaign name` field

The campaign name (the GA `utm_campaign` slug) drives analytics tagging on every campaign in the sequence. The parser supports two field-name conventions:

- `**Campaign name:** ...` (used in the AU/NZ launch MDs)
- `**AC Campaign name:** ...` (used in onboarding / abandon-cart / transition MDs)

Both resolve to `SequenceMetadata.campaign_name`. Backticks wrapping the slug are stripped automatically (`` `implant-pathway-2026-aunz` `` parses identically to the unquoted form).

This field is mandatory for sequences that need analytics. If absent, AC won't apply utm_campaign automatically.

## Per-email H2 section

The H2 line declares one email:

```markdown
## E1 - Title of the Email
```

The parser uses this regex (from `_H2_PATTERN`):

```
^## (?P<code>[\w-]+) [—-] (?P<title>.+?)$
```

Match anatomy:

- `##` - H2 marker
- `code` - one or more word characters / hyphens (e.g., `E1`, `WL-1`, `C1`, `G1`, `LPIS-OB-1`)
- `[—-]` - separator: an em-dash (`—`, U+2014) OR a hyphen (`-`)
- `title` - free text up to end of line

Both em-dashes and hyphens are accepted as separators. Per project convention, prefer hyphen (`## E1 - Title`); em-dash is supported for legacy iDD source files that were authored with em-dashes.

### Per-email metadata

Lines matching `**field:** value` between the H2 and the first H3 are captured into the email's metadata dict (`EmailDef.metadata`):

```markdown
## E1 - Segmentation Call-Out

**Send date:** Monday April 27, 2026
**Send to:** Full AU/NZ list (~6,000 contacts)
**Themeplate:** TP01 - The Exclusively Empowered Call-Out
**Job:** Self-selection, exclusive empowerment, open consistency loop.

### Subject Line Options
...
```

Once the parser hits the first H3, metadata extraction stops - all later `**field:**` lines are part of body content.

## `### Subject Line Options` block

A numbered list of subject line candidates. The parser captures the bolded text from each line:

```markdown
### Subject Line Options

1. **First subject line option** (rationale text in parens, ignored by parser)
2. **Second subject line option** (rationale)
3. **Third subject line option** (rationale)
```

Pattern (from `_SUBJECT_LINE_PATTERN`):

```
^\d+\. \*\*(?P<subject>.+?)\*\*
```

Rules:

- Must be a numbered list (`1.`, `2.`, `3.`)
- Subject text must be wrapped in `**bold**`
- Whatever text follows the closing `**` is preserved in the source MD but ignored by the parser - good for rationale notes
- The first option becomes `EmailDef.primary_subject` (the recommended subject used at campaign creation time)
- All options are stored in order in `EmailDef.subject_lines`
- Three options is the project convention but the parser accepts any count >= 0

## `### Preview Text` block

The preview / preheader text for the email (the snippet that appears under the subject in the inbox):

```markdown
### Preview Text

"You know the anatomy. You know the prosthetics. There's one thing you haven't done yet."
```

Rules:

- Quote marks are stripped at parse time. Both straight (`"..."`) and smart (`"..."`) quotes are supported.
- Only the first non-empty line is captured.
- Empty preview text is allowed but discouraged - some clients render the start of the body in its place, which can include merge field placeholders.

## `### Email Body` block

The email body in markdown. Extends from the H3 line until the next H3 (any kind), the next H2, or end of file:

```markdown
### Email Body

Hey %FIRSTNAME|TITLECASE%,

Something is coming that I've been working on for a while now...

[Continue to checkout](https://example.com/product?cid=%CONTACTID%)

Talk soon,
Ahmad
```

Trailing `---` (markdown horizontal-rule dividers) at the end of the body are stripped during parse.

## Body markdown features

Standard CommonMark works in the body. Specific patterns the renderer recognises:

### Standard markdown

- Paragraphs (blank-line-separated)
- `**bold**`, `*italic*`
- Numbered and bulleted lists
- `[link text](https://url.example)` inline links
- `> blockquote`
- `# H1`, `## H2`, `### H3` (rendered as styled headings inside the email)
- Horizontal rules `---`

### AC merge fields

Merge fields are passed through verbatim. ActiveCampaign substitutes them at send time:

| Field | Renders as |
|---|---|
| `%FIRSTNAME%` | Contact's first name (raw casing) |
| `%FIRSTNAME\|TITLECASE%` | First name with normalised title case |
| `%CONTACTID%` | Numeric contact ID (used in `?cid=` query params) |
| `%UNSUBSCRIBELINK%` | AC's mandatory unsubscribe URL |
| `%SENDER-INFO%` | AC's mandatory CAN-SPAM postal address block |
| `%LPIS_PURCHASE_DATE%` | Custom field value (project-specific) |

Project convention: use `%FIRSTNAME|TITLECASE%` everywhere personal-name interpolation appears, so "JOHN" or "john" both render as "John".

### Conditional content

ActiveCampaign's conditional syntax is preserved verbatim through the renderer:

```markdown
%IF !empty($SPECIALTY)%
You mentioned you specialise in %SPECIALTY%.
%ELSE%
Whatever you specialise in,
%/IF%
```

The parser does not validate the conditional - it just preserves the text. AC evaluates it at send time.

### Explicit CTA buttons

Use the `[[button:Text|url]]` marker to force a styled button regardless of CTA pattern matching:

```markdown
[[button:Hold my seat|https://example.com/seat?cid=%CONTACTID%]]
```

This gets converted to `<mj-button>` with `theme.colors.cta_bg` background and `theme.colors.cta_text` text colour.

### Auto-detected CTA buttons

A standard markdown link is auto-promoted from inline anchor to styled CTA button when EITHER condition fires:

1. Link text matches one of `theme.cta_patterns` (case-insensitive, with trailing arrows like `→` / `->` / `»` stripped before comparison).
2. Link URL matches `theme.urls.sales_page` (compared up to the first `?`, so query string differences including `%CONTACTID%` substitution don't break the match).

The matching algorithm is exact-equality after normalisation, not substring: `[Register now](...)` matches the pattern `"Register now"` but not `"Register"`. To force a button when neither rule fires, use the `[[button:Text|url]]` marker.

In practice: list every CTA phrase you actually use in `theme.cta_patterns` and let auto-detection handle 95% of buttons. Reach for `[[button:...]]` only for one-offs.

## Split-send sections

When one H2 carries two `### Email Body` blocks with annotations, the parser splits the email into multiple campaigns - one per body block. Useful for AM/PM sends, time-zone variants, A/B subject tests with body changes:

```markdown
## G12 - Final Day Triple Send

### Subject Line Options

1. **Final hours**
2. **Last call**

### Preview Text

"Cart closes tonight."

### Email Body (Morning Send - 8am EST)

Morning copy here...

### Email Body (Evening Send - 8pm EST)

Evening copy here, more urgent...
```

Parser behaviour:

- Detects multiple `### Email Body (label)` headings under one H2
- Emits one EmailDef per body, codes suffixed `a`, `b`, `c`...
- For the example above: `G12a` titled `Final Day Triple Send (Morning Send - 8am EST)` and `G12b` titled `Final Day Triple Send (Evening Send - 8pm EST)`
- Both share the H2's subject lines + preview text
- Bodies differ
- The annotation regex pattern: `^### Email Body(\s*\((?P<label>.+?)\))?\s*$`

If you want two campaigns sharing a subject but different copy, use this pattern. If you need fully separate campaigns (different subjects, different sends), use two H2 sections instead.

## Parser gotchas

Things that look like they should work but don't, ranked by frequency:

| Gotcha | Symptom | Fix |
|---|---|---|
| Subject line not bolded with `**...**` | Subject lines parse as empty | Wrap each subject in `**bold**`. The bold is mandatory. |
| Preview text not on its own line after the H3 | Preview parses as empty | Put the preview text on the line after `### Preview Text`, not the same line. |
| Preview text without quote marks | Quote marks not stripped (because there were none) - body parses normally | Wrap preview in `"..."`. Quotes are stripped during parse but not required - only required for project-style consistency. |
| Email body content directly under H2 with no `### Email Body` heading | Section parses with empty body, raises `'### Email Body' section not found or empty` | Add `### Email Body` before the body content. |
| H2 separator is wrong character (en-dash, slash, colon) | H2 doesn't match, section is silently dropped | Use hyphen (`-`) per project convention, or em-dash (`—`) for legacy compatibility. |
| Metadata field after the first H3 | Field is ignored | Move all `**field:** value` lines to between the H2 and the first H3. |
| Markdown link text doesn't match `cta_patterns` | Link renders as inline anchor, not button | Add the phrase to `theme.cta_patterns`, or use `[[button:Text\|url]]` syntax. |
| Two `### Email Body` blocks where you wanted one | Parser splits into A/B campaigns | Either remove the second block, or rename to `### Email Body (Section name)` so the labels are explicit. |

## Full example

A 2-email sequence with all features used:

```markdown
# Sample Onboarding Sequence

**Campaign name:** `sample-onboarding-2026`

**Send dates:** Triggered immediately after purchase + 3-day cadence

**Voice:** Founder, first person, casual

**Audience:** Customers who just bought the product

---

## OB-1 - Welcome and Login

**Send date:** Triggered (immediate on purchase)

**Send to:** New purchasers

**Themeplate:** Custom

**Job:** Welcome, login link, set expectations

### Subject Line Options

1. **You're in! Here's what happens next, %FIRSTNAME|TITLECASE%** (Personal, immediate, sets up the next email)

2. **Welcome to the program** (Plain, low-risk)

3. **Quick login + your first step** (Action-oriented)

### Preview Text

"Login link inside, plus a one-minute video on what to do first."

### Email Body

Hey %FIRSTNAME|TITLECASE%,

Thanks for joining! Your account is set up and ready.

Here's what happens next:

1. Click the login link below.
2. Watch the welcome video (it's two minutes).
3. Pick your first module.

[[button:Take me to my dashboard|https://example.com/dashboard?cid=%CONTACTID%]]

If you hit any snags, just reply to this email - I read every reply.

Talk soon,
Sarah

---

## OB-2 - First module check-in

**Send date:** 3 days after OB-1

**Send to:** OB-1 recipients who haven't completed the first module

**Themeplate:** Custom

**Job:** Re-engage, lower the bar

### Subject Line Options

1. **Have you started yet, %FIRSTNAME|TITLECASE%?**

2. **Just five minutes is enough**

3. **A small nudge**

### Preview Text

"You don't have to finish it. Just open it."

### Email Body

Hey %FIRSTNAME|TITLECASE%,

Quick check-in. I noticed you haven't opened the first module yet.

%IF !empty($SPECIALTY)%
I know you're busy with %SPECIALTY% work.
%ELSE%
I know you're busy.
%/IF%

But the first module is short - five minutes. You don't have to finish anything. Just open it and watch the intro.

[Continue to checkout](https://example.com/product?cid=%CONTACTID%)

That's it. Then close the tab and come back when you're ready.

Talk soon,
Sarah

P.S. - If you'd rather not hear from me, [click here](https://example.com/not-interested?cid=%CONTACTID%). No hard feelings.
```

Parser output for this file (simplified):

```
SequenceMetadata(
    title="Sample Onboarding Sequence",
    fields={
        "campaign_name": "sample-onboarding-2026",
        "send_dates": "Triggered immediately after purchase + 3-day cadence",
        "voice": "Founder, first person, casual",
        "audience": "Customers who just bought the product",
    },
)

[
    EmailDef(
        code="OB-1",
        title="Welcome and Login",
        subject_lines=[
            "You're in! Here's what happens next, %FIRSTNAME|TITLECASE%",
            "Welcome to the program",
            "Quick login + your first step",
        ],
        preview_text="Login link inside, plus a one-minute video on what to do first.",
        body_md="Hey %FIRSTNAME|TITLECASE%,\n\nThanks for joining!...",
        metadata={
            "send_date": "Triggered (immediate on purchase)",
            "send_to": "New purchasers",
            "themeplate": "Custom",
            "job": "Welcome, login link, set expectations",
        },
    ),
    EmailDef(
        code="OB-2",
        title="First module check-in",
        ...
    ),
]
```

## Cross-references

- Parser code: `scripts/python/ac_builder/parser.py`
- Renderer (markdown -> MJML): `scripts/python/ac_builder/render/md_to_mjml_body.py`
- Theme schema: `docs/theme-schema.md` and `themes/_schema.json`
- Real-world examples: any file under `output/emails-au-nz/`, `output/emails-onboarding/`, etc. in the LPIS / IIDF / ASIMR project repo
