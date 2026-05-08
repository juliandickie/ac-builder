"""Tests for stylistic / length / contrast checks."""
from ac_builder.validate.pre_send import PreSendInputs, run_checks

_BASE_TOKENS = "%UNSUBSCRIBELINK% %SENDER-INFO%"


def _inp(html=None, subject="Hi", preview="P", footer_mode="launch", theme_cta_bg=None, theme_cta_text=None):
    return PreSendInputs(
        html=html or f'<html lang="en"><head><title>x</title></head><body><p>{_BASE_TOKENS}</p></body></html>',
        subject=subject,
        preview=preview,
        footer_mode=footer_mode,
        theme_cta_bg=theme_cta_bg,
        theme_cta_text=theme_cta_text,
    )


def test_subject_over_33_chars_is_warn():
    long = "This subject line is more than thirty-three characters long"
    report = run_checks(_inp(subject=long))
    codes = {f.code for f in report.warnings}
    assert "subject-mobile-truncation" in codes


def test_subject_under_33_chars_no_finding():
    report = run_checks(_inp(subject="Short subject"))
    codes = {f.code for f in report.warnings}
    assert "subject-mobile-truncation" not in codes


def test_preview_over_85_chars_is_warn():
    long = "x" * 86
    report = run_checks(_inp(preview=long))
    codes = {f.code for f in report.warnings}
    assert "preview-too-long" in codes


def test_low_contrast_cta_is_warn():
    report = run_checks(_inp(theme_cta_bg="#ffffff", theme_cta_text="#ffff00"))
    codes = {f.code for f in report.warnings}
    assert "cta-low-contrast" in codes


def test_high_contrast_cta_no_finding():
    report = run_checks(_inp(theme_cta_bg="#0a3d62", theme_cta_text="#ffffff"))
    codes = {f.code for f in report.warnings}
    assert "cta-low-contrast" not in codes


def test_firstname_literal_warn():
    html = f'<html lang="en"><head><title>x</title></head><body><p>Hi %FIRSTNAME%, {_BASE_TOKENS}</p></body></html>'
    report = run_checks(_inp(html=html))
    codes = {f.code for f in report.warnings}
    assert "firstname-missing-modifier" in codes


def test_firstname_with_titlecase_no_finding():
    html = f'<html lang="en"><head><title>x</title></head><body><p>Hi %FIRSTNAME|TITLECASE%, {_BASE_TOKENS}</p></body></html>'
    report = run_checks(_inp(html=html))
    codes = {f.code for f in report.warnings}
    assert "firstname-missing-modifier" not in codes
