"""Tests for tools/lint-skills.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _lint_skills_path() -> Path:
    """Path to the lint-skills.py script (relative to scripts/python/)."""
    pkg_root = Path(__file__).parent.parent  # scripts/python/
    return pkg_root.parent.parent / "tools" / "lint-skills.py"


def test_valid_skill_passes(tmp_path):
    """A SKILL.md with valid frontmatter exits 0."""
    skill_dir = tmp_path / "skills" / "valid-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: valid-skill\n"
        "description: Use when the user wants to do a thing. Does the thing.\n"
        "allowed-tools: Bash\n"
        "---\n\n"
        "# Body\n"
    )

    result = subprocess.run(
        [sys.executable, str(_lint_skills_path()), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"


def test_missing_name_fails(tmp_path):
    skill_dir = tmp_path / "skills" / "no-name"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "description: x\n"
        "---\n"
    )

    result = subprocess.run(
        [sys.executable, str(_lint_skills_path()), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "name" in result.stderr.lower() or "name" in result.stdout.lower()


def test_invalid_name_fails(tmp_path):
    """Names with uppercase or underscores or claude/anthropic are rejected."""
    skill_dir = tmp_path / "skills" / "BadName"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: BadName\n"
        "description: x\n"
        "---\n"
    )

    result = subprocess.run(
        [sys.executable, str(_lint_skills_path()), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_description_too_long_fails(tmp_path):
    skill_dir = tmp_path / "skills" / "long-desc"
    skill_dir.mkdir(parents=True)
    long_desc = "x" * 1100  # over 1024 char limit
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: long-desc\n"
        f"description: {long_desc}\n"
        "---\n"
    )

    result = subprocess.run(
        [sys.executable, str(_lint_skills_path()), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "1024" in result.stdout or "1024" in result.stderr or "long" in (result.stderr + result.stdout).lower()


def test_reserved_word_in_name_fails(tmp_path):
    """Names containing 'claude' or 'anthropic' are rejected."""
    skill_dir = tmp_path / "skills" / "claude-helper"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: claude-helper\n"
        "description: x\n"
        "---\n"
    )

    result = subprocess.run(
        [sys.executable, str(_lint_skills_path()), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
