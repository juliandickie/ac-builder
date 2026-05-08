"""Integration tests: every MJML template + theme combo compiles cleanly."""
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ac_builder.render.mjml_runner import compile_mjml
from ac_builder.render.theme_loader import load_theme

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"

SEQUENCE_TEMPLATES = ["promo.mjml", "onboarding.mjml", "abandon-cart.mjml", "transactional.mjml"]
THEMES = ["lpis", "iidf", "asimr"]

SAMPLE_BODY_MJML = """
<mj-section padding="0">
  <mj-column>
    <mj-text>Hi %FIRSTNAME|TITLECASE%,</mj-text>
    <mj-text>Body paragraph one.</mj-text>
  </mj-column>
</mj-section>
"""


def _jinja_env():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


@pytest.mark.parametrize("template_name", SEQUENCE_TEMPLATES)
@pytest.mark.parametrize("theme_name", THEMES)
def test_template_compiles(template_name, theme_name):
    theme = load_theme(theme_name)
    env = _jinja_env()
    tmpl = env.get_template(template_name)

    footer_mode = {
        "promo.mjml": "launch",
        "onboarding.mjml": "onboarding",
        "abandon-cart.mjml": "launch",
        "transactional.mjml": "transactional",
    }[template_name]

    rendered_mjml = tmpl.render(
        theme={
            "name": theme.name,
            "fonts": theme.fonts,
            "colors": theme.colors,
            "branding": theme.branding,
            "urls": theme.urls,
        },
        title=f"Test {template_name}",
        preheader_text="Test preheader text",
        body_mjml=SAMPLE_BODY_MJML,
        footer_mode=footer_mode,
        header_image_url=None,
        header_image_alt=None,
        header_image_link=None,
    )

    result = compile_mjml(rendered_mjml, validate=True)
    assert "<html" in result.html.lower()
    assert "%UNSUBSCRIBELINK%" in result.html
    assert "%SENDER-INFO%" in result.html
    assert "%FIRSTNAME|TITLECASE%" in result.html
