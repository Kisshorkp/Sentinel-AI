"""LangGraph state for the dashboard spend-check agent (isolated from analyzer graph)."""

from __future__ import annotations

from typing import Any, TypedDict

from models.agent_report import PipelineAgentReport, TableAgentReport
from models.analyzer_input import AnalyzerResult
from models.campaign_daily_snapshot import CampaignDailyHygieneContext, CampaignDailySnapshotRow
from services.google_ads_fetch_service import GoogleAdsFetchService


class DashboardAgentState(TypedDict, total=False):
    """State for the dashboard-only LangGraph pipeline."""

    result: AnalyzerResult
    campaign_rows: list[CampaignDailySnapshotRow]
    campaign_hygiene: CampaignDailyHygieneContext | None
    customer_id: str
    fetch_service: GoogleAdsFetchService
    settings: Any

    account_reports: list[TableAgentReport]
    daily_reports: list[TableAgentReport]
    hourly_reports: list[TableAgentReport]
    hourly_rows_by_label: dict[str, list[dict[str, object]]]
    campaign_reports: list[TableAgentReport]
    campaign_by_type: list[TableAgentReport]
    campaign_overall: TableAgentReport | None

    agent_report: PipelineAgentReport
    errors: dict[str, str]
