"""Test that parser captures the optional **Theme:** metadata field per email."""
from ac_builder.parser import parse_md_text


def test_email_with_theme_field_captured():
    md = """
# Test Sequence

## E1 — First Email

**Send date:** Mon Apr 27, 2026
**Theme:** lpis

### Subject Line Options

1. **Subject A**

### Preview Text

"Preview"

### Email Body

Body content.
"""
    emails = parse_md_text(md)
    assert len(emails) == 1
    assert emails[0].metadata.get("theme") == "lpis"


def test_email_without_theme_field():
    md = """
# Test Sequence

## E1 — First Email

**Send date:** Mon Apr 27, 2026

### Subject Line Options

1. **Subject A**

### Preview Text

"Preview"

### Email Body

Body content.
"""
    emails = parse_md_text(md)
    assert "theme" not in emails[0].metadata
