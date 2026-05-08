"""Tests for accessibility checks."""
from ac_builder.validate.pre_send import PreSendInputs, run_checks


def _inputs(html):
    return PreSendInputs(html=html, subject="Hi", preview="P", footer_mode="launch")


_BASE_TOKENS = "%UNSUBSCRIBELINK% %SENDER-INFO%"


def test_image_without_alt_is_error():
    html = f'<html lang="en"><body><img src="https://x.com/y.jpg" />{_BASE_TOKENS}</body></html>'
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.errors}
    assert "missing-alt-text" in codes


def test_image_with_alt_no_finding():
    html = f'<html lang="en"><body><img src="https://x.com/y.jpg" alt="Banner" />{_BASE_TOKENS}</body></html>'
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.errors}
    assert "missing-alt-text" not in codes


def test_image_with_empty_alt_no_finding():
    html = f'<html lang="en"><body><img src="https://x.com/y.jpg" alt="" />{_BASE_TOKENS}</body></html>'
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.errors}
    assert "missing-alt-text" not in codes


def test_missing_html_lang_is_warn():
    html = f"<html><body><p>{_BASE_TOKENS}</p></body></html>"
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.warnings}
    assert "missing-html-lang" in codes


def test_missing_title_is_warn():
    html = f'<html lang="en"><head></head><body>{_BASE_TOKENS}</body></html>'
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.warnings}
    assert "missing-title" in codes


def test_layout_table_without_role_is_warn():
    html = (
        f'<html lang="en"><head><title>x</title></head><body>'
        f'<table><tr><td>cell</td></tr></table>{_BASE_TOKENS}</body></html>'
    )
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.warnings}
    assert "table-missing-role" in codes


def test_layout_table_with_role_no_finding():
    html = (
        f'<html lang="en"><head><title>x</title></head><body>'
        f'<table role="presentation"><tr><td>cell</td></tr></table>{_BASE_TOKENS}</body></html>'
    )
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.warnings}
    assert "table-missing-role" not in codes
