#!/usr/bin/env python3
"""Validate SKILL.md frontmatter across the skills/ directory.

Checks per Anthropic 2026 best practices:
- frontmatter exists and is valid YAML
- name field present, lowercase + hyphens, max 64 chars, no 'claude' or 'anthropic'
- description field present, max 1024 chars

Usage:
    python tools/lint-skills.py [<repo-root>]

Exits 0 if all skills pass, 1 if any fail (with details on stderr).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


_RESERVED_WORDS = ("claude", "anthropic")
_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def _check_skill(skill_md: Path) -> list[str]:
    """Return list of error messages (empty = passes)."""
    errors: list[str] = []
    text = skill_md.read_text()

    m = _FRONTMATTER.match(text)
    if not m:
        return [f"{skill_md}: missing or malformed frontmatter (must start with --- ... ---)"]

    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return [f"{skill_md}: frontmatter YAML parse error: {e}"]

    if not isinstance(fm, dict):
        return [f"{skill_md}: frontmatter is not a YAML mapping"]

    # name
    name = fm.get("name")
    if not name:
        errors.append(f"{skill_md}: missing 'name' field")
    elif not isinstance(name, str):
        errors.append(f"{skill_md}: 'name' must be a string, got {type(name).__name__}")
    elif not _NAME_PATTERN.match(name):
        errors.append(
            f"{skill_md}: 'name' must match pattern ^[a-z][a-z0-9-]{{0,63}}$ (got: {name!r})"
        )
    else:
        for word in _RESERVED_WORDS:
            if word in name:
                errors.append(f"{skill_md}: 'name' contains reserved word {word!r}")

    # description
    desc = fm.get("description")
    if not desc:
        errors.append(f"{skill_md}: missing 'description' field")
    elif not isinstance(desc, str):
        errors.append(f"{skill_md}: 'description' must be a string")
    elif len(desc) > 1024:
        errors.append(
            f"{skill_md}: 'description' is {len(desc)} chars (max 1024)"
        )

    return errors


def main(argv: list[str]) -> int:
    repo_root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    skills_dir = repo_root / "skills"

    if not skills_dir.exists():
        print(f"No skills/ directory at {skills_dir}", file=sys.stderr)
        return 1

    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    if not skill_files:
        print(f"No SKILL.md files found in {skills_dir}", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for skill_md in skill_files:
        errs = _check_skill(skill_md)
        all_errors.extend(errs)
        status = "OK" if not errs else "FAIL"
        print(f"{status}: {skill_md.parent.name}")

    if all_errors:
        print("", file=sys.stderr)
        for err in all_errors:
            print(err, file=sys.stderr)
        return 1

    print(f"\n{len(skill_files)} skills checked, all valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
