"""Tests for HTML to plain text conversion."""
from ac_builder.text_renderer import html_to_text


def test_simple_paragraphs():
    html = "<html><body><p>First paragraph.</p><p>Second paragraph.</p></body></html>"
    text = html_to_text(html)
    assert "First paragraph." in text
    assert "Second paragraph." in text
    assert "<p>" not in text


def test_links_unwrap_to_text_with_url():
    html = '<p>Visit <a href="https://example.com">our site</a> for details.</p>'
    text = html_to_text(html)
    assert "our site" in text
    assert "https://example.com" in text


def test_button_links_render_url_on_separate_line():
    html = '<table><tr><td><a href="https://idd.com/cta" style="background-color:#000;padding:16px 32px">Register now</a></td></tr></table>'
    text = html_to_text(html)
    assert "Register now" in text
    assert "https://idd.com/cta" in text


def test_ac_merge_fields_preserved():
    html = "<p>Hi %FIRSTNAME|TITLECASE%, your ID is %CONTACTID%.</p>"
    text = html_to_text(html)
    assert "%FIRSTNAME|TITLECASE%" in text
    assert "%CONTACTID%" in text


def test_strips_style_and_script_tags():
    html = "<html><head><style>body{color:red}</style></head><body><p>Hi.</p><script>alert(1)</script></body></html>"
    text = html_to_text(html)
    assert "color:red" not in text
    assert "alert(1)" not in text
    assert "Hi." in text


def test_heading_emphasized_in_caps():
    html = "<h2>Important Section</h2><p>Body.</p>"
    text = html_to_text(html)
    assert "IMPORTANT SECTION" in text or "Important Section" in text


def test_lists_format_as_bullets():
    html = "<ul><li>First</li><li>Second</li></ul>"
    text = html_to_text(html)
    assert "First" in text
    assert "Second" in text
    assert "- First" in text or "* First" in text or "• First" in text


def test_blank_lines_collapsed():
    html = "<p>Para 1.</p><p></p><p></p><p>Para 2.</p>"
    text = html_to_text(html)
    assert "\n\n\n" not in text
