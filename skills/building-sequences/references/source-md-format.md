# Source MD format reference

The canonical structure ac-builder's parser expects for source markdown files. One file per sequence; one `## E<code>` section per email.

## Document header

The top of the file describes the sequence as a whole. The parser is forgiving here, but the fields it actually reads are:

- **H1 title** (`# Sequence Name`) - for human reference; not read by the parser
- **`Campaign name:`** field - sets the AC `Campaign name` (used as a UTM-style identifier on tracked links). Wrap in backticks for readability:
  ```markdown
  **Campaign name:** `implant-pathway-2026-iidf-branch-c`
  ```
  The `--utm-campaign` CLI flag overrides this if passed.

Other lines like Subsequence, Send dates, Audience, Voice, Pricing, etc. are documentation for humans authoring the sequence. The parser ignores them.

## Per-email section

Each email is an `## E<code>` H2 section. The code becomes the source identifier for the email (used in `--emails` filtering and the output table). Both em-dash and hyphen separators work:

```markdown
## E1 - Segmentation Call-Out
## E1 — Segmentation Call-Out
```

The full email name in AC is composed from the sequence + code + title.

### Per-email metadata fields

These come right after the H2 line. Format is `**field:** value`. Parser-recognised fields:

- **`Send date:`** - human-readable date string (informational; not used by ac-builder for scheduling)
- **`Theme:`** - per-email theme override (e.g. `lpis`, `iidf`, `asimr` or a custom theme name). Overrides the file-level theme inference for this email only.

Other fields like `Themeplate:`, `Job:`, `Audit patches applied:` are documentation for human authors. They are not parsed.

## Required sub-sections

Each email H2 must contain three sub-sections under H3 headings:

### Subject Line Options

A numbered list. The first option is used as the campaign subject. The bold span sets the actual subject text; trailing text is treated as an authoring rationale.

```markdown
### Subject Line Options

1. **Your hands-on starting point** (Direct, benefit-oriented)

2. **Two days in Auckland. July 3-4.** (Specificity, no hype)

3. **The pig jaw course is open** (Plain-spoken)
```

Multiple subject options are good practice for A/B authoring; only the first is wired to the campaign.

### Preview Text

The preheader text shown in the inbox preview pane. Either bare text or text in quotes works:

```markdown
### Preview Text

Auckland, July 3-4. Day 1 theory with me. Day 2 hands-on pig jaw surgery.
```

Preview text inherits the same merge field support as body content.

### Email Body

The body content as standard markdown. Supports paragraphs, bold/italic, lists, links, plus AC-specific features described below.

```markdown
### Email Body

%FIRSTNAME|TITLECASE%,

You told me in the last email that you want hands-on practice...
```

The body section runs until the next `##` (next email or end of file).

## Body content features

### AC merge fields

Standard ActiveCampaign personalisation tokens, used inline:

- `%FIRSTNAME|TITLECASE%` - first name with TitleCase normalisation
- `%CONTACTID%` - the contact's AC ID; used as a cid query parameter on tracked links
- `%UNSUBSCRIBELINK%` - one-click unsubscribe link (rendered in the footer)
- `%SENDER-INFO%` - sender physical address block (rendered in the footer)

Custom fields use `%FIELD_NAME%` (all caps).

### Conditional content

Wrap personalised blocks in AC's IF/ELSE/ENDIF syntax. Only renders the matched branch:

```markdown
%IF !empty($SPECIALTY)%
Hi %FIRSTNAME|TITLECASE%, since you work in %SPECIALTY%, this matters even more.
%ELSE%
Hi %FIRSTNAME|TITLECASE%.
%/IF%
```

### Explicit CTA buttons

Force a specific link to render as a styled button using the `[[button:Label|URL]]` syntax:

```markdown
[[button:Hold my seat|https://example.com/checkout?cid=%CONTACTID%]]
```

The button gets the theme's primary CTA styling. The label and URL are required, separated by `|`.

### Auto-detected CTAs

The renderer also auto-promotes plain markdown links to button styling when their URL matches one of the patterns in the theme's `cta_patterns` config. For example, an LPIS theme might match URLs containing `/sales/lpis` or `/checkout`. Inline links to your blog, FAQ, etc. stay as plain text links. See `theme-resolution.md` for how patterns are configured.

### Standard markdown

The renderer supports standard markdown bold (`**`), italic (`*`), unordered lists (`- `), ordered lists (`1. `), inline links (`[text](url)`), and paragraphs (blank-line separated). HTML pass-through is intentionally limited; if you find yourself wanting raw HTML, that's usually a sign the theme should be enhanced instead.

## Split-send sections

For emails that send the same content at two different times (e.g. a morning + evening send on the same day), use two body sections under one H2 with explicit time labels:

```markdown
## G12 - Final-day double tap

### Subject Line Options

1. **Final hours**

### Preview Text

This is your last chance.

### Email Body (Morning Send - 8am EST)

Morning version of the body...

### Email Body (Evening Send - 8pm EST)

Evening version with last-call urgency...
```

The orchestrator splits this into two campaigns: `G12a` (morning) and `G12b` (evening). Both are independently created and validated. Filter to one with `--emails G12a`.

## Tips

- Keep each email under ~500 words of body for readability
- Use H3 (`###`) inside body sparingly; the renderer styles them but they break visual hierarchy in narrow inboxes
- Test merge fields with realistic-looking data; an empty `%FIRSTNAME|TITLECASE%` should still produce a sentence that reads naturally
- The first subject line is the one that ships - don't bury the recommended one at position 3
