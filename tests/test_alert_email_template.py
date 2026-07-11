"""Tests for critical alert HTML email template (INR)."""

from __future__ import annotations

from models.agent_report import CheckStatus, Severity, TableAgentReport, ThresholdCheck
from services.alert_email_template import build_critical_alert_email_html


def test_critical_alert_html_uses_inr_and_campaign_fields():
    report = TableAgentReport(
        table_name="Campaign daily spend snapshot",
        campaign_type="Performance Max campaigns",
        campaign_id="999",
        campaign_name="Performance Max - Brand US",
        severity=Severity.CRITICAL,
        checks=[
            ThresholdCheck(
                rule="budget_used_pct",
                threshold="<= 100%",
                actual="2299.7%",
                status=CheckStatus.FAIL,
                message="Cost exceeds budget",
            )
        ],
    )
    html = build_critical_alert_email_html(
        report,
        report.checks,
        ai_insight="Abnormal spend acceleration detected. Immediate review recommended.",
        currency="INR",
        meta={
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "budget_amount": 7000,
            "budget_period": "DAILY",
            "primary_status": "ELIGIBLE",
            "spend": 160979.14,
            "utilization_pct": 2299.7,
            "mtd_target": 6416.67,
            "mtd_actual": 153749.49,
        },
    )
    assert "Critical Budget Alert" in html
    assert "Performance Max - Brand US" in html
    assert "Start Date" in html
    assert "End Date" in html
    assert "Budget" in html
    assert "Status" in html
    assert "₹" in html
    assert "INR" in html
    assert "$7,000" not in html
    assert "AI Insight" in html
    assert "Budget Health" not in html
    assert "Budget Used Pct" not in html
    assert "MTD Spend" not in html
