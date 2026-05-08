"""Tests for the mjml CLI subprocess wrapper."""
import pytest

from ac_builder.render.mjml_runner import (
    MjmlError,
    MjmlResult,
    compile_mjml,
    mjml_version,
)


def test_mjml_version_returns_a_version_string():
    v = mjml_version()
    assert isinstance(v, str)
    assert "." in v


def test_compile_mjml_simple_returns_html():
    mjml = """
    <mjml>
      <mj-body>
        <mj-section>
          <mj-column>
            <mj-text>Hello world</mj-text>
          </mj-column>
        </mj-section>
      </mj-body>
    </mjml>
    """
    result = compile_mjml(mjml)
    assert isinstance(result, MjmlResult)
    assert "<html" in result.html.lower()
    assert "Hello world" in result.html
    assert result.errors == []


def test_compile_mjml_invalid_raises_with_useful_error():
    mjml = "<mjml><mj-body><mj-not-a-real-tag /></mj-body></mjml>"
    with pytest.raises(MjmlError) as exc_info:
        compile_mjml(mjml, validate=True)
    assert "mj-not-a-real-tag" in str(exc_info.value).lower() or "unknown" in str(exc_info.value).lower()


def test_compile_mjml_strict_validation_catches_warnings():
    mjml = """
    <mjml>
      <mj-body>
        <mj-section>
          <mj-column>
            <mj-text>OK</mj-text>
          </mj-column>
        </mj-section>
      </mj-body>
    </mjml>
    """
    result = compile_mjml(mjml, validate=False)
    assert "OK" in result.html
