"""Tests for pipeline alerts grouping service."""

from __future__ import annotations

from unittest.mock import patch

from config.settings import AppSettings
from models.agent_report import CheckStatus, PipelineAgentReport, Severity, TableAgentReport, ThresholdCheck
from models.campaign import RiskLevel, SpendAlert
from services.pipeline_alerts_service import build_pipeline_alerts, count_pipeline_alerts


def _report(
    table_name: str,
    *,
    rule: str = "mtd_vs_target",
    status: CheckStatus = CheckStatus.WARNING,
    campaign_name: str | None = None,
    email_sent: bool = False,
) -> TableAgentReport:
    return TableAgentReport(
        table_name=table_name,
        campaign_name=campaign_name,
        checks=[
            ThresholdCheck(
                rule=rule,
                threshold="100%",
                actual="110%",
                status=status,
                message=f"{rule} exceeded threshold",
            )
        ],
        severity=Severity.WARNING,
        summary="Test summary",
        email_sent=email_sent,
    )


def test_build_pipeline_alerts_from_agent_report():
    report = PipelineAgentReport(
        analyzer_table=[_report("account_overview")],
        daily_snapshot=[_report("daily", campaign_name="Search")],
        hourly_snapshot=[_report("hourly", rule="hourly_spike")],
        campaign_daily_snapshot=[_report("campaign", campaign_name="Brand Search", rule="daily_spend")],
    )

    grouped = build_pipeline_alerts(report)

    assert len(grouped["account"]) == 1
    assert len(grouped["daily"]) == 1
    assert len(grouped["hourly"]) == 1
    assert len(grouped["campaign"]) == 1
    assert grouped["account"][0]["severity"] == "warning"
    assert grouped["campaign"][0]["campaign_name"] == "Brand Search"
    assert count_pipeline_alerts(grouped) == 4


def test_email_sent_only_on_critical_pipeline_alerts():
    report = PipelineAgentReport(
        analyzer_table=[
            _report("account_overview", status=CheckStatus.WARNING),
            _report("account_overview", status=CheckStatus.FAIL, email_sent=True),
        ],
    )

    grouped = build_pipeline_alerts(report)

    critical = next(a for a in grouped["account"] if a["severity"] == "critical")
    warning = next(a for a in grouped["account"] if a["severity"] == "warning")
    assert warning["email_sent"] is False
    assert critical["email_sent"] is True


@patch("services.pipeline_alerts_service.send_spend_alert_email", return_value=True)
def test_budget_fallback_sends_email_for_critical_only(mock_send):
    spend_alerts = [
        SpendAlert(
            campaign_id="1",
            campaign_name="YouTube Awareness",
            stakeholder="Marketing",
            risk_level=RiskLevel.OVER_BUDGET,
            utilization_pct=103.4,
            overspend_amount=3400,
            message="YouTube Awareness exceeded budget by 3,400.00",
        ),
        SpendAlert(
            campaign_id="2",
            campaign_name="Brand Search",
            stakeholder="Marketing",
            risk_level=RiskLevel.WARNING,
            utilization_pct=85.0,
            overspend_amount=0,
            message="Brand Search reached 85% of monthly budget.",
        ),
    ]
    settings = AppSettings()

    grouped = build_pipeline_alerts(None, spend_alerts, settings)

    assert grouped["account"][0]["email_sent"] is True
    assert grouped["account"][1]["email_sent"] is False
    mock_send.assert_called_once()


def test_pass_checks_are_excluded():
    report = PipelineAgentReport(
        analyzer_table=[
            TableAgentReport(
                table_name="account_overview",
                checks=[
                    ThresholdCheck(
                        rule="mtd_vs_target",
                        threshold="100%",
                        actual="90%",
                        status=CheckStatus.PASS,
                        message="Within limit",
                    )
                ],
            )
        ],
    )

    grouped = build_pipeline_alerts(report)
    assert grouped["account"] == []
    assert count_pipeline_alerts(grouped) == 0
