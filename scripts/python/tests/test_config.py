"""Tests for ac_builder.config layered credential resolution."""
from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_process_env_takes_precedence(monkeypatch, tmp_path):
    """Process env vars beat both project and user config files."""
    from ac_builder.config import load_credentials

    # Process env wins
    monkeypatch.setenv("AC_API_URL", "https://from-env.api-us1.com")
    monkeypatch.setenv("AC_API_KEY", "key-from-env")

    # Project config exists but should be ignored
    project_env = tmp_path / "ac-builder.env"
    project_env.write_text("AC_API_URL=https://from-project.api-us1.com\n")

    monkeypatch.chdir(tmp_path)
    creds = load_credentials()
    assert creds["AC_API_URL"] == "https://from-env.api-us1.com"
    assert creds["AC_API_KEY"] == "key-from-env"


def test_project_env_overrides_user_config(monkeypatch, tmp_path):
    """Project ./ac-builder.env beats user ~/.config/ac-builder/config.env."""
    from ac_builder.config import load_credentials

    # No process env vars
    monkeypatch.delenv("AC_API_URL", raising=False)
    monkeypatch.delenv("AC_API_KEY", raising=False)

    # User config (we point XDG_CONFIG_HOME at a tmp dir)
    user_dir = tmp_path / "user-config" / "ac-builder"
    user_dir.mkdir(parents=True)
    (user_dir / "config.env").write_text(
        "AC_API_URL=https://from-user.api-us1.com\nAC_API_KEY=user-key\n"
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))

    # Project config
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "ac-builder.env").write_text(
        "AC_API_URL=https://from-project.api-us1.com\nAC_API_KEY=project-key\n"
    )
    monkeypatch.chdir(project_dir)

    creds = load_credentials()
    assert creds["AC_API_URL"] == "https://from-project.api-us1.com"
    assert creds["AC_API_KEY"] == "project-key"


def test_user_config_used_when_no_project_or_env(monkeypatch, tmp_path):
    """User ~/.config/ac-builder/config.env is the default."""
    from ac_builder.config import load_credentials

    monkeypatch.delenv("AC_API_URL", raising=False)
    monkeypatch.delenv("AC_API_KEY", raising=False)

    user_dir = tmp_path / "user-config" / "ac-builder"
    user_dir.mkdir(parents=True)
    (user_dir / "config.env").write_text(
        "AC_API_URL=https://from-user.api-us1.com\nAC_API_KEY=user-key\n"
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))

    # CWD has no project config
    monkeypatch.chdir(tmp_path)

    creds = load_credentials()
    assert creds["AC_API_URL"] == "https://from-user.api-us1.com"
    assert creds["AC_API_KEY"] == "user-key"


def test_missing_credentials_returns_empty(monkeypatch, tmp_path):
    """When nothing is set, return empty dict (caller decides how to error)."""
    from ac_builder.config import load_credentials

    monkeypatch.delenv("AC_API_URL", raising=False)
    monkeypatch.delenv("AC_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "no-such-dir"))
    monkeypatch.chdir(tmp_path)

    creds = load_credentials()
    assert creds == {} or creds.get("AC_API_URL", "") == ""
