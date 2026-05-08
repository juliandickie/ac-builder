"""All theme JSON files in themes/ must validate against _schema.json."""
import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).parent.parent
THEMES_DIR = REPO_ROOT / "themes"
SCHEMA_PATH = THEMES_DIR / "_schema.json"


def _load_schema():
    with SCHEMA_PATH.open() as f:
        return json.load(f)


def _theme_files():
    return sorted(p for p in THEMES_DIR.glob("*.json") if p.name != "_schema.json")


@pytest.mark.parametrize("theme_path", _theme_files(), ids=lambda p: p.stem)
def test_theme_validates_against_schema(theme_path):
    schema = _load_schema()
    with theme_path.open() as f:
        theme = json.load(f)
    jsonschema.validate(theme, schema)
    assert theme["name"] == theme_path.stem


def test_three_themes_exist():
    names = {p.stem for p in _theme_files()}
    assert {"lpis", "iidf", "asimr"}.issubset(names)
