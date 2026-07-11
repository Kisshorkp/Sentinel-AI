"""Run the four AI agents sequentially with optional pipeline UI updates."""

from __future__ import annotations

from datetime import date

import streamlit as st

from config.settings import AppSettings
from models.agent_report import PipelineAgentReport, TableAgentReport
from models.analyzer_input import AnalyzerResult
from models.campaign_daily_snapshot import CampaignDailyHygieneContext, CampaignDailySnapshotRow
from agents.analyzer_table_agent import run_analyzer_table_agent
from agents.campaign_daily_snapshot_agent import run_campaign_daily_snapshot_agent
from agents.daily_snapshot_agent import run_daily_snapshot_agent
from agents.hourly_agent import run_hourly_agent
from agents.supervisor import run_supervisor
from components.agent_pipeline_ui import AGENT_PIPELINE_STEPS, PipelineStepStatus, render_agent_pipeline
from services.google_ads_fetch_service import (
    ANALYZER_LABELS,
    GoogleAdsFetchService,
    build_hourly_snapshot_rows,
)
from utils.mtd_metrics import reference_t_dates, t1_seven_day_window


def _set_step(
    step_status: dict[str, str],
    step_id: str,
    status: PipelineStepStatus,
    ui_placeholder: st.delta_generator.DeltaGenerator | None,
) -> None:
    step_status[step_id] = status.value
    if ui_placeholder is not None:
        render_agent_pipeline(step_status, placeholder=ui_placeholder, interactive=False)


def _run_hourly_agents(
    fetch_service: GoogleAdsFetchService,
    customer_id: str,
    settings: AppSettings,
) -> tuple[list[TableAgentReport], dict[str, list[dict[str, object]]]]:
    """Fetch hourly data and run hourly agent for each campaign type."""
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


def run_sequential_agent_pipeline(
    result: AnalyzerResult,
    settings: AppSettings,
    campaign_rows: list[CampaignDailySnapshotRow],
    fetch_service: GoogleAdsFetchService,
    customer_id: str,
    *,
    campaign_hygiene: CampaignDailyHygieneContext | None = None,
    step_status: dict[str, str] | None = None,
    ui_placeholder: st.delta_generator.DeltaGenerator | None = None,
) -> tuple[PipelineAgentReport, dict[str, str], dict[str, list[dict[str, object]]] | None]:
    """
    Execute agents in order: Fetch (pre-complete) → Account → Daily → Hourly → Campaign.
    Returns pipeline report, final step status, and hourly rows by label.
    """
    if step_status is None:
        step_status = {step["id"]: PipelineStepStatus.PENDING.value for step in AGENT_PIPELINE_STEPS}
    else:
        step_status = dict(step_status)
    hourly_by_label: dict[str, list[dict[str, object]]] | None = None

    try:
        _set_step(step_status, "account", PipelineStepStatus.RUNNING, ui_placeholder)
        analyzer_reports = run_analyzer_table_agent(result, settings)
        _set_step(step_status, "account", PipelineStepStatus.COMPLETE, ui_placeholder)

        _set_step(step_status, "daily", PipelineStepStatus.RUNNING, ui_placeholder)
        daily_reports = run_daily_snapshot_agent(result, settings)
        _set_step(step_status, "daily", PipelineStepStatus.COMPLETE, ui_placeholder)

        _set_step(step_status, "hourly", PipelineStepStatus.RUNNING, ui_placeholder)
        hourly_reports, hourly_by_label = _run_hourly_agents(fetch_service, customer_id, settings)
        _set_step(step_status, "hourly", PipelineStepStatus.COMPLETE, ui_placeholder)

        _set_step(step_status, "campaign", PipelineStepStatus.RUNNING, ui_placeholder)
        campaign_reports, campaign_overall, campaign_by_type = run_campaign_daily_snapshot_agent(
            campaign_rows, settings, hygiene=campaign_hygiene
        )
        _set_step(step_status, "campaign", PipelineStepStatus.COMPLETE, ui_placeholder)

        pipeline_report = run_supervisor(analyzer_reports, daily_reports, hourly_reports, settings)
        pipeline_report = pipeline_report.model_copy(
            update={
                "campaign_daily_snapshot": campaign_reports,
                "campaign_daily_by_type": campaign_by_type,
                "campaign_daily_overall": campaign_overall,
            }
        )
        return pipeline_report, step_status, hourly_by_label

    except Exception as exc:
        errors = st.session_state.get("pipeline_step_errors") or {}
        for step_id, status in list(step_status.items()):
            if status == PipelineStepStatus.RUNNING.value:
                _set_step(step_status, step_id, PipelineStepStatus.ERROR, ui_placeholder)
                errors[step_id] = str(exc)
        st.session_state["pipeline_step_errors"] = errors
        raise
