"""Tests for ac-builder render and check CLI commands."""
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent


@pytest.fixture
def sample_md(tmp_path):
    md = """
# Test sequence

**Campaign name:** `test-aunz`

## E1 — Hello

**Send date:** Mon
**Theme:** lpis

### Subject Line Options

1. **Hello world**

### Preview Text

"Welcome"

### Email Body

Hi %FIRSTNAME|TITLECASE%,

Welcome.

%UNSUBSCRIBELINK% %SENDER-INFO%
"""
    p = tmp_path / "sample.md"
    p.write_text(md)
    return p


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ac_builder.cli", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_render_emits_html_to_file(sample_md, tmp_path):
    out_path = tmp_path / "rendered.html"
    proc = _run(["render", str(sample_md), "--email", "E1", "--out", str(out_path)])
    assert proc.returncode == 0, proc.stderr
    assert out_path.exists()
    html = out_path.read_text()
    assert "<html" in html.lower()
    assert "%FIRSTNAME|TITLECASE%" in html


def test_check_passes_for_valid_html(tmp_path):
    valid_html = """<!DOCTYPE html><html lang="en"><head><title>x</title></head>
    <body><p>Hi %FIRSTNAME|TITLECASE%,</p>
    <p>Not the right fit? <a href="https://instituteofdigitaldentistry.com/not-interested/?cid=%CONTACTID%">Click here</a> to opt out.</p>
    <p>%UNSUBSCRIBELINK% %SENDER-INFO%</p></body></html>"""
    p = tmp_path / "x.html"
    p.write_text(valid_html)
    proc = _run(["check", str(p)])
    assert proc.returncode == 0, proc.stderr


def test_check_fails_for_html_missing_unsubscribe(tmp_path):
    invalid = "<html><body><p>%SENDER-INFO%</p></body></html>"
    p = tmp_path / "bad.html"
    p.write_text(invalid)
    proc = _run(["check", str(p)])
    assert proc.returncode != 0
    assert "missing-unsubscribe-link" in (proc.stdout + proc.stderr).lower() or "unsubscribe" in (proc.stdout + proc.stderr).lower()
