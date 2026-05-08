"""Tests for markdown → MJML body fragment conversion."""
import pytest

from ac_builder.render.md_to_mjml_body import md_to_mjml_body
from ac_builder.render.theme_loader import load_theme


@pytest.fixture
def theme():
    return load_theme("lpis")


def test_output_is_wrapped_in_section_column(theme):
    md = "Hello world."
    out = md_to_mjml_body(md, theme=theme)
    # Body fragment must wrap content in a single mj-section + mj-column
    assert "<mj-section" in out
    assert "<mj-column" in out
    # Counts: exactly one outer wrapper
    assert out.count("<mj-section") == 1
    assert out.count("<mj-column") == 1


def test_single_paragraph_becomes_mj_text(theme):
    md = "Hello world."
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-text" in out
    assert "Hello world." in out


def test_multiple_paragraphs_become_separate_mj_texts(theme):
    md = "First paragraph.\n\nSecond paragraph."
    out = md_to_mjml_body(md, theme=theme)
    assert out.count("<mj-text") == 2
    assert "First paragraph." in out
    assert "Second paragraph." in out


def test_h2_heading_emits_styled_mj_text(theme):
    md = "## My Heading\n\nBody text."
    out = md_to_mjml_body(md, theme=theme)
    assert "My Heading" in out
    assert 'font-size="24px"' in out


def test_h3_heading_emits_smaller_styled_mj_text(theme):
    md = "### Subheading\n\nBody."
    out = md_to_mjml_body(md, theme=theme)
    assert "Subheading" in out
    assert 'font-size="20px"' in out


def test_hr_emits_mj_divider(theme):
    md = "Above\n\n---\n\nBelow"
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-divider" in out


def test_h1_is_skipped(theme):
    md = "# This Should Not Appear\n\nThis should appear."
    out = md_to_mjml_body(md, theme=theme)
    assert "This Should Not Appear" not in out
    assert "This should appear." in out


def test_empty_input_returns_empty_string(theme):
    out = md_to_mjml_body("", theme=theme)
    assert out.strip() == ""


def test_unordered_list_emits_mj_text_with_ul(theme):
    md = "- First item\n- Second item\n- Third item"
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-text" in out
    assert "<ul" in out
    assert "<li" in out
    assert out.count("<li") == 3
    assert "First item" in out
    assert "Third item" in out


def test_ordered_list_emits_mj_text_with_ol(theme):
    md = "1. Step one\n2. Step two\n3. Step three"
    out = md_to_mjml_body(md, theme=theme)
    assert "<ol" in out
    assert "<li" in out
    assert out.count("<li") == 3


def test_list_with_inline_formatting(theme):
    md = "- **Bold item** in list\n- *Italic item* in list"
    out = md_to_mjml_body(md, theme=theme)
    assert "<strong>Bold item</strong>" in out
    assert "<em>Italic item</em>" in out


def test_ac_merge_fields_preserved_verbatim(theme):
    md = "Hi %FIRSTNAME|TITLECASE%, your contact ID is %CONTACTID%."
    out = md_to_mjml_body(md, theme=theme)
    assert "%FIRSTNAME|TITLECASE%" in out
    assert "%CONTACTID%" in out


def test_unsubscribe_and_sender_info_tokens_preserved(theme):
    md = "Footer line: %UNSUBSCRIBELINK% and %SENDER-INFO%"
    out = md_to_mjml_body(md, theme=theme)
    assert "%UNSUBSCRIBELINK%" in out
    assert "%SENDER-INFO%" in out


def test_inline_link_renders_with_theme_color(theme):
    md = "Visit [our site](https://example.com) for details."
    out = md_to_mjml_body(md, theme=theme)
    assert '<a href="https://example.com"' in out
    assert theme.colors["primary"] in out
    assert ">our site</a>" in out


def test_inline_link_with_merge_field_in_url(theme):
    md = "Click [here](https://idd.com/x?cid=%CONTACTID%) please."
    out = md_to_mjml_body(md, theme=theme)
    assert "%CONTACTID%" in out
    assert "https://idd.com/x?cid=%CONTACTID%" in out


def test_conditional_content_preserved_via_mj_raw(theme):
    md = "%IF !empty($FIRSTNAME)%Hi %FIRSTNAME%,%ELSE%Hi there,%/IF%\n\nBody text."
    out = md_to_mjml_body(md, theme=theme)
    assert "%IF !empty($FIRSTNAME)%" in out
    assert "%/IF%" in out


def test_bold_and_italic_inline(theme):
    md = "This is **bold** and this is *italic*."
    out = md_to_mjml_body(md, theme=theme)
    assert "<strong>bold</strong>" in out
    assert "<em>italic</em>" in out


def test_paragraph_only_link_with_cta_pattern_becomes_button(theme):
    md = "[Register now](https://idd.com/lpis)"
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-button" in out
    assert 'href="https://idd.com/lpis"' in out
    assert "Register now" in out


def test_paragraph_only_link_without_cta_pattern_stays_text(theme):
    md = "[Read the article](https://idd.com/blog)"
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-button" not in out
    assert '<a href="https://idd.com/blog"' in out


def test_inline_link_in_sentence_does_not_become_button(theme):
    md = "If you're interested, [Register now](https://idd.com/lpis) please."
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-button" not in out
    assert '<a href="https://idd.com/lpis"' in out


def test_explicit_button_marker(theme):
    md = "[[button:Custom CTA Text|https://idd.com/custom]]"
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-button" in out
    assert 'href="https://idd.com/custom"' in out
    assert "Custom CTA Text" in out


def test_explicit_button_marker_overrides_cta_pattern_match(theme):
    md = "[[button:Just words|https://idd.com/x]]"
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-button" in out
    assert "Just words" in out


def test_button_marker_with_merge_field_in_url(theme):
    md = "[[button:Hold my seat|https://idd.com/lpis?cid=%CONTACTID%]]"
    out = md_to_mjml_body(md, theme=theme)
    assert "%CONTACTID%" in out
    assert "<mj-button" in out


def test_bold_wrapped_link_to_sales_page_becomes_button(theme):
    """Real iDD source pattern: **[CTA text →](sales_page)** on its own line."""
    sales = theme.urls["sales_page"]
    md = f"**[I want in, Ahmad. Tell me more. →]({sales})**"
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-button" in out, "Bold-wrapped sales-page link must promote to button"
    # Visible text preserves the arrow - that's how it's authored
    assert "I want in, Ahmad. Tell me more." in out


def test_bold_wrapped_link_to_arbitrary_url_does_not_become_button(theme):
    md = "**[Read more on the blog](https://idd.com/blog/post)**"
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-button" not in out
    assert '<a href="https://idd.com/blog/post"' in out


def test_cta_pattern_match_tolerates_trailing_arrow(theme):
    md = "[Register now →](https://idd.com/lpis)"
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-button" in out
    # Arrow preserved in button label
    assert "Register now" in out


def test_cta_url_match_with_contactid_merge_field(theme):
    """The actual sales_page URL in the theme includes ?cid=%CONTACTID%."""
    md = "**[Count me in →](https://instituteofdigitaldentistry.com/live-courses/live-patient-implant-surgery-course-wellington-new-zealand/?cid=%CONTACTID%)**"
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-button" in out
    assert "%CONTACTID%" in out


def test_inline_sales_page_link_in_sentence_does_not_become_button(theme):
    """Even with the URL being the sales page, an in-sentence link stays as <a>."""
    sales = theme.urls["sales_page"]
    md = f"For more, see [our course page]({sales}) and decide."
    out = md_to_mjml_body(md, theme=theme)
    assert "<mj-button" not in out
    assert f'<a href="{sales}"' in out


# --- H2 accent stripe ---

def test_h2_uses_primary_color_and_accent_stripe(theme):
    md = "## What you'll get\n\nBody."
    out = md_to_mjml_body(md, theme=theme)
    primary = theme.colors["primary"]
    accent = theme.colors["accent"]
    # H2 text gets primary color and a left-border accent stripe span
    assert f'color="{primary}"' in out
    assert f"border-left:4px solid {accent}" in out


def test_h3_uses_primary_color_no_stripe(theme):
    md = "### Subheading\n\nBody."
    out = md_to_mjml_body(md, theme=theme)
    primary = theme.colors["primary"]
    assert f'color="{primary}"' in out
    # H3 has no stripe span - that's reserved for h2 major sections
    assert "border-left:4px solid" not in out


# --- Section strip ---

def test_section_strip_marker_emits_coloured_band(theme):
    md = "Above the strip.\n\n=== Why this matters ===\n\nBelow the strip."
    out = md_to_mjml_body(md, theme=theme)
    # Strip uses secondary (brighter teal) when defined, falling back to
    # primary otherwise. LPIS has secondary set.
    expected_bg = theme.colors.get("secondary") or theme.colors["primary"]
    assert f'background-color="{expected_bg}"' in out
    assert "WHY THIS MATTERS" not in out  # uppercase via CSS, not text mutation
    assert "Why this matters" in out
    assert "text-transform:uppercase" in out
    # Three sections total: above content, strip, below content
    assert out.count("<mj-section") == 3


def test_section_strip_with_only_strip_no_other_content(theme):
    md = "=== Section ==="
    out = md_to_mjml_body(md, theme=theme)
    # Just the strip, no wrapper content section
    assert out.count("<mj-section") == 1
    assert "Section" in out


def test_section_strip_with_apostrophe_does_not_double_escape(theme):
    """Regression: 'What's coming' was rendered as 'What&#x27;s coming'.

    The strip text comes from the inline renderer already HTML-escaped;
    re-escaping it produced &amp;#x27; which renders as literal &#x27; text
    after CSS text-transform uppercases the 'x' to 'X'.
    """
    md = "=== What's coming ==="
    out = md_to_mjml_body(md, theme=theme)
    assert "&amp;#x27;" not in out, "Strip text must not be double-escaped"
    # Single-encoded form is fine - the browser decodes &#x27; back to '
    assert "What&#x27;s coming" in out or "What's coming" in out


def test_section_strip_falls_back_to_primary_when_no_secondary():
    """Regression: themes without a secondary color must still render strips."""
    from ac_builder.render.theme_loader import ThemeData
    fake_theme = ThemeData(
        name="test",
        display_name="Test",
        colors={
            "primary": "#000080",
            "cta_bg": "#000080",
            "cta_text": "#ffffff",
            "body_text": "#222222",
            "body_text_dark": "#eaeaea",
            "bg": "#fff",
            "bg_dark": "#000",
            "card_bg": "#fff",
            "card_bg_dark": "#000",
        },
        fonts={"body": "Arial, sans-serif"},
        branding={"banner_url": "https://example.com/x.jpg", "banner_alt": "x"},
        urls={"sales_page": "https://example.com/", "not_interested": "https://example.com/no"},
        cta_patterns=["Click"],
        tags={},
    )
    md = "=== Section ==="
    out = md_to_mjml_body(md, theme=fake_theme)
    assert 'background-color="#000080"' in out


def test_section_strip_does_not_match_in_middle_of_paragraph(theme):
    md = "This paragraph mentions === something === in the middle."
    out = md_to_mjml_body(md, theme=theme)
    # Inline === is preserved as text, not promoted to a strip
    assert out.count("<mj-section") == 1
    expected_bg = theme.colors.get("secondary") or theme.colors["primary"]
    assert f'background-color="{expected_bg}"' not in out


# --- Blockquote callout ---

def test_blockquote_emits_callout_section(theme):
    md = "Above.\n\n> P.S. Trust your instinct.\n\nBelow."
    out = md_to_mjml_body(md, theme=theme)
    accent = theme.colors["accent"]
    # Callout section has cream-tone bg and accent left border
    assert "background-color=\"#fdf8ec\"" in out
    assert f"border-left:4px solid {accent}" in out
    assert "P.S. Trust your instinct." in out
    # Three sections: above content, callout, below content
    assert out.count("<mj-section") == 3


def test_blockquote_renders_inline_formatting(theme):
    md = "> This is **important** and *italic*."
    out = md_to_mjml_body(md, theme=theme)
    assert "<strong>important</strong>" in out
    assert "<em>italic</em>" in out


# --- Pillar row ---

def test_pillar_row_emits_two_columns(theme):
    from textwrap import dedent
    md = dedent("""\
        :::pillars
        ### Column A
        Body A
        +++
        ### Column B
        Body B
        :::""")
    out = md_to_mjml_body(md, theme=theme)
    # Section wraps columns
    assert out.count("<mj-section") == 1
    assert out.count("<mj-column") == 2
    assert "Column A" in out
    assert "Column B" in out
    assert "Body A" in out
    assert "Body B" in out


def test_pillar_row_emits_three_columns(theme):
    from textwrap import dedent
    md = dedent("""\
        :::pillars
        ### Path 1
        First
        +++
        ### Path 2
        Second
        +++
        ### Path 3
        Third
        :::""")
    out = md_to_mjml_body(md, theme=theme)
    assert out.count("<mj-column") == 3
    assert "Path 1" in out
    assert "Path 2" in out
    assert "Path 3" in out


def test_pillar_columns_render_buttons(theme):
    """A button inside a pillar column should still become an mj-button."""
    from textwrap import dedent
    sales = theme.urls["sales_page"]
    md = dedent(f"""\
        :::pillars
        ### Option A

        Body A

        **[Reserve seat →]({sales})**
        +++
        ### Option B

        Body B

        **[Tell me more →]({sales})**
        :::""")
    out = md_to_mjml_body(md, theme=theme)
    assert out.count("<mj-button") == 2
    assert "Reserve seat" in out
    assert "Tell me more" in out


def test_pillar_columns_render_h3_with_primary_color(theme):
    from textwrap import dedent
    md = dedent("""\
        :::pillars
        ### Option A
        Body A
        +++
        ### Option B
        Body B
        :::""")
    out = md_to_mjml_body(md, theme=theme)
    primary = theme.colors["primary"]
    # Each h3 inside a pillar column inherits the heading treatment
    assert out.count(f'color="{primary}"') >= 2


def test_pillar_row_with_surrounding_content(theme):
    from textwrap import dedent
    md = dedent("""\
        Above the pillars.

        :::pillars
        ### A
        Body
        +++
        ### B
        Body
        :::

        Below the pillars.""")
    out = md_to_mjml_body(md, theme=theme)
    # Three sections: above content wrapper, pillars, below content wrapper
    assert out.count("<mj-section") == 3
    assert "Above the pillars." in out
    assert "Below the pillars." in out


def test_pillar_columns_use_card_bg(theme):
    from textwrap import dedent
    md = dedent("""\
        :::pillars
        ### A
        B
        +++
        ### C
        D
        :::""")
    out = md_to_mjml_body(md, theme=theme)
    card_bg = theme.colors.get("card_bg", "#ffffff")
    # Each column has card_bg as background-color
    assert out.count(f'background-color="{card_bg}"') == 2


def test_pillar_row_with_blank_inner_renders_nothing(theme):
    """A pillars block with no actual column content should not emit anything broken."""
    from textwrap import dedent
    md = dedent("""\
        :::pillars

        :::""")
    out = md_to_mjml_body(md, theme=theme)
    # No mj-column emitted because there are no columns of real content
    assert "<mj-column" not in out
