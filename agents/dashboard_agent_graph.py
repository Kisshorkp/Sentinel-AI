"""Dashboard LangGraph agent — account / daily / hourly / campaign checks.

Isolated from the Campaign Analysis pipeline (`agents/graph.py`, `api_pipeline_runner`).
Reuses existing `run_*` agent functions without modifying them.
"""

from __future__ import annotations

import logging
from datetime import date

from config.settings import AppSettings
from models.agent_report import PipelineAgentReport, TableAgentReport
from models.analyzer_input import AnalyzerResult
from models.campaign_daily_snapshot import CampaignDailyHygieneContext, CampaignDailySnapshotRow
from agents.analyzer_table_agent import run_analyzer_table_agent
from agents.campaign_daily_snapshot_agent import run_campaign_daily_snapshot_agent
from agents.daily_snapshot_agent import run_daily_snapshot_agent
from agents.hourly_agent import run_hourly_agent
from agents.supervisor import run_supervisor
from services.google_ads_fetch_service import (
    ANALYZER_LABELS,
    GoogleAdsFetchService,
    build_hourly_snapshot_rows,
)
from utils.mtd_metrics import reference_t_dates, t1_seven_day_window

logger = logging.getLogger(__name__)


def _run_hourly(
    fetch_service: GoogleAdsFetchService,
    customer_id: str,
    settings: AppSettings,
) -> tuple[list[TableAgentReport], dict[str, list[dict[str, object]]]]:
    t1_date, t2_date = reference_t_dates()
    today_date = date.today()
    avg_window_start, avg_window_end = t1_seven_day_window()
    store = fetch_service.fetch_hourly_metrics(
        customer_id, avg_window_start, max(avg_window_end, today_date)
    )

    hourly_by_label: dict[str, list[dict[str, object]]] = {}
    hourly_reports: list[TableAgentReport] = []
    for label in ANALYZER_LABELS:
        rows = build_hourly_snapshot_rows(
            store, label, t1_date, t2_date, today_date, avg_window_start, avg_window_end
        )
        hourly_by_label[label] = rows
        hourly_reports.append(run_hourly_agent(label, rows, settings))
    return hourly_reports, hourly_by_label


def _run_direct(
    result: AnalyzerResult,
    settings: AppSettings,
    campaign_rows: list[CampaignDailySnapshotRow],
    fetch_service: GoogleAdsFetchService,
    customer_id: str,
    *,
    campaign_hygiene: CampaignDailyHygieneContext | None = None,
) -> tuple[PipelineAgentReport, dict[str, list[dict[str, object]]], dict[str, str]]:
    errors: dict[str, str] = {}
    hourly_by_label: dict[str, list[dict[str, object]]] = {}

    account_reports = run_analyzer_table_agent(result, settings)
    daily_reports = run_daily_snapshot_agent(result, settings)
    hourly_reports, hourly_by_label = _run_hourly(fetch_service, customer_id, settings)
    campaign_reports, campaign_overall, campaign_by_type = run_campaign_daily_snapshot_agent(
        campaign_rows, settings, hygiene=campaign_hygiene
    )
    report = run_supervisor(account_reports, daily_reports, hourly_reports, settings)
    report = report.model_copy(
        update={
            "campaign_daily_snapshot": campaign_reports,
            "campaign_daily_by_type": campaign_by_type,
            "campaign_daily_overall": campaign_overall,
        }
    )
    return report, hourly_by_label, errors


def _run_with_langgraph(
    result: AnalyzerResult,
    settings: AppSettings,
    campaign_rows: list[CampaignDailySnapshotRow],
    fetch_service: GoogleAdsFetchService,
    customer_id: str,
    *,
    campaign_hygiene: CampaignDailyHygieneContext | None = None,
) -> tuple[PipelineAgentReport, dict[str, list[dict[str, object]]], dict[str, str]]:
    from langgraph.graph import END, START, StateGraph

    from agents.dashboard_agent_state import DashboardAgentState

    def account_node(state: DashboardAgentState) -> dict:
        try:
            reports = run_analyzer_table_agent(state["result"], settings)
            return {"account_reports": reports}
        except Exception as exc:
            logger.exception("Dashboard account agent failed")
            return {"account_reports": [], "errors": {**(state.get("errors") or {}), "account": str(exc)}}

    def daily_node(state: DashboardAgentState) -> dict:
        try:
            reports = run_daily_snapshot_agent(state["result"], settings)
            return {"daily_reports": reports}
        except Exception as exc:
            logger.exception("Dashboard daily agent failed")
            return {"daily_reports": [], "errors": {**(state.get("errors") or {}), "daily": str(exc)}}

    def hourly_node(state: DashboardAgentState) -> dict:
        try:
            reports, by_label = _run_hourly(fetch_service, customer_id, settings)
            return {"hourly_reports": reports, "hourly_rows_by_label": by_label}
        except Exception as exc:
            logger.exception("Dashboard hourly agent failed")
            return {
                "hourly_reports": [],
                "hourly_rows_by_label": {},
                "errors": {**(state.get("errors") or {}), "hourly": str(exc)},
            }

    def campaign_node(state: DashboardAgentState) -> dict:
        try:
            reports, overall, by_type = run_campaign_daily_snapshot_agent(
                state.get("campaign_rows") or [],
                settings,
                hygiene=state.get("campaign_hygiene"),
            )
            return {
                "campaign_reports": reports,
                "campaign_overall": overall,
                "campaign_by_type": by_type,
            }
        except Exception as exc:
            logger.exception("Dashboard campaign agent failed")
            return {
                "campaign_reports": [],
                "campaign_overall": None,
                "campaign_by_type": [],
                "errors": {**(state.get("errors") or {}), "campaign": str(exc)},
            }

    def supervisor_node(state: DashboardAgentState) -> dict:
        report = run_supervisor(
            state.get("account_reports") or [],
            state.get("daily_reports") or [],
            state.get("hourly_reports") or [],
            settings,
        )
        report = report.model_copy(
            update={
                "campaign_daily_snapshot": state.get("campaign_reports") or [],
                "campaign_daily_by_type": state.get("campaign_by_type") or [],
                "campaign_daily_overall": state.get("campaign_overall"),
            }
        )
        return {"agent_report": report}

    graph = StateGraph(DashboardAgentState)
    graph.add_node("account", account_node)
    graph.add_node("daily", daily_node)
    graph.add_node("hourly", hourly_node)
    graph.add_node("campaign", campaign_node)
    graph.add_node("supervisor", supervisor_node)

    # Sequential checks (avoids parallel Google Ads rate limits + state merge issues).
    graph.add_edge(START, "account")
    graph.add_edge("account", "daily")
    graph.add_edge("daily", "hourly")
    graph.add_edge("hourly", "campaign")
    graph.add_edge("campaign", "supervisor")
    graph.add_edge("supervisor", END)

    app = graph.compile()
    final = app.invoke(
        {
            "result": result,
            "campaign_rows": campaign_rows,
            "campaign_hygiene": campaign_hygiene,
            "customer_id": customer_id,
            "errors": {},
        }
    )
    return (
        final["agent_report"],
        final.get("hourly_rows_by_label") or {},
        final.get("errors") or {},
    )


def run_dashboard_agent(
    result: AnalyzerResult,
    settings: AppSettings,
    campaign_rows: list[CampaignDailySnapshotRow],
    fetch_service: GoogleAdsFetchService,
    customer_id: str,
    *,
    campaign_hygiene: CampaignDailyHygieneContext | None = None,
) -> tuple[PipelineAgentReport, dict[str, list[dict[str, object]]], dict[str, str]]:
    """Run the dashboard spend-check agent (LangGraph when available)."""
    try:
        return _run_with_langgraph(
            result,
            settings,
            campaign_rows,
            fetch_service,
            customer_id,
            campaign_hygiene=campaign_hygiene,
        )
    except ImportError:
        logger.info("langgraph not installed — running dashboard agent sequentially")
        return _run_direct(
            result,
            settings,
            campaign_rows,
            fetch_service,
            customer_id,
            campaign_hygiene=campaign_hygiene,
        )
