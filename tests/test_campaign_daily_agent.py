"""Tests for campaign daily snapshot agent."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

from agents.campaign_daily_snapshot_agent import (
    _compact_llm_payload,
    run_campaign_daily_snapshot_agent,
)
from config.settings import AppSettings
from models.agent_report import CheckStatus, Severity, TableAgentReport, ThresholdCheck
from models.campaign_daily_snapshot import CampaignDailyHygieneContext, CampaignDailySnapshotRow


def _row(
    name: str,
    campaign_type: str = "Search campaigns",
    *,
    campaign_id: str = "123",
    t1_cost: float = 100,
    today_cost: float = 120,
) -> CampaignDailySnapshotRow:
    return CampaignDailySnapshotRow(
        campaign_type=campaign_type,
        campaign_id=campaign_id,
        campaign_name=name,
        t1_date=date(2026, 7, 9),
        t1_cost=t1_cost,
        t2_date=date(2026, 7, 8),
        t2_cost=80,
        today_date=date(2026, 7, 10),
        today_cost=today_cost,
        t1_7day_avg_cost=90,
    )


@patch(
    "agents.campaign_daily_snapshot_agent.invoke_summary",
    return_value="Summary text.",
)
def test_campaign_daily_agent_one_summary_per_type(mock_summary):
    settings = AppSettings(openrouter_api_key="test")
    rows = [_row("Brand"), _row("Generic"), _row("Video A", "Video campaigns")]

    campaign_reports, overall, by_type = run_campaign_daily_snapshot_agent(
        rows,
        settings,
        hygiene=CampaignDailyHygieneContext(
            t1_date=date(2026, 7, 9),
            today_date=date(2026, 7, 10),
        ),
    )

    assert len(campaign_reports) == 3
    assert all(report.summary == "" for report in campaign_reports)
    assert all(len(report.checks) >= 6 for report in campaign_reports)
    assert overall is not None
    assert overall.campaign_type == "All campaigns"
    assert len(by_type) == 2
    assert {report.campaign_type for report in by_type} == {"Search campaigns", "Video campaigns"}
    assert all(report.summary == "Summary text." for report in by_type)
    assert mock_summary.call_count == 3


def test_compact_llm_payload_caps_large_campaign_sets():
    rows = [
        _row(f"Campaign {i}", campaign_id=str(i), t1_cost=float(i), today_cost=float(i))
        for i in range(80)
    ]
    reports = [
        TableAgentReport(
            table_name="Campaign daily spend snapshot",
            campaign_type="Search campaigns",
            campaign_id=str(i),
            campaign_name=f"Campaign {i}",
            checks=[
                ThresholdCheck(
                    rule="budget_amount_zero",
                    threshold="> 0",
                    actual="0",
                    status=CheckStatus.FAIL if i % 3 == 0 else CheckStatus.PASS,
                    message="fail" if i % 3 == 0 else "",
                )
            ],
            severity=Severity.CRITICAL if i % 3 == 0 else Severity.HEALTHY,
        )
        for i in range(80)
    ]

    payload = _compact_llm_payload("Search campaigns", rows, reports)

    assert "campaigns=80" in payload
    assert "Campaign 79" in payload  # top spender included
    assert "omitted=" in payload
    assert payload.count("'id':") <= 40
    assert len(payload) < 25_000
