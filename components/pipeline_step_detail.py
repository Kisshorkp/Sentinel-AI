"""Pipeline tabs — one tab per agent step with that step's data only."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.account_pipeline_tab import render_account_pipeline_tab
from components.daily_pipeline_tab import render_daily_pipeline_tab
from components.campaign_pipeline_tab import render_campaign_pipeline_tab
from components.hourly_pipeline_tab import render_hourly_pipeline_tab
from components.agent_pipeline_ui import AGENT_PIPELINE_STEPS, badge_label
from config.settings import AppSettings
from models.agent_report import PipelineAgentReport
from models.analyzer_input import AnalyzerResult
from models.campaign_daily_snapshot import CampaignDailySnapshotRow
from utils.fetch_preview import preview_records
from utils.formatting import format_currency

_PREVIEW_LIMIT = 10


def step_is_clickable(status: str) -> bool:
    return status in ("complete", "error")


__all__ = ["preview_records", "render_pipeline_step_detail", "render_pipeline_tabs", "step_is_clickable"]


def _tab_label(step: dict[str, str], status: str) -> str:
    badge = badge_label(step["id"], status)
    return f"{step['icon']} {step['title']} ({badge})"


def _render_locked_step(status: str) -> None:
    if status == "running":
        st.warning("This step is still running. Its data will appear here when it completes.")
    elif status == "error":
        st.error("This step failed. Check the error details once the run finishes.")
    else:
        st.info("This step is pending. Data will appear here after it completes.")


def _render_error(step_id: str, message: str, step_title: str) -> None:
    st.error(f"**{step_title} error:** {message}")


def _render_records_table(
    rows: list[dict[str, object]],
    *,
    currency: str,
    cost_columns: tuple[str, ...] = ("Cost",),
) -> None:
    if not rows:
        st.info("No records available for this step.")
        return

    df = pd.DataFrame(rows[:_PREVIEW_LIMIT])
    formatters = {
        column: (lambda v, c=currency: format_currency(v, c))
        for column in cost_columns
        if column in df.columns
    }
    st.dataframe(
        df.style.format(formatters) if formatters else df,
        use_container_width=True,
        hide_index=True,
    )
    if len(rows) > _PREVIEW_LIMIT:
        st.caption(f"Showing {_PREVIEW_LIMIT} of {len(rows)} records.")


def _google_ads_records_from_session() -> list[dict[str, object]]:
    records = st.session_state.get("google_ads_fetch_records") or []
    if records:
        return records

    result: AnalyzerResult | None = st.session_state.get("analyzer_result")
    if result is None:
        return []

    fallback: list[dict[str, object]] = []
    for field in result.fields:
        fallback.append(
            {
                "Campaign type": field.label,
                "Date": f"{field.start_date} → {field.end_date}",
                "Cost": field.cost,
                "Conversions": field.conversions,
                "Conv. value": field.conversions_value,
            }
        )
        for day_offset, daily_cost in enumerate(field.recent_daily_costs, start=1):
            fallback.append(
                {
                    "Campaign type": field.label,
                    "Date": f"Recent day {day_offset}",
                    "Cost": daily_cost,
                    "Conversions": 0.0,
                    "Conv. value": 0.0,
                }
            )
    return fallback


def _render_fetch_tab(settings: AppSettings) -> None:
    errors = st.session_state.get("pipeline_step_errors") or {}
    if errors.get("fetch"):
        _render_error("fetch", errors["fetch"], "Google Ads")
        return

    all_records = _google_ads_records_from_session()
    records = preview_records(all_records, _PREVIEW_LIMIT)
    result: AnalyzerResult | None = st.session_state.get("analyzer_result")
    st.caption("Google Ads API daily campaign metrics (up to 10 rows).")
    if result is not None:
        st.caption(f"Fetch window: {result.fetch_start_date} → {result.fetch_end_date}.")
    _render_records_table(records, currency=settings.app_currency, cost_columns=("Cost",))


def _render_account_tab(result: AnalyzerResult, settings: AppSettings, agent_report: PipelineAgentReport | None) -> None:
    errors = st.session_state.get("pipeline_step_errors") or {}
    if errors.get("account"):
        _render_error("account", errors["account"], "Account-wise")
        return

    render_account_pipeline_tab(result, settings, agent_report)


def _render_daily_tab(result: AnalyzerResult, settings: AppSettings, agent_report: PipelineAgentReport | None) -> None:
    errors = st.session_state.get("pipeline_step_errors") or {}
    if errors.get("daily"):
        _render_error("daily", errors["daily"], "Daily-wise")
        return

    render_daily_pipeline_tab(result, settings, agent_report)


def _render_hourly_tab(settings: AppSettings, agent_report: PipelineAgentReport | None) -> None:
    errors = st.session_state.get("pipeline_step_errors") or {}
    if errors.get("hourly"):
        _render_error("hourly", errors["hourly"], "Hourly")
        return

    hourly_by_label = st.session_state.get("hourly_rows_by_label") or {}
    render_hourly_pipeline_tab(hourly_by_label, settings, agent_report)


def _render_campaign_tab(settings: AppSettings, agent_report: PipelineAgentReport | None) -> None:
    errors = st.session_state.get("pipeline_step_errors") or {}
    if errors.get("campaign"):
        _render_error("campaign", errors["campaign"], "Campaign-wise")
        return

    campaign_rows: list[CampaignDailySnapshotRow] = st.session_state.get("campaign_daily_snapshot_rows") or []
    render_campaign_pipeline_tab(campaign_rows, settings, agent_report)


def _render_step_tab(
    step_id: str,
    step_status: dict[str, str],
    settings: AppSettings,
    result: AnalyzerResult | None,
    agent_report: PipelineAgentReport | None,
) -> None:
    status = step_status.get(step_id, "pending")
    if not step_is_clickable(status):
        _render_locked_step(status)
        return

    if step_id == "fetch":
        _render_fetch_tab(settings)
    elif step_id == "account" and result is not None:
        _render_account_tab(result, settings, agent_report)
    elif step_id == "daily" and result is not None:
        _render_daily_tab(result, settings, agent_report)
    elif step_id == "hourly":
        _render_hourly_tab(settings, agent_report)
    elif step_id == "campaign":
        _render_campaign_tab(settings, agent_report)
    else:
        st.info("Run the analyzer first to load data for this step.")


def render_pipeline_tabs(step_status: dict[str, str], settings: AppSettings) -> None:
    """Compact pipeline status row + one tab per step with that step's data only."""
    from components.agent_pipeline_ui import render_agent_pipeline

    st.markdown("##### AI Agent Pipeline")
    render_agent_pipeline(step_status, title="", interactive=False)
    st.caption("Pipeline status above. Open a tab below to view records for that step only.")

    tab_labels = [
        _tab_label(step, step_status.get(step["id"], "pending"))
        for step in AGENT_PIPELINE_STEPS
    ]
    tabs = st.tabs(tab_labels)
    result: AnalyzerResult | None = st.session_state.get("analyzer_result")
    agent_report: PipelineAgentReport | None = st.session_state.get("agent_report")

    for tab, step in zip(tabs, AGENT_PIPELINE_STEPS):
        with tab:
            _render_step_tab(step["id"], step_status, settings, result, agent_report)


def render_pipeline_step_detail(
    selected_step: str | None,
    step_status: dict[str, str] | None,
    settings: AppSettings,
) -> None:
    """Legacy single-step detail panel (kept for compatibility)."""
    if not selected_step or not step_status:
        return
    with st.container(border=True):
        _render_step_tab(
            selected_step,
            step_status,
            settings,
            st.session_state.get("analyzer_result"),
            st.session_state.get("agent_report"),
        )
