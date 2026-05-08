"""Load and validate iDD product themes from JSON.

Themes drive MJML rendering: colors, fonts, banner URLs, CTA detection
patterns, and product tag names. Each theme is a JSON file in `themes/`
matching `themes/_schema.json`.

Public surface:
    load_theme(name) -> ThemeData
    infer_theme_from_path(md_path) -> str | None
    ThemeData (dataclass), ThemeNotFoundError, ThemeValidationError
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema

_DEFAULT_THEMES_DIR = Path(__file__).resolve().parent.parent.parent / "themes"


def _resolve_themes_dir() -> Path:
    """Resolve themes directory, honouring AC_BUILDER_THEMES_DIR env var."""
    override = os.getenv("AC_BUILDER_THEMES_DIR")
    if override:
        return Path(override)
    return _DEFAULT_THEMES_DIR


# Module-level THEMES_DIR retained for backward compatibility with imports,
# but lookups should prefer _resolve_themes_dir() for env-var support.
THEMES_DIR = _DEFAULT_THEMES_DIR


class ThemeNotFoundError(FileNotFoundError):
    """Raised when a theme name doesn't resolve to a JSON file."""


class ThemeValidationError(ValueError):
    """Raised when a theme JSON fails schema validation."""


@dataclass(frozen=True)
class ThemeData:
    """In-memory representation of a theme JSON. Frozen - read-only once loaded."""
    name: str
    display_name: str
    colors: dict[str, str]
    fonts: dict[str, str]
    branding: dict[str, str | int]
    urls: dict[str, str]
    cta_patterns: list[str]
    tags: dict[str, str] = field(default_factory=dict)


def discover_theme_names() -> list[str]:
    """List theme short-names found in the active themes directory.

    Returns an empty list if the directory doesn't exist. Excludes `_schema.json`.
    Honours AC_BUILDER_THEMES_DIR env var.
    """
    themes_dir = _resolve_themes_dir()
    if not themes_dir.exists():
        return []
    return sorted(
        p.stem for p in themes_dir.glob("*.json") if p.name != "_schema.json"
    )


def load_theme(name: str) -> ThemeData:
    """Load a theme by short name. Validates against the schema.

    Raises:
        ThemeNotFoundError: if `themes/{name}.json` doesn't exist.
        ThemeValidationError: if the JSON fails schema validation.
    """
    themes_dir = _resolve_themes_dir()
    path = themes_dir / f"{name}.json"
    if not path.exists():
        raise ThemeNotFoundError(f"Theme '{name}' not found at {path}")

    with path.open() as f:
        data = json.load(f)

    schema_path = themes_dir / "_schema.json"
    with schema_path.open() as f:
        schema = json.load(f)

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        raise ThemeValidationError(
            f"Theme '{name}' failed validation: {exc.message} (path: {list(exc.absolute_path)})"
        ) from exc

    return ThemeData(
        name=data["name"],
        display_name=data["display_name"],
        colors=data["colors"],
        fonts=data["fonts"],
        branding=data["branding"],
        urls=data["urls"],
        cta_patterns=data["cta_patterns"],
        tags=data.get("tags", {}),
    )


_FILENAME_THEME_PATTERNS: list[tuple[tuple[str, ...], str]] = [
    (("Branch_C", "IIDF"), "iidf"),
    (("ASIMR", "GLOBAL_Campaign_2"), "asimr"),
    (("LPIS", "Main_Sequence", "Waitlist", "October_LPIS"), "lpis"),
]


def infer_theme_from_path(md_path: str | Path) -> str | None:
    """Infer the theme name from a source MD filename. None if ambiguous.

    Returns None for multi-product files like Abandon_Cart_Sequences_All_Products.md.
    """
    name = Path(md_path).name
    for patterns, theme in _FILENAME_THEME_PATTERNS:
        if any(p in name for p in patterns):
            return theme
    return None
