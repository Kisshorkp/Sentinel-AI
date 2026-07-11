"""Unit tests for the isolated dashboard LangGraph agent (no Google Ads calls)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from config.settings import AppSettings
from models.agent_report import PipelineAgentReport, Severity, TableAgentReport
from models.analyzer_input import AnalyzerResult, CampaignFieldInput


def _field(label: str) -> CampaignFieldInput:
    today = date.today()
    return CampaignFieldInput(
        label=label,
        budget=100000,
        cost=40000,
        converted_cost=40000,
        conversions=10,
        conversions_value=50000,
        mtd_achieve=35000,
        mtd_target=40000,
        mtd_achieve_end=today,
        t1_date=today,
        t1_cost=5000,
        t2_date=today,
        t2_cost=4800,
        t1_7day_avg_cost=4500,
        recent_daily_costs=[4000, 4200, 4500, 4600, 4700, 4800, 5000],
        today_date=today,
        today_cost=1200,
        start_date=today.replace(day=1),
        end_date=today,
    )


def test_run_dashboard_agent_direct_path():
    settings = AppSettings()
    labels = [
        "Search campaigns",
        "Video campaigns",
        "Demand Gen campaigns",
        "Performance Max campaigns",
    ]
    fields = [_field(label) for label in labels]
    result = AnalyzerResult(
        account="123",
        account_start_date=fields[0].start_date,
        account_end_date=fields[0].end_date,
        fetch_start_date=fields[0].start_date,
        fetch_end_date=fields[0].end_date,
        fields=fields,
        total_budget=400000,
        total_spend=160000,
        total_converted_cost=160000,
        total_conversions=40,
        total_conversions_value=200000,
        highest_spend_field=labels[0],
        lowest_spend_field=labels[-1],
        data_source="test",
    )

    account_report = TableAgentReport(
        table_name="account", campaign_type=labels[0], severity=Severity.HEALTHY, summary="ok"
    )
    daily_report = TableAgentReport(
        table_name="daily", campaign_type=labels[0], severity=Severity.WARNING, summary="warn"
    )
    hourly_report = TableAgentReport(
        table_name="hourly", campaign_type=labels[0], severity=Severity.HEALTHY, summary="ok"
    )
    campaign_report = TableAgentReport(
        table_name="campaign", campaign_type=labels[0], severity=Severity.HEALTHY, summary="ok"
    )

    with (
        patch("agents.dashboard_agent_graph.run_analyzer_table_agent", return_value=[account_report]),
        patch("agents.dashboard_agent_graph.run_daily_snapshot_agent", return_value=[daily_report]),
        patch(
            "agents.dashboard_agent_graph._run_hourly",
            return_value=([hourly_report], {labels[0]: []}),
        ),
        patch(
            "agents.dashboard_agent_graph.run_campaign_daily_snapshot_agent",
            return_value=([campaign_report], campaign_report, []),
        ),
        patch(
            "agents.dashboard_agent_graph.run_supervisor",
            return_value=PipelineAgentReport(
                analyzer_table=[account_report],
                daily_snapshot=[daily_report],
                hourly_snapshot=[hourly_report],
                overall_severity=Severity.WARNING,
                overall_summary="Dashboard agent summary",
            ),
        ),
        patch("agents.dashboard_agent_graph._run_with_langgraph", side_effect=ImportError("no lg")),
    ):
        from agents.dashboard_agent_graph import run_dashboard_agent

        report, hourly_by_label, errors = run_dashboard_agent(
            result,
            settings,
            [],
            MagicMock(),
            "123",
        )

    assert report.overall_severity == Severity.WARNING
    assert report.overall_summary == "Dashboard agent summary"
    assert report.campaign_daily_snapshot == [campaign_report]
    assert labels[0] in hourly_by_label
    assert errors == {}
