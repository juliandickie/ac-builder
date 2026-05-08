"""subprocess wrapper for the `mjml` CLI.

Calls Node's mjml binary installed at `tools/ac-builder/node_modules/.bin/mjml`.
Captures stdout (HTML) and stderr (errors/warnings) and returns a structured
MjmlResult or raises MjmlError on failure.

Reference: https://documentation.mjml.io/#cli
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

AC_BUILDER_ROOT = Path(__file__).resolve().parent.parent.parent
MJML_BIN = AC_BUILDER_ROOT / "node_modules" / ".bin" / "mjml"


class MjmlError(RuntimeError):
    """Raised when mjml compilation fails or produces blocking errors."""


@dataclass
class MjmlResult:
    """Result of a successful MJML compile."""
    html: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def mjml_version() -> str:
    """Return the installed mjml version, e.g. "4.15.3"."""
    if not MJML_BIN.exists():
        raise MjmlError(
            f"mjml binary not found at {MJML_BIN}. "
            "Run `npm install` in tools/ac-builder/ first."
        )
    proc = subprocess.run(
        [str(MJML_BIN), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or proc.stderr or "").strip()
    for line in out.splitlines():
        if ":" in line:
            ver = line.split(":", 1)[1].strip()
            if ver and ver[0].isdigit():
                return ver
    raise MjmlError(f"Could not parse mjml --version output: {out!r}")


def compile_mjml(
    mjml_source: str,
    *,
    validate: bool = True,
    base_path: Path | None = None,
) -> MjmlResult:
    """Compile MJML source to HTML.

    Args:
        mjml_source: The MJML document as a string.
        validate: If True, runs `--validate strict` so unknown tags / invalid
            attributes raise MjmlError.
        base_path: Optional. Sets the working directory for `mj-include` resolution.
            Default is `tools/ac-builder/templates/`.

    Raises:
        MjmlError: if mjml exits non-zero or validation finds blocking errors.
    """
    if not MJML_BIN.exists():
        raise MjmlError(
            f"mjml binary not found at {MJML_BIN}. "
            "Run `npm install` in tools/ac-builder/ first."
        )

    cwd = base_path or (AC_BUILDER_ROOT / "templates")

    # mjml CLI: -i = stdin, -s = stdout. Strict validation is via the
    # mjml-core config flag (--config.validationLevel=strict), NOT --validate
    # (which is the file-validator subcommand).
    args = [str(MJML_BIN), "-i", "-s"]
    if validate:
        args.append("--config.validationLevel=strict")

    proc = subprocess.run(
        args,
        input=mjml_source,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        check=False,
    )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    if proc.returncode != 0:
        raise MjmlError(
            f"mjml compilation failed (exit {proc.returncode}):\n{stderr}\n\n"
            f"Source (first 500 chars):\n{mjml_source[:500]}"
        )

    warnings = []
    errors = []
    for line in stderr.splitlines():
        line = line.strip()
        if not line:
            continue
        if "warning" in line.lower():
            warnings.append(line)
        elif "error" in line.lower():
            errors.append(line)

    if validate and errors:
        raise MjmlError("mjml validation errors:\n" + "\n".join(errors))

    return MjmlResult(html=stdout, warnings=warnings, errors=errors)
