"""Layered credential resolution for ac-builder.

Precedence (highest to lowest):
    1. Process env vars (AC_API_URL, AC_API_KEY, etc.)
    2. Project-level ./ac-builder.env in CWD
    3. User-level $XDG_CONFIG_HOME/ac-builder/config.env (default ~/.config/ac-builder/config.env)

Returns a dict of resolved env-var-style settings. The caller (typically a
client class) reads from this dict or falls back to os.environ.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values


_KNOWN_KEYS = (
    "AC_API_URL",
    "AC_API_KEY",
    "AC_DEFAULT_LIST_ID",
    "AC_DEFAULT_FROM_NAME",
    "AC_DEFAULT_FROM_EMAIL",
    "AC_DEFAULT_REPLY_TO",
    "AC_DEFAULT_ADDRESS_ID",
)


def _user_config_path() -> Path:
    """Return the XDG-standard user config path for ac-builder."""
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_home:
        base = Path(xdg_home)
    else:
        base = Path.home() / ".config"
    return base / "ac-builder" / "config.env"


def _project_config_path() -> Path:
    """Return the project-level ac-builder.env in CWD."""
    return Path.cwd() / "ac-builder.env"


def load_credentials() -> dict[str, str]:
    """Resolve AC credentials from env, project, or user config (in that order).

    Returns a dict with whatever keys are populated. Process env vars take
    precedence over project/user files. Project file beats user file. Caller
    is responsible for raising if required keys are missing.
    """
    result: dict[str, str] = {}

    # Lowest precedence: user config
    user_path = _user_config_path()
    if user_path.exists():
        for key, value in dotenv_values(user_path).items():
            if value is not None:
                result[key] = value

    # Middle: project config (overrides user)
    project_path = _project_config_path()
    if project_path.exists():
        for key, value in dotenv_values(project_path).items():
            if value is not None:
                result[key] = value

    # Highest: process env (overrides everything)
    for key in _KNOWN_KEYS:
        env_value = os.environ.get(key)
        if env_value:
            result[key] = env_value

    return result
