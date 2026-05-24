"""Verify the theme JSON schema itself is a valid JSON Schema document."""
import json

import jsonschema

from ac_builder.render.theme_loader import THEMES_DIR

SCHEMA_PATH = THEMES_DIR / "_schema.json"


def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), f"Theme schema missing at {SCHEMA_PATH}"


def test_schema_is_valid_json_schema():
    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    # Should not raise
    jsonschema.Draft202012Validator.check_schema(schema)


def test_schema_requires_core_fields():
    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    required = set(schema.get("required", []))
    assert {"name", "display_name", "colors", "fonts", "branding", "urls", "cta_patterns", "tags"}.issubset(required)


def test_schema_validates_a_minimal_valid_theme():
    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    valid_theme = {
        "name": "test",
        "display_name": "Test Theme",
        "colors": {
            "primary": "#000000",
            "cta_bg": "#000000",
            "cta_text": "#ffffff",
            "body_text": "#222222",
            "body_text_dark": "#eaeaea",
            "bg": "#ffffff",
            "bg_dark": "#121212",
            "card_bg": "#ffffff",
            "card_bg_dark": "#1e1e1e",
        },
        "fonts": {"body": "Arial, sans-serif"},
        "branding": {
            "banner_url": "https://example.com/banner.jpg",
            "banner_alt": "Test banner",
        },
        "urls": {
            "sales_page": "https://example.com/buy",
            "not_interested": "https://example.com/not-interested",
        },
        "cta_patterns": ["Register now"],
        "tags": {"interest": "INTEREST: TEST"},
    }
    jsonschema.validate(valid_theme, schema)


def test_schema_rejects_invalid_color_format():
    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    bad_theme = {
        "name": "test",
        "display_name": "Test",
        "colors": {"primary": "red"},
        "fonts": {"body": "Arial"},
        "branding": {"banner_url": "https://x.com/b.jpg", "banner_alt": "a"},
        "urls": {"sales_page": "https://x.com", "not_interested": "https://x.com"},
        "cta_patterns": ["x"],
        "tags": {},
    }
    import pytest
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad_theme, schema)
