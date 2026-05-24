"""Tests for the end-to-end composition pipeline."""

from ac_builder.parser import EmailDef
from ac_builder.render.compose import ComposeRequest, ComposeResult, compose_email
from ac_builder.render.theme_loader import load_theme


def _sample_email() -> EmailDef:
    return EmailDef(
        code="E1",
        title="Welcome",
        subject_lines=["Welcome to the residency", "You're in"],
        preview_text="Three things to know before we start",
        body_md="Hi %FIRSTNAME|TITLECASE%,\n\nWelcome to LPIS.\n\n[[button:Hold my seat|https://idd.com/lpis]]",
        metadata={"send_date": "Mon Apr 27, 2026"},
    )


def test_compose_returns_compose_result():
    theme = load_theme("lpis")
    req = ComposeRequest(
        email=_sample_email(),
        theme=theme,
        template_name="promo.mjml",
        footer_mode="launch",
    )
    result = compose_email(req)
    assert isinstance(result, ComposeResult)
    assert result.html
    assert "<html" in result.html.lower()


def test_compose_output_has_required_compliance_tokens():
    theme = load_theme("lpis")
    req = ComposeRequest(email=_sample_email(), theme=theme, template_name="promo.mjml", footer_mode="launch")
    result = compose_email(req)
    assert "%UNSUBSCRIBELINK%" in result.html
    assert "%SENDER-INFO%" in result.html


def test_compose_preserves_personalization_tokens():
    theme = load_theme("lpis")
    req = ComposeRequest(email=_sample_email(), theme=theme, template_name="promo.mjml", footer_mode="launch")
    result = compose_email(req)
    assert "%FIRSTNAME|TITLECASE%" in result.html


def test_compose_includes_preheader_text():
    theme = load_theme("lpis")
    req = ComposeRequest(email=_sample_email(), theme=theme, template_name="promo.mjml", footer_mode="launch")
    result = compose_email(req)
    assert "Three things to know before we start" in result.html


def test_compose_with_header_image_override():
    theme = load_theme("lpis")
    req = ComposeRequest(
        email=_sample_email(),
        theme=theme,
        template_name="promo.mjml",
        footer_mode="launch",
        header_image_url="https://override.example.com/banner.jpg",
        header_image_alt="Override banner",
    )
    result = compose_email(req)
    assert "https://override.example.com/banner.jpg" in result.html


def test_compose_onboarding_footer_omits_not_interested():
    theme = load_theme("lpis")
    req = ComposeRequest(email=_sample_email(), theme=theme, template_name="onboarding.mjml", footer_mode="onboarding")
    result = compose_email(req)
    assert "Not the right fit" not in result.html


def test_compose_records_template_metadata():
    theme = load_theme("lpis")
    req = ComposeRequest(email=_sample_email(), theme=theme, template_name="promo.mjml", footer_mode="launch")
    result = compose_email(req)
    assert result.template_name == "promo.mjml"
    assert result.theme_name == "lpis"
    assert result.template_version
