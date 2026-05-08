"""Tests for compliance and size checks."""
from ac_builder.validate.pre_send import PreSendInputs, run_checks


def _inputs(html, footer_mode="launch", subject="Hi", preview="P"):
    return PreSendInputs(html=html, subject=subject, preview=preview, footer_mode=footer_mode)


def test_missing_unsubscribe_link_is_error_in_launch_mode():
    html = "<html><body><p>%SENDER-INFO%</p></body></html>"
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.errors}
    assert "missing-unsubscribe-link" in codes


def test_missing_sender_info_is_error_in_launch_mode():
    html = "<html><body><p>%UNSUBSCRIBELINK%</p></body></html>"
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.errors}
    assert "missing-sender-info" in codes


def test_compliance_tokens_present_no_finding():
    html = "<html><body><p>%UNSUBSCRIBELINK% %SENDER-INFO%</p></body></html>"
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.errors}
    assert "missing-unsubscribe-link" not in codes
    assert "missing-sender-info" not in codes


def test_html_over_100kb_is_error():
    big_html = "<html><body><p>%UNSUBSCRIBELINK% %SENDER-INFO%" + "x" * 101_000 + "</p></body></html>"
    report = run_checks(_inputs(big_html))
    codes = {f.code for f in report.errors}
    assert "html-size-error" in codes


def test_html_over_85kb_is_warning():
    medium_html = "<html><body><p>%UNSUBSCRIBELINK% %SENDER-INFO%" + "x" * 86_000 + "</p></body></html>"
    report = run_checks(_inputs(medium_html))
    codes = {f.code for f in report.warnings}
    assert "html-size-warn" in codes


def test_http_image_is_error():
    html = '<html><body><img src="http://example.com/x.jpg" alt="x" />%UNSUBSCRIBELINK% %SENDER-INFO%</body></html>'
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.errors}
    assert "http-image-src" in codes


def test_https_image_no_finding():
    html = '<html><body><img src="https://example.com/x.jpg" alt="x" />%UNSUBSCRIBELINK% %SENDER-INFO%</body></html>'
    report = run_checks(_inputs(html))
    codes = {f.code for f in report.errors}
    assert "http-image-src" not in codes


def test_onboarding_mode_does_not_require_unsubscribe():
    html = "<html><body><p>Welcome.</p></body></html>"
    report = run_checks(_inputs(html, footer_mode="onboarding"))
    codes = {f.code for f in report.errors}
    assert "missing-unsubscribe-link" not in codes


def test_onboarding_with_not_interested_url_is_error():
    html = '<html><body><a href="https://instituteofdigitaldentistry.com/not-interested/?cid=%CONTACTID%">x</a>%UNSUBSCRIBELINK% %SENDER-INFO%</body></html>'
    report = run_checks(_inputs(html, footer_mode="onboarding"))
    codes = {f.code for f in report.errors}
    assert "onboarding-has-not-interested" in codes
