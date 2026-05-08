"""Golden file regression tests for md_to_mjml_body."""
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ac_builder.render.md_to_mjml_body import md_to_mjml_body
from ac_builder.render.mjml_runner import compile_mjml
from ac_builder.render.theme_loader import load_theme

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_e1():
    return (FIXTURES / "sample_email_e1.md").read_text()


def test_sample_e1_renders_without_error(sample_e1):
    theme = load_theme("lpis")
    body = md_to_mjml_body(sample_e1, theme=theme)
    assert body.strip()


def test_sample_e1_contains_expected_elements(sample_e1):
    theme = load_theme("lpis")
    body = md_to_mjml_body(sample_e1, theme=theme)

    assert "%FIRSTNAME|TITLECASE%" in body

    # h2 → styled mj-text - tolerate either escaped or raw apostrophe
    assert "What you&#x27;ll get" in body or "What you'll get" in body

    # List with 3 items
    assert body.count("<li") == 3

    # Explicit button marker became mj-button
    assert "<mj-button" in body
    assert "Hold my seat" in body
    assert "%CONTACTID%" in body

    # Conditional content preserved in mj-raw
    assert "%IF $SPECIALTY == 'Orthodontics'%" in body
    assert "<mj-raw>" in body


def test_sample_e1_output_compiles_with_full_template(sample_e1):
    """Wrap the body in promo.mjml + theme and ensure mjml strict mode accepts it."""
    repo_root = Path(__file__).parent.parent
    env = Environment(loader=FileSystemLoader(str(repo_root / "templates")), undefined=StrictUndefined)
    tmpl = env.get_template("promo.mjml")

    theme = load_theme("lpis")
    body = md_to_mjml_body(sample_e1, theme=theme)

    rendered_mjml = tmpl.render(
        theme={
            "name": theme.name,
            "fonts": theme.fonts,
            "colors": theme.colors,
            "branding": theme.branding,
            "urls": theme.urls,
        },
        title="Sample E1",
        preheader_text="A sample preheader",
        body_mjml=body,
        footer_mode="launch",
        header_image_url=None,
        header_image_alt=None,
        header_image_link=None,
    )
    result = compile_mjml(rendered_mjml, validate=True)
    assert "<html" in result.html.lower()
