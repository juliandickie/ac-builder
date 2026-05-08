"""Tests for banner rotation across emails in a sequence."""
from ac_builder.render.compose import (
    ComposeRequest,
    compose_email,
    pick_banner_for_email,
)
from ac_builder.parser import EmailDef
from ac_builder.render.theme_loader import load_theme


def test_pick_banner_cycles_by_email_number():
    urls = ["url0", "url1", "url2"]
    assert pick_banner_for_email("E1", urls) == "url0"
    assert pick_banner_for_email("E2", urls) == "url1"
    assert pick_banner_for_email("E3", urls) == "url2"
    assert pick_banner_for_email("E4", urls) == "url0"
    assert pick_banner_for_email("E5", urls) == "url1"
    assert pick_banner_for_email("E20", urls) == "url1"  # (20-1) % 3 = 1


def test_pick_banner_handles_hyphenated_codes():
    urls = ["a", "b", "c"]
    assert pick_banner_for_email("WL-1", urls) == "a"
    assert pick_banner_for_email("WL-2", urls) == "b"
    assert pick_banner_for_email("LPIS-OB-1", urls) == "a"
    assert pick_banner_for_email("LPIS-OB-2", urls) == "b"


def test_pick_banner_single_url_returns_it():
    assert pick_banner_for_email("E1", ["only-one"]) == "only-one"


def test_pick_banner_empty_raises():
    import pytest
    with pytest.raises(ValueError):
        pick_banner_for_email("E1", [])


def test_lpis_theme_exposes_three_banner_urls():
    theme = load_theme("lpis")
    banners = theme.branding.get("banner_urls")
    assert isinstance(banners, list)
    assert len(banners) == 3
    for url in banners:
        assert url.startswith("https://content.app-us1.com/LMez9/")


def test_iidf_theme_no_placeholder():
    theme = load_theme("iidf")
    banner_url = theme.branding.get("banner_url", "")
    assert "PLACEHOLDER" not in banner_url
    assert len(theme.branding.get("banner_urls", [])) == 3


def test_asimr_theme_no_placeholder():
    theme = load_theme("asimr")
    banner_url = theme.branding.get("banner_url", "")
    assert "PLACEHOLDER" not in banner_url
    assert len(theme.branding.get("banner_urls", [])) == 3


def test_compose_uses_rotated_banner_when_no_override():
    """When no header_image_url is passed, compose should pick from theme.banner_urls."""
    theme = load_theme("lpis")
    banners = theme.branding["banner_urls"]

    e1 = EmailDef(
        code="E1",
        title="First",
        subject_lines=["Hi"],
        preview_text="P",
        body_md="Hi %FIRSTNAME|TITLECASE%, body. %UNSUBSCRIBELINK% %SENDER-INFO%",
        metadata={},
    )
    e2 = EmailDef(
        code="E2",
        title="Second",
        subject_lines=["Hi"],
        preview_text="P",
        body_md="Body. %UNSUBSCRIBELINK% %SENDER-INFO%",
        metadata={},
    )

    out_e1 = compose_email(ComposeRequest(email=e1, theme=theme, template_name="promo.mjml", footer_mode="launch"))
    out_e2 = compose_email(ComposeRequest(email=e2, theme=theme, template_name="promo.mjml", footer_mode="launch"))

    assert banners[0] in out_e1.html
    assert banners[1] in out_e2.html


def test_compose_explicit_header_url_overrides_rotation():
    """An explicit --header-image-url should win over the rotation."""
    theme = load_theme("lpis")
    e1 = EmailDef(
        code="E1",
        title="First",
        subject_lines=["Hi"],
        preview_text="P",
        body_md="Body. %UNSUBSCRIBELINK% %SENDER-INFO%",
        metadata={},
    )
    out = compose_email(ComposeRequest(
        email=e1,
        theme=theme,
        template_name="promo.mjml",
        footer_mode="launch",
        header_image_url="https://override.example.com/banner.jpg",
    ))
    assert "https://override.example.com/banner.jpg" in out.html
