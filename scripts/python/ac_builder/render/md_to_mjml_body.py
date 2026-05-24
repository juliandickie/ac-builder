"""Convert markdown email body content to an MJML body fragment.

Input: markdown source (the `### Email Body` content from a source MD).
Output: MJML body fragment containing one or more <mj-section> blocks.

Behaviour:
  - Paragraphs → <mj-text>
  - h2/h3/h4 → styled <mj-text> (h2 with gold accent stripe, h3 primary color)
  - h1 is dropped (treated as email title)
  - hr → <mj-divider>
  - Lists (ul/ol) → <mj-text> containing styled <ul>/<ol>
  - Inline links → <a> inside <mj-text>
  - Paragraph-only links matching theme.cta_patterns OR pointing at the
    theme's sales_page → <mj-button> (bulletproof VML in Outlook)
  - [[button:Text|url]] markers → <mj-button>
  - === Section Title === on its own line → coloured strip <mj-section>
  - > Blockquote → cream callout box with accent left border
  - AC merge fields preserved verbatim
  - Conditional content (%IF%...%/IF%) wrapped in <mj-raw>

Output structure: regular content blocks (text, headings, lists, dividers,
buttons) are grouped into a single <mj-section><mj-column>...</mj-column></mj-section>
wrapper. Special blocks (strip, callout) emit their own full-width section
between content sections. base.mjml accepts a sequence of sections.
"""
from __future__ import annotations

import base64
import html as html_module
import re

from markdown_it import MarkdownIt
from markdown_it.token import Token

from ac_builder.render.theme_loader import ThemeData

_HEADING_SIZES = {2: "24px", 3: "20px", 4: "18px"}

# Bottom-only padding model: every block has top=0 and a per-level bottom.
# This makes the gap above any block come entirely from the previous block's
# bottom padding (typically 16px from mj-text default). One value per
# transition, no stacking.
#
# Bottom padding scales with heading weight: h2 gets 16px (matches body
# rhythm, separates from following content). h3 gets 12px (tighter, groups
# with its content). h4 gets 8px (smallest, subordinate).
_HEADING_BOTTOM_PAD = {2: "16px", 3: "12px", 4: "8px"}


def md_to_mjml_body(md: str, *, theme: ThemeData) -> str:
    """Convert a markdown body to an MJML body fragment.

    Returns empty string if md is empty/whitespace-only.

    Output is a sequence of <mj-section> blocks. Regular content (text,
    headings, lists, dividers, buttons) is grouped into one wrapper section
    per run; special blocks (strip, callout, pillars) each emit their own
    section.
    """
    md = (md or "").strip()
    if not md:
        return ""

    blocks = _render_blocks(md, theme=theme)
    return _assemble_sections(blocks)


def _render_blocks(
    md: str, *, theme: ThemeData, inside_pillar: bool = False
) -> list[tuple[str, str]]:
    """Return a list of (kind, html) tuples without the outer section wrapper.

    Used by md_to_mjml_body via _assemble_sections, and by _emit_pillar_row
    for recursive per-column rendering. Returning the raw block list lets
    callers either wrap (the top-level body) or concatenate (column inner
    content where the wrapper is provided by mj-section/mj-column).

    `inside_pillar` is forwarded through paragraph emit to button emit so
    buttons rendered inside a pillar column use tighter padding than
    standalone CTA buttons (the global mj-button defaults are tuned for
    full-width centered buttons, not narrow column buttons).
    """
    md = _preprocess_button_markers(md)
    md = _preprocess_strip_markers(md)
    md = _preprocess_pillars_markers(md)

    parser = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})
    # Disable URL normalization so AC merge fields like %CONTACTID% in hrefs
    # aren't percent-encoded to %25CONTACTID%25.
    parser.normalizeLink = lambda url: url
    parser.validateLink = lambda url: True
    tokens = parser.parse(md)

    # Each entry is (kind, html). kind is "content" (gets bundled into a
    # wrapper mj-section) or "section" (already a complete mj-section).
    blocks: list[tuple[str, str]] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok.type == "paragraph_open":
            inline = tokens[i + 1]
            kind, html = _emit_paragraph_block(inline, theme, inside_pillar=inside_pillar)
            if html:
                blocks.append((kind, html))
            i += 3
            continue

        if tok.type == "heading_open":
            level = int(tok.tag[1])
            inline = tokens[i + 1]
            if level != 1:
                html = _emit_heading(level, inline, theme, inside_pillar=inside_pillar)
                if html:
                    blocks.append(("content", html))
            i += 3
            continue

        if tok.type == "hr":
            blocks.append((
                "content",
                '<mj-divider border-color="#dddddd" border-width="1px" padding="16px 0" />',
            ))
            i += 1
            continue

        if tok.type in ("bullet_list_open", "ordered_list_open"):
            list_tag = "ol" if tok.type == "ordered_list_open" else "ul"
            close_type = tok.type.replace("_open", "_close")
            depth = 1
            j = i + 1
            while j < len(tokens) and depth > 0:
                if tokens[j].type == tok.type:
                    depth += 1
                elif tokens[j].type == close_type:
                    depth -= 1
                if depth > 0:
                    j += 1
            list_tokens = tokens[i + 1 : j]
            html = _emit_list(list_tag, list_tokens, theme)
            if html:
                blocks.append(("content", html))
            i = j + 1
            continue

        if tok.type == "blockquote_open":
            close_type = "blockquote_close"
            depth = 1
            j = i + 1
            while j < len(tokens) and depth > 0:
                if tokens[j].type == "blockquote_open":
                    depth += 1
                elif tokens[j].type == close_type:
                    depth -= 1
                if depth > 0:
                    j += 1
            html = _emit_callout(tokens[i + 1 : j], theme)
            if html:
                blocks.append(("section", html))
            i = j + 1
            continue

        i += 1

    return blocks


def _assemble_sections(blocks: list[tuple[str, str]]) -> str:
    """Group consecutive content blocks into wrapper sections; emit standalone
    sections between them.

    Vertical rhythm: every wrapper section uses symmetric 16px top/bottom
    padding. Combined with mj-text's default 16px bottom on each paragraph,
    this gives a consistent gap to the next strip/callout/pillar regardless
    of which side you measure from.

    Horizontal: 16px L/R gutter so content has breathing room from the email
    body edge without losing too much content width.
    """
    out: list[str] = []
    content_run: list[str] = []

    def flush_content():
        if not content_run:
            return
        inner = "\n".join(content_run)
        # Bottom is 0: the next section (strip/callout/pillar/footer) provides
        # its own top padding. The last paragraph's mj-text default 16px bottom
        # padding gives breathing room. This keeps gaps symmetric across both
        # sides of any standalone section.
        out.append(
            f'<mj-section padding="16px 16px 0 16px"><mj-column>\n'
            f'{inner}\n'
            f'</mj-column></mj-section>'
        )
        content_run.clear()

    for kind, html in blocks:
        if kind == "section":
            flush_content()
            out.append(html)
        else:
            content_run.append(html)
    flush_content()

    return "\n".join(out)


_BUTTON_MARKER_RE = re.compile(r"\[\[button:(?P<text>[^|\]]+?)\|(?P<href>[^\]]+?)\]\]")


def _preprocess_button_markers(md: str) -> str:
    """Replace [[button:Text|url]] markers with a sentinel that survives markdown parsing."""
    def _sub(m: re.Match) -> str:
        text = m.group("text").strip()
        href = m.group("href").strip()
        return f"@@AC_BUTTON@@{text}@@HREF@@{href}@@END@@"
    return _BUTTON_MARKER_RE.sub(_sub, md)


_BUTTON_SENTINEL_RE = re.compile(r"@@AC_BUTTON@@(?P<text>.+?)@@HREF@@(?P<href>.+?)@@END@@")


# Section strip syntax: a line containing only `=== Title ===` becomes a thin
# coloured banner. Three or more `=` on each side, optional spaces inside.
# Use [ \t]* (horizontal whitespace only) - \s* would eat surrounding newlines
# and collapse the blank lines that markdown needs to recognize paragraph breaks.
_STRIP_LINE_RE = re.compile(r"^[ \t]*={3,}[ \t]*(?P<text>[^=].*?[^=])[ \t]*={3,}[ \t]*$", re.MULTILINE)


def _preprocess_strip_markers(md: str) -> str:
    """Replace `=== Title ===` lines with a sentinel that survives markdown parsing.

    Markdown-it would normally parse `=== Title ===` as a paragraph (it isn't
    setext heading syntax, which is `Title\n===`), so the sentinel approach is
    the cleanest interception point.
    """
    def _sub(m: re.Match) -> str:
        text = m.group("text").strip()
        return f"@@AC_STRIP@@{text}@@END@@"
    return _STRIP_LINE_RE.sub(_sub, md)


_STRIP_SENTINEL_RE = re.compile(r"@@AC_STRIP@@(?P<text>.+?)@@END@@")


# Pillar row syntax: a fenced block with `+++` separators between columns.
#   :::pillars
#   ### Column 1 heading
#   Body markdown
#   **[CTA →](url)**
#   +++
#   ### Column 2 heading
#   ...
#   :::
#
# Each column's content is full markdown - rendered recursively through
# _render_blocks so headings get the gold stripe, buttons render bulletproof,
# AC merge fields pass through, etc.
#
# DOTALL so `.` matches newlines; non-greedy so two consecutive blocks don't
# accidentally merge.
_PILLARS_FENCE_RE = re.compile(
    r"^[ \t]*:::pillars[ \t]*\n(?P<inner>.*?)\n[ \t]*:::[ \t]*$",
    re.MULTILINE | re.DOTALL,
)


def _preprocess_pillars_markers(md: str) -> str:
    """Replace `:::pillars ... :::` blocks with a base64-encoded sentinel.

    base64 encoding is used because the inner markdown could contain anything
    (pipes, brackets, AC merge fields, even nested sentinels from the button
    or strip preprocessors). Encoding sidesteps the question of "what
    characters survive markdown parsing" entirely.

    Empty pillars blocks (no content between fences) are dropped silently.
    """
    def _sub(m: re.Match) -> str:
        inner = m.group("inner").strip()
        if not inner:
            return ""
        encoded = base64.b64encode(inner.encode("utf-8")).decode("ascii")
        return f"@@AC_PILLARS@@{encoded}@@END@@"
    return _PILLARS_FENCE_RE.sub(_sub, md)


_PILLARS_SENTINEL_RE = re.compile(r"@@AC_PILLARS@@(?P<payload>[A-Za-z0-9+/=]+)@@END@@")


def _emit_paragraph_block(
    inline_tok: Token, theme: ThemeData, *, inside_pillar: bool = False
) -> tuple[str, str]:
    """Render a paragraph as one of: button, strip, conditional, or text.

    Returns (kind, html) where kind is "section" for full-width blocks
    (strip) and "content" for things that go inside the bundled wrapper
    (text, button, conditional). Empty (kind, "") if the paragraph is blank.

    `inside_pillar` propagates to button emission so pillar-column buttons
    render with tighter padding.
    """
    text_html = _render_inline_to_html(inline_tok, theme)
    if not text_html.strip():
        return ("content", "")

    if _looks_like_ac_conditional(text_html):
        return ("content", f'<mj-raw>{text_html}</mj-raw>')

    pillars = _PILLARS_SENTINEL_RE.search(text_html)
    if pillars:
        try:
            inner_md = base64.b64decode(pillars.group("payload")).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return ("content", "")
        return ("section", _emit_pillar_row(inner_md, theme))

    strip = _STRIP_SENTINEL_RE.search(text_html)
    if strip:
        return ("section", _emit_section_strip(strip.group("text"), theme))

    sentinel = _BUTTON_SENTINEL_RE.search(text_html)
    if sentinel:
        return ("content", _emit_button(
            sentinel.group("text"), sentinel.group("href"), theme,
            inside_pillar=inside_pillar,
        ))

    button = _try_extract_cta_button(inline_tok, theme, inside_pillar=inside_pillar)
    if button:
        return ("content", button)

    return ("content", f'<mj-text>{text_html}</mj-text>')


_INLINE_EMPHASIS_WRAPPERS = {
    "strong_open", "strong_close", "em_open", "em_close",
    "s_open", "s_close",
}

# Decorative trailing characters commonly added to CTA link text:
# arrows, punctuation, whitespace. Preserved in the rendered button label
# (they look great there) but stripped before pattern matching.
_CTA_TRAILING_DECORATIONS = " \t .,;:!?→➔➜»>→⇒➤-"


def _try_extract_cta_button(
    inline_tok: Token, theme: ThemeData, *, inside_pillar: bool = False
) -> str | None:
    """Promote a paragraph-only link to a button when:

    1. The paragraph contains exactly one link after stripping bold/italic
       emphasis wrappers and empty-text padding.
    2. EITHER the link text (with trailing arrows/punctuation stripped)
       matches one of `theme.cta_patterns`, OR the link URL is the theme's
       primary `sales_page` (or any URL listed in `theme.cta_url_overrides`).

    This is permissive on purpose: authors write `**[Count me in →](sales_page)**`,
    not `[Register now](sales_page)`. We trust their intent when the URL is
    a known CTA destination.
    """
    children = inline_tok.children or []
    meaningful = [
        c for c in children
        if not (c.type == "text" and not c.content.strip())
        and c.type not in _INLINE_EMPHASIS_WRAPPERS
    ]

    # After unwrapping emphasis we expect exactly: link_open, text, link_close
    if len(meaningful) != 3:
        return None
    if meaningful[0].type != "link_open" or meaningful[2].type != "link_close":
        return None
    if meaningful[1].type != "text":
        return None

    link_text = meaningful[1].content.strip()
    href = meaningful[0].attrGet("href") or ""

    if not (_matches_cta_pattern(link_text, theme) or _url_is_primary_cta(href, theme)):
        return None
    return _emit_button(link_text, href, theme, inside_pillar=inside_pillar)


def _matches_cta_pattern(text: str, theme: ThemeData) -> bool:
    """True when `text` (with trailing decorations stripped) equals a CTA pattern."""
    norm = text.strip().rstrip(_CTA_TRAILING_DECORATIONS).strip().lower()
    if not norm:
        return False
    return any(p.lower() == norm for p in theme.cta_patterns)


def _url_is_primary_cta(href: str, theme: ThemeData) -> bool:
    """True when the URL matches the theme's sales page (ignoring AC merge-field
    differences in the query string).

    Compares only the URL up to the first '?' so that variations in query
    parameters - including %CONTACTID% substitution - don't break matching.
    """
    if not href:
        return False
    sales_page = (theme.urls or {}).get("sales_page", "")
    if not sales_page:
        return False
    return href.split("?", 1)[0] == sales_page.split("?", 1)[0]


def _emit_button(
    text: str, href: str, theme: ThemeData, *, inside_pillar: bool = False
) -> str:
    """Render an MJML button. Theme provides bg + text colors via mj-attributes default.

    Standalone (default): centered, 24px vertical outer padding for breathing
    room, generous inner-padding inherited from global mj-button defaults
    (16px / 32px). Reads as the page's primary action.

    Pillar context (`inside_pillar=True`): tighter outer + inner padding and
    smaller font so the button fits cleanly inside a ~180px column without
    forcing the text to wrap to 3 lines. The overrides also reduce the
    line-height ("line-height" attribute) so wrapped text stays compact.
    """
    safe_text = html_module.escape(text)
    safe_href = _escape_href(href)

    if inside_pillar:
        # No outer padding - the column's own padding-bottom (16px) provides
        # the gap below the button to the column edge, and the body text's
        # mj-text padding-bottom (16px) provides the gap above. Inner-padding
        # gives the click target its visual height.
        return (
            f'<mj-button href="{safe_href}" align="center" '
            f'padding="0" inner-padding="10px 14px" '
            f'font-size="14px" line-height="1.25">{safe_text}</mj-button>'
        )

    # Bottom-only model: top=0 (preceding paragraph's mj-text 16px bottom is
    # the gap above), 16px L/R for breathing room from email edges, 16px
    # bottom for the gap to the next section.
    return (
        f'<mj-button href="{safe_href}" align="center" '
        f'padding="0 16px 16px 16px">{safe_text}</mj-button>'
    )


def _emit_section_strip(text_html: str, theme: ThemeData) -> str:
    """Render a thin coloured banner section.

    Used as a chapter marker in long emails. Renders as:
      - mj-section with theme.colors.secondary (or primary) background, full width
      - mj-text inside: white, uppercase, letter-spacing tracked
      - 12px vertical padding (thin) so it reads as a band, not a header

    The `text_html` argument is HTML-safe (already escaped by the inline
    renderer when the sentinel marker was parsed). Do NOT escape again:
    that produces &amp;#x27; double-encoding which renders as literal text.

    Background color preference: secondary > primary. Using secondary
    differentiates the strip from any primary-colored CTA buttons,
    avoiding the "wall of navy" effect when both are stacked.

    bgcolor on the table cell is the most universally-supported style in
    HTML email; this works in Outlook 2007 Word engine through the new
    Outlook WebView2 without any special-casing.
    """
    bg = theme.colors.get("secondary") or theme.colors.get("primary", "#0a3d62")
    return (
        f'<mj-section background-color="{bg}" padding="14px 24px">'
        f'<mj-column>'
        f'<mj-text color="#ffffff" font-size="13px" font-weight="bold" '
        f'letter-spacing="1.5px" align="center" padding="0">'
        f'<span style="text-transform:uppercase;">{text_html}</span>'
        f'</mj-text>'
        f'</mj-column>'
        f'</mj-section>'
    )


def _emit_callout(inner_tokens: list[Token], theme: ThemeData) -> str:
    """Render a blockquote as a callout box: cream background, accent left border.

    Blockquote contents (one or more paragraphs) are rendered inline. Use cases:
    P.S. lines, testimonial pulls, key insights worth highlighting.

    The cream-tone background works in light mode; in dark mode the muted
    foreground keeps it readable. classic Outlook drops the border-left on
    the inner span (graceful degradation - the cream background still flags
    it as different).
    """
    accent = theme.colors.get("accent", theme.colors.get("primary", "#c7a200"))

    # Walk inner_tokens and render each paragraph's inline content.
    paragraph_htmls: list[str] = []
    i = 0
    while i < len(inner_tokens):
        tok = inner_tokens[i]
        if tok.type == "paragraph_open":
            inline = inner_tokens[i + 1]
            paragraph_htmls.append(_render_inline_to_html(inline, theme))
            i += 3
            continue
        i += 1

    if not paragraph_htmls:
        return ""

    body = "<br/><br/>".join(paragraph_htmls)
    return (
        f'<mj-section background-color="#fdf8ec" padding="20px 24px">'
        f'<mj-column>'
        f'<mj-text font-style="italic" line-height="1.6" padding="0">'
        f'<span style="display:inline-block; '
        f'border-left:4px solid {accent}; '
        f'padding-left:14px;">{body}</span>'
        f'</mj-text>'
        f'</mj-column>'
        f'</mj-section>'
    )


_PILLAR_COLUMN_SEP = re.compile(r"^[ \t]*\+{3,}[ \t]*$", re.MULTILINE)


def _emit_pillar_row(inner_md: str, theme: ThemeData) -> str:
    """Render a multi-column pillar row from markdown content.

    Splits inner_md by `+++` lines into columns, recursively renders each
    column's markdown via _render_blocks, and wraps the whole thing in
    <mj-section><mj-column> × N.

    MJML auto-distributes column widths (100% / N) and auto-stacks columns
    to single-column on viewports below 600px - no media queries needed
    in our code.

    Each column gets card_bg background and 16px padding to read as a
    distinct card. The section sits on the email body bg so the columns
    visually separate from each other.
    """
    columns_md = _PILLAR_COLUMN_SEP.split(inner_md)
    columns_md = [c.strip() for c in columns_md if c.strip()]
    if not columns_md:
        return ""

    card_bg = theme.colors.get("card_bg", "#ffffff")

    column_htmls = []
    for col_md in columns_md:
        col_blocks = _render_blocks(col_md, theme=theme, inside_pillar=True)
        # Inside a pillar column, suppress the "section" kind for nested
        # callouts/strips - they would create invalid nested mj-section
        # structure. Treat everything as content here.
        col_inner = "\n".join(html for _, html in col_blocks)
        # 12px top + 12px bottom on the column gives a 28px above-heading gap
        # (16 from preceding paragraph mj-text + 12 column top + 0 heading top)
        # and matching 28px below-button gap. Tighter than 16px column padding
        # but still visibly card-like.
        column_htmls.append(
            f'<mj-column background-color="{card_bg}" padding="12px 16px" '
            f'vertical-align="top" css-class="card-bg">\n'
            f'{col_inner}\n'
            f'</mj-column>'
        )

    # Section vertical padding is 0: the column's own padding provides the
    # card-edge breathing room, and the wrapper above/below contributes 16px
    # via its own top/bottom padding. Stacking section + column padding gave
    # ~48px above headings - excessive. Tight 8px L/R gives columns more
    # width inside the 600px frame.
    return (
        '<mj-section padding="0 8px">\n'
        + "\n".join(column_htmls)
        + '\n</mj-section>'
    )


_AC_CONDITIONAL_RE = re.compile(r"%IF\s|%ELSE%|%/IF%|%ELSEIF\s")


def _looks_like_ac_conditional(text: str) -> bool:
    """Return True if the text contains AC conditional content syntax."""
    return bool(_AC_CONDITIONAL_RE.search(text))


def _emit_heading(
    level: int, inline_tok: Token, theme: ThemeData, *, inside_pillar: bool = False
) -> str:
    """Render an h2/h3/h4 with theme-aware colour and an accent stripe on h2.

    Visual hierarchy:
      h2 - 24px, primary color, headings font, 4px gold left stripe
      h3 - 20px, primary color, headings font
      h4 - 18px, muted color, body font

    Padding follows the bottom-only model: top=0 always (gap above is
    provided by the previous block's bottom padding), bottom varies by
    level. `inside_pillar` is accepted for API symmetry but no longer
    affects padding - top is 0 everywhere.
    """
    text_html = _render_inline_to_html(inline_tok, theme)
    size = _HEADING_SIZES.get(level, "16px")
    bottom_pad = _HEADING_BOTTOM_PAD.get(level, "8px")

    body_font = theme.fonts["body"]
    headings_font = theme.fonts.get("headings", body_font)
    primary = theme.colors.get("primary", theme.colors["body_text"])
    accent = theme.colors.get("accent", primary)
    muted = theme.colors.get("muted", theme.colors["body_text"])

    if level == 2:
        # Gold accent stripe on the left for the major section marker.
        # The span is inline-block so the border-left renders in modern clients;
        # classic Outlook Word engine drops the border but keeps the bold colored
        # text - graceful degradation.
        font = headings_font
        color = primary
        inner = (
            f'<span style="display:inline-block; '
            f'border-left:4px solid {accent}; '
            f'padding-left:12px; line-height:1.25;">'
            f'{text_html}</span>'
        )
    elif level == 3:
        font = headings_font
        color = primary
        inner = text_html
    else:
        font = body_font
        color = muted
        inner = text_html

    return (
        f'<mj-text font-size="{size}" font-weight="bold" '
        f'color="{color}" '
        f'font-family="{html_module.escape(font, quote=True)}" '
        f'padding="0 0 {bottom_pad} 0">{inner}</mj-text>'
    )


def _emit_list(list_tag: str, inner_tokens: list[Token], theme: ThemeData) -> str:
    """Render a list (ul or ol) and its items to an mj-text block."""
    items_html: list[str] = []
    i = 0
    while i < len(inner_tokens):
        tok = inner_tokens[i]
        if tok.type == "list_item_open":
            j = i + 1
            depth = 1
            item_inlines: list[str] = []
            while j < len(inner_tokens) and depth > 0:
                child = inner_tokens[j]
                if child.type == "list_item_open":
                    depth += 1
                elif child.type == "list_item_close":
                    depth -= 1
                    if depth == 0:
                        break
                elif child.type == "inline":
                    item_inlines.append(_render_inline_to_html(child, theme))
                j += 1
            items_html.append(f"<li style=\"margin-bottom:8px;\">{' '.join(item_inlines)}</li>")
            i = j + 1
            continue
        i += 1

    style = (
        f'margin: 0 0 16px 24px; padding: 0; '
        f'font-family: {theme.fonts["body"]}; '
        f'color: {theme.colors["body_text"]}; '
        f'font-size: 16px; line-height: 1.6;'
    )
    return f'<mj-text><{list_tag} style="{style}">{"".join(items_html)}</{list_tag}></mj-text>'


def _render_inline_to_html(inline_tok: Token, theme: ThemeData) -> str:
    """Walk an inline token's children and produce HTML for use inside mj-text."""
    if not inline_tok.children:
        return _preserve_ac_tokens(inline_tok.content or "")

    parts: list[str] = []
    for child in inline_tok.children:
        if child.type == "text":
            parts.append(_preserve_ac_tokens(child.content))
        elif child.type == "softbreak":
            parts.append(" ")
        elif child.type == "hardbreak":
            parts.append("<br/>")
        elif child.type == "strong_open":
            parts.append("<strong>")
        elif child.type == "strong_close":
            parts.append("</strong>")
        elif child.type == "em_open":
            parts.append("<em>")
        elif child.type == "em_close":
            parts.append("</em>")
        elif child.type == "code_inline":
            parts.append(f"<code>{html_module.escape(child.content)}</code>")
        elif child.type == "link_open":
            href = child.attrGet("href") or ""
            parts.append(f'<a href="{_escape_href(href)}" style="color:{theme.colors["primary"]};">')
        elif child.type == "link_close":
            parts.append("</a>")
    return "".join(parts)


_AC_TOKEN_PATTERN = re.compile(r"(%[A-Z][A-Z0-9_|\-]*%|%IF .*?%|%ELSE%|%/IF%)")


def _preserve_ac_tokens(text: str) -> str:
    """Escape HTML special chars but leave AC merge tokens (%FOO%) untouched."""
    parts = _AC_TOKEN_PATTERN.split(text)
    out: list[str] = []
    for part in parts:
        if _AC_TOKEN_PATTERN.fullmatch(part):
            out.append(part)
        else:
            out.append(html_module.escape(part))
    return "".join(out)


def _escape_href(href: str) -> str:
    """Escape a URL for an href attribute, preserving AC merge tokens (%CONTACTID% etc).

    Standard html.escape would percent-encode the '%' in merge tokens; we split on the
    AC-token pattern and escape only the non-token parts so tokens survive verbatim.
    """
    parts = _AC_TOKEN_PATTERN.split(href)
    out: list[str] = []
    for part in parts:
        if _AC_TOKEN_PATTERN.fullmatch(part):
            out.append(part)
        else:
            out.append(html_module.escape(part, quote=True))
    return "".join(out)
