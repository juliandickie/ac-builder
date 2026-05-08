"""Tests for theme_loader.py."""
from pathlib import Path

import pytest

from ac_builder.render.theme_loader import (
    ThemeData,
    ThemeNotFoundError,
    ThemeValidationError,
    infer_theme_from_path,
    load_theme,
)


def test_load_theme_returns_themedata():
    theme = load_theme("lpis")
    assert isinstance(theme, ThemeData)
    assert theme.name == "lpis"
    assert theme.display_name.startswith("Live Patient")


def test_load_theme_exposes_colors_dict():
    theme = load_theme("lpis")
    assert theme.colors["primary"].startswith("#")
    assert "body_text" in theme.colors
    assert "bg_dark" in theme.colors


def test_load_theme_exposes_cta_patterns_list():
    theme = load_theme("lpis")
    assert "Register now" in theme.cta_patterns


def test_load_unknown_theme_raises():
    with pytest.raises(ThemeNotFoundError):
        load_theme("does-not-exist")


def test_load_invalid_theme_raises_validation_error(tmp_path, monkeypatch):
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    schema_src = Path(__file__).parent.parent / "themes" / "_schema.json"
    (themes_dir / "_schema.json").write_text(schema_src.read_text())
    (themes_dir / "broken.json").write_text('{"name": "broken"}')

    from ac_builder.render import theme_loader
    monkeypatch.setattr(theme_loader, "THEMES_DIR", themes_dir)

    with pytest.raises(ThemeValidationError):
        load_theme("broken")


def test_infer_theme_from_path_lpis():
    assert infer_theme_from_path("output/emails-au-nz/AUNZ_Main_Sequence_E1_to_E20.md") == "lpis"
    assert infer_theme_from_path("output/emails-au-nz/AUNZ_Waitlist_Parallel_Emails_WL1_to_WL4.md") == "lpis"
    assert infer_theme_from_path("output/emails-transition-nurture/October_LPIS_Transition_Sequence.md") == "lpis"
    assert infer_theme_from_path("output/emails-onboarding/LPIS_Post_Purchase_Onboarding_Emails.md") == "lpis"


def test_infer_theme_from_path_iidf():
    assert infer_theme_from_path("output/emails-au-nz/AUNZ_Branch_C_IIDF_Emails_C1_to_C5.md") == "iidf"
    assert infer_theme_from_path("output/emails-onboarding/IIDF_Post_Purchase_Onboarding_Emails.md") == "iidf"


def test_infer_theme_from_path_asimr():
    assert infer_theme_from_path("output/emails-au-nz/GLOBAL_Campaign_2_ASIMR_Emails_G1_to_G14.md") == "asimr"
    assert infer_theme_from_path("output/emails-onboarding/ASIMR_Post_Purchase_Onboarding_Emails.md") == "asimr"


def test_infer_theme_from_path_unknown_returns_none():
    assert infer_theme_from_path("output/emails-abandon-cart/Abandon_Cart_Sequences_All_Products.md") is None
