"""Tests for per-table email alerts."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from config.settings import AppSettings
from models.agent_report import CheckStatus, PipelineAgentReport, TableAgentReport, ThresholdCheck
from agents.email_agent import (
    _resolve_recipients,
    run_pipeline_email_alerts,
    send_table_email_alert,
)


def _report(table_name: str, campaign: str, status: CheckStatus, **kwargs) -> TableAgentReport:
    return TableAgentReport(
        table_name=table_name,
        campaign_type=campaign,
        checks=[
            ThresholdCheck(
                rule="test_rule",
                threshold="x",
                actual="y",
                status=status,
                message="test issue",
            )
        ],
        summary="Test summary",
        **kwargs,
    )


def test_resolve_recipients_uses_default_env():
    settings = MagicMock()
    settings.default_alert_recipients = ["kishorkp4912@gmail.com"]
    with patch("agents.email_agent._load_yaml_recipients", return_value={}):
        recipients = _resolve_recipients(settings, "Search campaigns")
    assert "kishorkp4912@gmail.com" in recipients


@patch("agents.email_agent._resolve_recipients", return_value=["kishorkp4912@gmail.com"])
@patch("agents.email_agent.invoke_summary", return_value="Email body")
def test_send_table_email_alert_skips_warning(mock_summary, mock_recipients):
    settings = AppSettings(openrouter_api_key="test-key", SMTP_HOST="", SMTP_USER="", SMTP_PASSWORD="")
    report = _report("Analyzer results", "Search campaigns", CheckStatus.WARNING)

    sent, log = send_table_email_alert(report, settings)

    assert sent is False
    assert log == []
    mock_summary.assert_not_called()


@patch("agents.email_agent._resolve_recipients", return_value=["kishorkp4912@gmail.com"])
@patch("agents.email_agent.invoke_summary", return_value="Email body")
def test_send_table_email_alert_demo_mode(mock_summary, mock_recipients):
    settings = AppSettings(openrouter_api_key="test-key", SMTP_HOST="", SMTP_USER="", SMTP_PASSWORD="")
    report = _report("Analyzer results", "Video campaigns", CheckStatus.FAIL)

    sent, log = send_table_email_alert(report, settings)

    assert sent is False
    assert log == []
    mock_summary.assert_called_once()


@patch("agents.email_agent._resolve_recipients", return_value=["kishorkp4912@gmail.com"])
def test_send_table_email_skips_when_all_pass(mock_recipients):
    settings = AppSettings(openrouter_api_key="test-key")
    report = _report("Daily spend snapshot", "Video campaigns", CheckStatus.PASS)

    sent, log = send_table_email_alert(report, settings)

    assert sent is False
    assert log == []


@patch("agents.email_agent.EmailService")
@patch("agents.email_agent._resolve_recipients", return_value=["kishorkp4912@gmail.com"])
@patch("agents.email_agent.invoke_summary", return_value="AI detected abnormal spend in INR.")
def test_send_table_email_when_smtp_configured(mock_summary, mock_recipients, mock_email_service):
    settings = AppSettings(
        openrouter_api_key="test-key",
        SMTP_HOST="smtp.gmail.com",
        SMTP_USER="sender@gmail.com",
        SMTP_PASSWORD="secret",
    )
    report = _report(
        "Campaign daily spend snapshot",
        "Search campaigns",
        CheckStatus.FAIL,
        campaign_id="1234567890",
        campaign_name="Brand Search IN",
        start_date="2026-01-01",
        end_date="2026-12-31",
        budget_amount=7000,
        budget_period="DAILY",
        primary_status="ELIGIBLE",
        spend_amount=160979.14,
        utilization_pct=2299.7,
    )

    sent, log = send_table_email_alert(report, settings)

    assert sent is True
    assert log == []
    mock_email_service.return_value.send.assert_called_once()
    args, kwargs = mock_email_service.return_value.send.call_args
    assert kwargs.get("html_body") or (len(args) >= 4)
    html = kwargs.get("html_body") or args[3]
    assert "₹" in html or "INR" in html
    assert "Critical Budget Alert" in html
    assert "Brand Search IN" in html
    assert "Start Date" in html
    assert "$" not in html.replace("$#", "")  # no dollar currency amounts


@patch("agents.email_agent.send_table_email_alert", side_effect=[(True, []), (False, [])])
def test_run_pipeline_email_alerts(mock_send):
    settings = AppSettings(openrouter_api_key="test-key")
    pipeline = PipelineAgentReport(
        analyzer_table=[_report("Analyzer results", "Search campaigns", CheckStatus.FAIL)],
        daily_snapshot=[_report("Daily spend snapshot", "Search campaigns", CheckStatus.PASS)],
    )

    updated = run_pipeline_email_alerts(pipeline, settings)

    assert updated.email_sent is True
    assert updated.email_log == []
    assert updated.analyzer_table[0].email_sent is True
