"""Load and validate iDD product themes from JSON.

Themes drive MJML rendering: colors, fonts, banner URLs, CTA detection
patterns, and product tag names. Each theme is a JSON file in `themes/`
matching `themes/_schema.json`.

Public surface:
    load_theme(name_or_path) -> ThemeData
    infer_theme_from_path(md_path) -> str | None
    discover_theme_names() -> list[str]
    ThemeData (dataclass), ThemeNotFoundError, ThemeValidationError

Resolution order for `load_theme(name)`:
    1. Explicit path (if name contains '/' or starts with '.')
    2. Project ./themes/<name>.json
    3. User $XDG_CONFIG_HOME/ac-builder/themes/<name>.json (default ~/.config/...)
    4. Plugin themes/examples/<name>.json (or AC_BUILDER_THEMES_DIR/examples/<name>.json)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema

# Plugin-bundled themes/ directory (where _schema.json lives).
# Path: <repo-root>/themes/. From this file at scripts/python/ac_builder/render/
# that's parent.parent.parent.parent.parent / "themes".
_DEFAULT_THEMES_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent / "themes"
)


def _resolve_themes_dir() -> Path:
    """Resolve plugin-bundled themes directory, honouring AC_BUILDER_THEMES_DIR env var.

    This returns the BASE themes directory (where _schema.json lives). The
    layered theme resolution in load_theme() looks INSIDE this base dir's
    examples/ subdir for plugin-bundled themes.
    """
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
    """List theme short-names found across the layered theme search paths.

    Walks the same directories as load_theme(): project ./themes/, user
    ~/.config/ac-builder/themes/, and plugin examples/. Returns the union
    (deduplicated, sorted). Excludes `_schema.json`. Honours
    AC_BUILDER_THEMES_DIR env var.
    """
    found: set[str] = set()

    # Project ./themes/
    project_dir = Path.cwd() / "themes"
    if project_dir.is_dir():
        found.update(p.stem for p in project_dir.glob("*.json") if p.name != "_schema.json")

    # User ~/.config/ac-builder/themes/
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    user_base = Path(xdg_home) if xdg_home else Path.home() / ".config"
    user_dir = user_base / "ac-builder" / "themes"
    if user_dir.is_dir():
        found.update(p.stem for p in user_dir.glob("*.json") if p.name != "_schema.json")

    # Plugin examples (under base themes dir)
    base = _resolve_themes_dir()
    examples_dir = base / "examples"
    if examples_dir.is_dir():
        found.update(p.stem for p in examples_dir.glob("*.json") if p.name != "_schema.json")
    # Also check the base dir itself for backward compat (e.g., if AC_BUILDER_THEMES_DIR
    # points directly at a flat themes directory without examples/ subdir)
    if base.is_dir():
        found.update(p.stem for p in base.glob("*.json") if p.name != "_schema.json")

    return sorted(found)


def _candidate_paths(theme_name: str) -> list[Path]:
    """Return ordered list of paths to try when resolving a theme name.

    Order (first match wins):
    1. Explicit path (if theme_name contains '/' or starts with '.')
    2. Project ./themes/<name>.json
    3. User $XDG_CONFIG_HOME/ac-builder/themes/<name>.json (default ~/.config/...)
    4. Plugin themes/examples/<name>.json (or AC_BUILDER_THEMES_DIR/examples/<name>.json)
    """
    candidates: list[Path] = []

    # 1. Explicit path
    if "/" in theme_name or theme_name.startswith("."):
        candidates.append(Path(theme_name).expanduser().resolve())
        return candidates

    filename = f"{theme_name}.json"

    # 2. Project-level
    candidates.append(Path.cwd() / "themes" / filename)

    # 3. User-level (XDG)
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    user_base = Path(xdg_home) if xdg_home else Path.home() / ".config"
    candidates.append(user_base / "ac-builder" / "themes" / filename)

    # 4. Plugin examples
    plugin_themes_dir_env = os.environ.get("AC_BUILDER_THEMES_DIR")
    if plugin_themes_dir_env:
        candidates.append(Path(plugin_themes_dir_env) / "examples" / filename)
    else:
        candidates.append(_DEFAULT_THEMES_DIR / "examples" / filename)

    return candidates


def load_theme(theme_name_or_path: str) -> ThemeData:
    """Load a theme by short name or explicit path. Validates against the schema.

    Resolution order: explicit > project ./themes > user ~/.config/ac-builder/themes > plugin themes/examples

    Raises:
        ThemeNotFoundError: if no candidate path exists.
        ThemeValidationError: if the JSON fails schema validation.
    """
    for candidate in _candidate_paths(theme_name_or_path):
        if candidate.exists():
            return _load_and_validate(candidate)

    tried = "\n  ".join(str(p) for p in _candidate_paths(theme_name_or_path))
    raise ThemeNotFoundError(
        f"Theme '{theme_name_or_path}' not found. Searched:\n  {tried}"
    )


def _load_and_validate(path: Path) -> ThemeData:
    """Load and validate a theme JSON at the given path. Internal helper.

    Looks for _schema.json relative to the theme file: same dir, parent dir
    (for examples/ case), or the plugin-bundled _DEFAULT_THEMES_DIR.
    """
    with path.open() as f:
        data = json.load(f)

    schema_path = None
    for candidate in (
        path.parent / "_schema.json",
        path.parent.parent / "_schema.json",
        _DEFAULT_THEMES_DIR / "_schema.json",
    ):
        if candidate.exists():
            schema_path = candidate
            break

    if schema_path is None:
        raise ThemeValidationError(f"No _schema.json found near {path}")

    with schema_path.open() as f:
        schema = json.load(f)

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        raise ThemeValidationError(
            f"Theme '{data.get('name', path.name)}' failed validation: "
            f"{exc.message} (path: {list(exc.absolute_path)})"
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
