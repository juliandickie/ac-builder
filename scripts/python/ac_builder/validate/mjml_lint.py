"""MJML strict validation as a standalone callable.

Re-exports mjml_runner.compile_mjml(validate=True) for callers who want to
lint MJML without rendering to final HTML. Keeps validation-related imports
together.
"""
from __future__ import annotations

from ac_builder.render.mjml_runner import MjmlError, MjmlResult, compile_mjml


def lint_mjml(mjml_source: str) -> MjmlResult:
    """Validate MJML in strict mode. Raises MjmlError on blocking issues.

    Returns the MjmlResult on success - the .html is the side effect of
    validation, not the primary output here.
    """
    return compile_mjml(mjml_source, validate=True)


__all__ = ["lint_mjml", "MjmlError", "MjmlResult"]
