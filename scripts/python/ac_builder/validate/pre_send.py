"""Pre-send validation suite for rendered email HTML.

Runs a series of checks before any --apply write to AC. ERROR-severity findings
abort the build for that email; WARN findings print to stderr but proceed.

Usage:
    inputs = PreSendInputs(html=..., subject=..., preview=..., footer_mode="launch")
    report = run_checks(inputs)
    if report.has_errors:
        # Abort build for this email
        ...
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class CheckFinding:
    """One finding from a single check."""
    code: str          # Stable identifier e.g. "html-size-error"
    severity: str      # "ERROR" or "WARN"
    message: str       # Human-readable description
    location: str | None = None


@dataclass
class CheckReport:
    """Output of a pre-send check run."""
    findings: list[CheckFinding] = field(default_factory=list)

    @property
    def errors(self) -> list[CheckFinding]:
        return [f for f in self.findings if f.severity == "ERROR"]

    @property
    def warnings(self) -> list[CheckFinding]:
        return [f for f in self.findings if f.severity == "WARN"]

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0


@dataclass
class PreSendInputs:
    """Inputs to run_checks()."""
    html: str
    subject: str
    preview: str
    footer_mode: str    # "launch" | "onboarding" | "transactional"
    theme_cta_bg: str | None = None
    theme_cta_text: str | None = None


CheckFn = Callable[[PreSendInputs], list[CheckFinding]]
_CHECKS: list[CheckFn] = []


def register_check(fn: CheckFn) -> CheckFn:
    """Decorator: register a check function in the global suite."""
    _CHECKS.append(fn)
    return fn


def run_checks(inputs: PreSendInputs) -> CheckReport:
    """Run all registered checks and return a consolidated CheckReport."""
    findings: list[CheckFinding] = []
    for check in _CHECKS:
        findings.extend(check(inputs))
    return CheckReport(findings=findings)


# Trigger check module imports so registrations happen.
from ac_builder.validate import _checks_compliance  # noqa: E402,F401
from ac_builder.validate import _checks_accessibility  # noqa: E402,F401
from ac_builder.validate import _checks_stylistic  # noqa: E402,F401
