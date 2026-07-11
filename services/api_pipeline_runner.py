"""Run the AI agent pipeline without Streamlit dependencies."""

from __future__ import annotations

import logging
from datetime import date

from agents.analyzer_table_agent import run_analyzer_table_agent
from agents.campaign_daily_snapshot_agent import run_campaign_daily_snapshot_agent
from agents.daily_snapshot_agent import run_daily_snapshot_agent
from agents.hourly_agent import run_hourly_agent
from agents.supervisor import run_supervisor
from models.pipeline_steps import AGENT_PIPELINE_STEPS, PipelineStepStatus, initial_step_status
from config.settings import AppSettings
from models.agent_report import PipelineAgentReport, TableAgentReport
from models.analyzer_input import AnalyzerResult
from models.campaign_daily_snapshot import CampaignDailyHygieneContext, CampaignDailySnapshotRow
from services.google_ads_fetch_service import (
    ANALYZER_LABELS,
    GoogleAdsFetchService,
    build_hourly_snapshot_rows,
)
from utils.mtd_metrics import reference_t_dates, t1_seven_day_window

logger = logging.getLogger(__name__)


def _run_hourly_agents(
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


def run_agent_pipeline(
    result: AnalyzerResult,
    settings: AppSettings,
    campaign_rows: list[CampaignDailySnapshotRow],
    fetch_service: GoogleAdsFetchService,
    customer_id: str,
    *,
    campaign_hygiene: CampaignDailyHygieneContext | None = None,
) -> tuple[PipelineAgentReport | None, dict[str, str], dict[str, list[dict[str, object]]], dict[str, str]]:
    step_status = initial_step_status()
    step_status["fetch"] = PipelineStepStatus.COMPLETE.value
    errors: dict[str, str] = {}
    hourly_by_label: dict[str, list[dict[str, object]]] = {}

    try:
        step_status["account"] = PipelineStepStatus.RUNNING.value
        analyzer_reports = run_analyzer_table_agent(result, settings)
        step_status["account"] = PipelineStepStatus.COMPLETE.value

        step_status["daily"] = PipelineStepStatus.RUNNING.value
        daily_reports = run_daily_snapshot_agent(result, settings)
        step_status["daily"] = PipelineStepStatus.COMPLETE.value

        step_status["hourly"] = PipelineStepStatus.RUNNING.value
        hourly_reports, hourly_by_label = _run_hourly_agents(fetch_service, customer_id, settings)
        step_status["hourly"] = PipelineStepStatus.COMPLETE.value

        step_status["campaign"] = PipelineStepStatus.RUNNING.value
        campaign_reports, campaign_overall, campaign_by_type = run_campaign_daily_snapshot_agent(
            campaign_rows, settings, hygiene=campaign_hygiene
        )
        step_status["campaign"] = PipelineStepStatus.COMPLETE.value

        pipeline_report = run_supervisor(analyzer_reports, daily_reports, hourly_reports, settings)
        pipeline_report = pipeline_report.model_copy(
            update={
                "campaign_daily_snapshot": campaign_reports,
                "campaign_daily_by_type": campaign_by_type,
                "campaign_daily_overall": campaign_overall,
            }
        )
        # Emails are sent from Budget Alerts (not here) so Run Analyzer stays fast/reliable.
        return pipeline_report, step_status, hourly_by_label, errors

    except Exception as exc:
        logger.exception("Agent pipeline failed")
        for step in AGENT_PIPELINE_STEPS:
            if step_status.get(step["id"]) == PipelineStepStatus.RUNNING.value:
                step_status[step["id"]] = PipelineStepStatus.ERROR.value
                errors[step["id"]] = str(exc)
                break
        return None, step_status, hourly_by_label, errors
