"""Tests for pre_send infrastructure: CheckFinding, CheckReport, run_checks."""
from ac_builder.validate.pre_send import (
    CheckFinding,
    CheckReport,
    PreSendInputs,
    run_checks,
)


def test_check_finding_dataclass():
    f = CheckFinding(code="x", severity="ERROR", message="m")
    assert f.code == "x"
    assert f.severity == "ERROR"
    assert f.message == "m"


def test_check_report_has_errors_property():
    r = CheckReport(findings=[
        CheckFinding(code="a", severity="WARN", message="w"),
        CheckFinding(code="b", severity="ERROR", message="e"),
    ])
    assert r.has_errors is True
    assert r.warning_count == 1
    assert r.error_count == 1


def test_check_report_no_errors():
    r = CheckReport(findings=[CheckFinding(code="a", severity="WARN", message="w")])
    assert r.has_errors is False


def test_run_checks_returns_check_report():
    inputs = PreSendInputs(
        html="<html><body><p>%UNSUBSCRIBELINK% %SENDER-INFO%</p></body></html>",
        subject="Hi",
        preview="A preview",
        footer_mode="launch",
    )
    report = run_checks(inputs)
    assert isinstance(report, CheckReport)
