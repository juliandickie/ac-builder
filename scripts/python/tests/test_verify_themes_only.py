"""Tests for `ac-builder verify --themes-only` flag."""
from __future__ import annotations


def test_verify_themes_only_skips_ac_api(tmp_path, monkeypatch):
    """--themes-only should NOT touch the AC API or check Node/MJML."""
    from ac_builder.cli import main

    # Point AC_API_URL at a non-existent host so any API call would fail.
    # If --themes-only honours the flag, we should still get exit 0.
    monkeypatch.setenv("AC_API_URL", "https://nonexistent.invalid")
    monkeypatch.setenv("AC_API_KEY", "irrelevant")

    # Use the bundled themes/ relative to the package
    from pathlib import Path
    pkg_root = Path(__file__).parent.parent
    themes_dir = pkg_root.parent.parent / "themes"  # repo root themes/
    monkeypatch.setenv("AC_BUILDER_THEMES_DIR", str(themes_dir))

    rc = main(["verify", "--themes-only"])
    assert rc == 0
