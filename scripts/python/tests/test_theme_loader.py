"""Tests for layered theme resolution: explicit > project > user > plugin examples."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ac_builder.render.theme_loader import infer_theme_from_path


def _make_theme(path: Path, name: str, color: str = "#112233") -> None:
    """Write a minimal valid theme JSON to the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "name": name,
        "display_name": name.title(),
        "colors": {
            "primary": color,
            "cta_bg": color,
            "cta_text": "#ffffff",
            "body_text": "#222222",
            "body_text_dark": "#eeeeee",
            "bg": "#ffffff",
            "bg_dark": "#111111",
            "card_bg": "#fafafa",
            "card_bg_dark": "#222222",
        },
        "fonts": {"body": "Arial, sans-serif"},
        "branding": {"banner_url": "https://example.com/b.jpg", "banner_alt": "banner"},
        "urls": {"sales_page": "https://example.com/", "not_interested": "https://example.com/no"},
        "cta_patterns": ["Buy now"],
        "tags": {},
    }))


def _copy_schema(target_themes_dir: Path) -> None:
    """Ensure target dir has a _schema.json (copies from the real one)."""
    real_schema = Path("/Users/juliandickie/code/ac-builder/themes/_schema.json")
    if real_schema.exists():
        target_themes_dir.mkdir(parents=True, exist_ok=True)
        (target_themes_dir / "_schema.json").write_text(real_schema.read_text())


def test_explicit_path_wins(tmp_path, monkeypatch):
    """An explicit absolute path beats all directory-based resolution."""
    from ac_builder.render.theme_loader import load_theme

    explicit_dir = tmp_path / "explicit-themes"
    _copy_schema(explicit_dir)
    _make_theme(explicit_dir / "explicit.json", "explicit", "#aabbcc")

    theme = load_theme(str(explicit_dir / "explicit.json"))
    assert theme.name == "explicit"
    assert theme.colors["primary"] == "#aabbcc"


def test_project_themes_dir_used_first(tmp_path, monkeypatch):
    """./themes/<name>.json beats ~/.config/ac-builder/themes/<name>.json."""
    from ac_builder.render.theme_loader import load_theme

    project_themes = tmp_path / "project" / "themes"
    _copy_schema(project_themes)
    _make_theme(project_themes / "acme.json", "acme", "#ff0000")

    user_themes = tmp_path / "user-config" / "ac-builder" / "themes"
    _copy_schema(user_themes)
    _make_theme(user_themes / "acme.json", "acme", "#00ff00")

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    monkeypatch.delenv("AC_BUILDER_THEMES_DIR", raising=False)
    monkeypatch.chdir(tmp_path / "project")

    theme = load_theme("acme")
    assert theme.colors["primary"] == "#ff0000"  # project wins


def test_user_themes_dir_when_no_project(tmp_path, monkeypatch):
    """~/.config/ac-builder/themes/<name>.json used when no ./themes/ override."""
    from ac_builder.render.theme_loader import load_theme

    user_themes = tmp_path / "user-config" / "ac-builder" / "themes"
    _copy_schema(user_themes)
    _make_theme(user_themes / "acme.json", "acme", "#00ff00")

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    monkeypatch.delenv("AC_BUILDER_THEMES_DIR", raising=False)
    monkeypatch.chdir(tmp_path)  # no ./themes/

    theme = load_theme("acme")
    assert theme.colors["primary"] == "#00ff00"


def test_plugin_examples_fallback(tmp_path, monkeypatch):
    """Falls back to plugin themes/examples/ when no project or user override."""
    from ac_builder.render.theme_loader import load_theme

    plugin_examples = tmp_path / "plugin" / "themes" / "examples"
    _copy_schema(plugin_examples)
    _make_theme(plugin_examples / "fallback.json", "fallback", "#0000ff")

    # AC_BUILDER_THEMES_DIR points at the plugin's themes/ folder (parent of examples/)
    monkeypatch.setenv("AC_BUILDER_THEMES_DIR", str(tmp_path / "plugin" / "themes"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "no-such"))
    monkeypatch.chdir(tmp_path)

    theme = load_theme("fallback")
    assert theme.colors["primary"] == "#0000ff"


def test_missing_theme_raises(tmp_path, monkeypatch):
    """Loading a non-existent theme raises ThemeNotFoundError."""
    from ac_builder.render.theme_loader import ThemeNotFoundError, load_theme

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
    monkeypatch.setenv("AC_BUILDER_THEMES_DIR", str(tmp_path / "empty"))
    monkeypatch.chdir(tmp_path)

    with pytest.raises((ThemeNotFoundError, FileNotFoundError, ValueError, RuntimeError)):
        load_theme("nonexistent-theme-xyz")


# --- infer_theme_from_path tests (preserved from prior version) ---

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
