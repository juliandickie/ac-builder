"""All bundled example themes must validate against _schema.json."""
import json

import jsonschema
import pytest

from ac_builder.render.theme_loader import THEMES_DIR

SCHEMA_PATH = THEMES_DIR / "_schema.json"
EXAMPLES_DIR = THEMES_DIR / "examples"


def _load_schema():
    with SCHEMA_PATH.open() as f:
        return json.load(f)


def _theme_files():
    return sorted(EXAMPLES_DIR.glob("*.json"))


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
