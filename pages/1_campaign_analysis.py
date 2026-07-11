"""Campaign-level spend analysis page."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from agents.email_agent import run_email_agent, run_pipeline_email_alerts
from agents.sequential_pipeline import run_sequential_agent_pipeline
from agents.hourly_agent import run_hourly_agent
from components.agent_summary_panel import render_pipeline_report, render_table_agent_report
from components.analyzer_form import render_analyzer_form
from components.agent_pipeline_ui import (
    PipelineStepStatus,
    initial_step_status,
    render_agent_pipeline,
    render_pipeline_anchor,
)
from components.pipeline_step_detail import render_pipeline_tabs
from components.campaign_daily_snapshot_table import render_campaign_daily_snapshot_table
from components.chat_panel import render_chat_panel
from components.credentials_panel import render_google_ads_credentials_info
from config.settings import AppSettings
from models.analyzer_input import AnalyzerResult
from services.campaign_analyzer_service import CampaignAnalyzerService
from services.campaign_daily_snapshot_service import CampaignDailySnapshotService
from services.campaign_data_service import CampaignDataService
from services.google_ads_fetch_service import (
    GoogleAdsFetchService,
    HourlyMetricsStore,
    build_hourly_snapshot_rows,
)
from services.spend_analytics_service import SpendAnalyticsService
from utils.formatting import format_currency, risk_label
from utils.streamlit_helpers import init_page
from utils.mtd_metrics import achieve_end_date, t1_seven_day_window
from utils.ui_styles import inject_app_styles

ANALYZER_LOGIC_VERSION = 23


def _clear_analyzer_session() -> None:
    st.session_state.pop("analyzer_result", None)
    st.session_state.pop("analyzer_fetched", None)
    st.session_state.pop("agent_report", None)
    st.session_state.pop("hourly_agent_report", None)
    st.session_state.pop("hourly_rows_for_chat", None)
    st.session_state.pop("hourly_extract_label", None)
    st.session_state.pop("hourly_metrics_cache_key", None)
    st.session_state.pop("hourly_metrics_store", None)
    st.session_state.pop("campaign_daily_snapshot_rows", None)
    st.session_state.pop("campaign_daily_hygiene", None)
    st.session_state.pop("agent_pipeline_status", None)
    st.session_state.pop("hourly_rows_by_label", None)
    st.session_state.pop("google_ads_fetch_records", None)
    st.session_state.pop("pipeline_step_errors", None)
    st.session_state.pop("pipeline_selected_step", None)


def _clear_hourly_extract_session() -> None:
    st.session_state.pop("hourly_extract_label", None)
    st.session_state.pop("hourly_metrics_cache_key", None)
    st.session_state.pop("hourly_metrics_store", None)


def _analyzer_result_is_current(result: AnalyzerResult | None) -> bool:
    if result is None:
        return False
    for field in result.fields:
        if not hasattr(field, "mtd_achieve") or not hasattr(field, "mtd_target"):
            return False
        if not hasattr(field, "t1_date"):
            return False
        if not hasattr(field, "today_cost"):
            return False
        if field.cost > 0 and getattr(field, "mtd_achieve_end", None) is None:
            if achieve_end_date(field.start_date, field.end_date) is not None:
                return False
    return True


def _render_sample_data(settings) -> None:
    campaigns = CampaignDataService(settings).load_campaigns()
    analytics = SpendAnalyticsService(settings)

    stakeholders = sorted({c.stakeholder for c in campaigns})
    selected = st.selectbox("Filter by stakeholder", ["All"] + stakeholders, key="stakeholder_filter")

    filtered = campaigns if selected == "All" else [c for c in campaigns if c.stakeholder == selected]

    rows = []
    for campaign in filtered:
        risk = campaign.risk_level(settings.warning_threshold_pct, settings.critical_threshold_pct)
        rows.append(
            {
                "Campaign": campaign.campaign_name,
                "Stakeholder": campaign.stakeholder,
                "Budget": campaign.monthly_budget,
                "Spend MTD": campaign.spend_mtd,
                "Yesterday": campaign.spend_yesterday,
                "Utilization": campaign.utilization_pct,
                "Projected EOM": campaign.projected_month_end_spend,
                "Remaining": campaign.remaining_budget,
                "Status": risk_label(risk.value),
            }
        )
    df = pd.DataFrame(rows)

    st.dataframe(
        df.style.format(
            {
                "Budget": lambda v: format_currency(v, settings.app_currency),
                "Spend MTD": lambda v: format_currency(v, settings.app_currency),
                "Yesterday": lambda v: format_currency(v, settings.app_currency),
                "Projected EOM": lambda v: format_currency(v, settings.app_currency),
                "Remaining": lambda v: format_currency(v, settings.app_currency),
                "Utilization": "{:.1f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    chart_col, risk_col = st.columns(2)
    with chart_col:
        st.markdown("##### Spend by Stakeholder")
        stakeholder_totals = analytics.spend_by_stakeholder(filtered if selected != "All" else campaigns)
        chart_df = pd.DataFrame(
            [{"Stakeholder": k, "Spend (MTD)": v} for k, v in stakeholder_totals.items()]
        )
        fig = px.pie(
            chart_df,
            names="Stakeholder",
            values="Spend (MTD)",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig.update_layout(template="plotly_dark", height=340, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with risk_col:
        st.markdown("##### Top Overspend Risk")
        top_risk = analytics.top_overspend_campaigns(campaigns)
        if top_risk:
            for campaign, amount in top_risk:
                st.warning(
                    f"**{campaign.campaign_name}** ({campaign.stakeholder}) — "
                    f"potential overspend: {format_currency(amount, settings.app_currency)}"
                )
        else:
            st.success("No overspend risk detected across campaigns.")


def _render_field_results_table(result: AnalyzerResult, currency: str, settings: AppSettings) -> None:
    render_pipeline_anchor("fetch")
    st.markdown("##### Analyzer results")
    st.caption(
        "MTD target = day-wise budget (budget ÷ days in range) summed through the MTD achieve window. "
        "MTD achieve = Google Ads spend for the same window (T-1 from today when end date is today or later)."
    )

    rows = []
    for field in result.fields:
        rows.append(
            {
                "Campaign type": field.label,
                "Budget": field.budget,
                "Start date": field.start_date,
                "End date": field.end_date,
                "Cost": field.cost,
                "MTD target": field.mtd_target,
                "MTD achieve": field.mtd_achieve,
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.format(
            {
                "Budget": lambda v: format_currency(v, currency) if v else "—",
                "Cost": lambda v: format_currency(v, currency),
                "MTD target": lambda v: format_currency(v, currency),
                "MTD achieve": lambda v: format_currency(v, currency),
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    total_cost = sum(field.cost for field in result.fields)
    total_budget = sum(field.budget for field in result.fields)
    cols = st.columns(3)
    with cols[0]:
        st.metric("Total budget (entered)", format_currency(total_budget, currency))
    with cols[1]:
        st.metric("Total cost (your date ranges)", format_currency(total_cost, currency))
    with cols[2]:
        used = (total_cost / total_budget * 100) if total_budget else 0
        st.metric("Budget used", f"{used:.1f}%")

    agent_report = st.session_state.get("agent_report")
    if agent_report:
        render_pipeline_anchor("account")
        st.markdown("---")
        render_pipeline_report(agent_report, table_filter="Analyzer results")

    st.markdown("---")
    _render_daily_snapshot_table(result, currency, settings)


def _hourly_cost_formatters(currency: str, t1_label: str, t2_label: str) -> dict:
    return {
        t1_label: lambda v: format_currency(v, currency),
        t2_label: lambda v: format_currency(v, currency),
        "Today's cost": lambda v: format_currency(v, currency),
        "T-1 7-day avg cost": lambda v: format_currency(v, currency),
    }


def _render_hourly_extract_table(
    result: AnalyzerResult,
    extract_label: str,
    currency: str,
    settings: AppSettings,
    t1_label: str,
    t2_label: str,
) -> None:
    field = next((item for item in result.fields if item.label == extract_label), None)
    if field is None or not field.t1_date or not field.t2_date:
        return

    today_date = field.today_date or date.today()
    avg_window_start, avg_window_end = t1_seven_day_window()
    cache_key = f"{result.account}_{avg_window_start}_{today_date}"
    cached_by_label = st.session_state.get("hourly_rows_by_label") or {}
    hourly_rows = cached_by_label.get(extract_label)

    if hourly_rows is None:
        if st.session_state.get("hourly_metrics_cache_key") != cache_key:
            with st.spinner(f"Fetching hourly Google Ads data for {extract_label}..."):
                store = GoogleAdsFetchService(settings).fetch_hourly_metrics(
                    result.account, avg_window_start, today_date
                )
                st.session_state["hourly_metrics_store"] = store
                st.session_state["hourly_metrics_cache_key"] = cache_key

        store = st.session_state.get("hourly_metrics_store")
        if not isinstance(store, HourlyMetricsStore):
            return

        hourly_rows = build_hourly_snapshot_rows(
            store,
            extract_label,
            field.t1_date,
            field.t2_date,
            today_date,
            avg_window_start,
            avg_window_end,
        )
    st.markdown(f"###### Hourly breakdown — {extract_label}")
    st.caption("Rows are hours 0–23 (hour 0 = 12:00 AM–12:59 AM).")
    hourly_df = pd.DataFrame(hourly_rows)
    st.dataframe(
        hourly_df.style.format(_hourly_cost_formatters(currency, t1_label, t2_label)),
        use_container_width=True,
        hide_index=True,
    )
    st.session_state["hourly_rows_for_chat"] = hourly_rows

    agent_report = st.session_state.get("agent_report")
    hourly_report = agent_report.hourly if agent_report and agent_report.hourly else None
    if hourly_report and hourly_report.campaign_type == extract_label:
        st.session_state["hourly_agent_report"] = hourly_report
    elif settings.openrouter_configured:
        with st.spinner(f"Running hourly AI agent for {extract_label}..."):
            hourly_report = run_hourly_agent(extract_label, hourly_rows, settings)
            sent, log = run_email_agent(hourly_report, settings)
            hourly_report = hourly_report.model_copy(update={"email_sent": sent, "email_log": log})
            st.session_state["hourly_agent_report"] = hourly_report

            if agent_report is not None:
                agent_report = agent_report.model_copy(
                    update={
                        "hourly": hourly_report,
                        "email_sent": agent_report.email_sent or sent,
                        "email_log": [*agent_report.email_log, *log],
                    }
                )
                st.session_state["agent_report"] = agent_report
            if sent:
                st.success(f"Hourly breakdown alert email sent for {extract_label}.")


def _render_daily_snapshot_table(result: AnalyzerResult, currency: str, settings: AppSettings) -> None:
    if not result.fields:
        return

    sample = result.fields[0]
    t1_label = sample.t1_date.isoformat() if sample.t1_date else "T-1"
    t2_label = sample.t2_date.isoformat() if sample.t2_date else "T-2"

    st.markdown("##### Daily spend snapshot")
    render_pipeline_anchor("daily")
    st.caption(
        f"T-1 = {t1_label}, T-2 = {t2_label}. "
        f"7-day average = mean daily cost from {t1_label} minus 6 days through {t1_label}."
    )

    rows = []
    for field in result.fields:
        rows.append(
            {
                "Campaign type": field.label,
                t1_label: field.t1_cost,
                t2_label: field.t2_cost,
                "Today's cost": field.today_cost,
                "T-1 7-day avg cost": field.t1_7day_avg_cost,
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.format(_hourly_cost_formatters(currency, t1_label, t2_label)),
        use_container_width=True,
        hide_index=True,
    )

    agent_report = st.session_state.get("agent_report")
    if agent_report:
        st.markdown("---")
        render_pipeline_report(agent_report, table_filter="Daily spend snapshot")

    campaign_rows = st.session_state.get("campaign_daily_snapshot_rows") or []
    render_campaign_daily_snapshot_table(
        campaign_rows,
        currency,
        agent_report,
    )

    st.markdown("**Extract hourly breakdown**")
    render_pipeline_anchor("hourly")
    btn_cols = st.columns(len(result.fields))
    for idx, field in enumerate(result.fields):
        with btn_cols[idx]:
            st.caption(field.label.replace(" campaigns", ""))
            if st.button("Extract", key=f"hourly_extract_{idx}", use_container_width=True):
                st.session_state["hourly_extract_label"] = field.label

    extract_label = st.session_state.get("hourly_extract_label")
    if extract_label and settings.google_ads_configured:
        st.markdown("---")
        _render_hourly_extract_table(result, extract_label, currency, settings, t1_label, t2_label)
        hourly_rows = st.session_state.get("hourly_rows_for_chat")
        hourly_report = st.session_state.get("hourly_agent_report")
        if hourly_report:
            st.markdown("---")
            render_table_agent_report(hourly_report)


def main() -> None:
    settings = init_page()
    inject_app_styles()

    st.title("Campaign Analysis")
    st.caption("Fill the form → Run Analyzer → view cost for each field's start/end dates.")

    tab_analyzer, tab_chat, tab_sample = st.tabs(["Google Ads Analyzer", "AI Chat", "Sample Data"])

    with tab_analyzer:
        render_google_ads_credentials_info(settings)

        if st.session_state.get("analyzer_logic_version") != ANALYZER_LOGIC_VERSION:
            _clear_analyzer_session()
            st.session_state["analyzer_logic_version"] = ANALYZER_LOGIC_VERSION

        cached = st.session_state.get("analyzer_result")
        if cached is not None and not _analyzer_result_is_current(cached):
            _clear_analyzer_session()

        form_request = render_analyzer_form(settings)

        pipeline_slot = st.empty()

        if form_request is not None:
            if not settings.google_ads_configured:
                st.error("Configure Google Ads credentials in `.env` first.")
            else:
                try:
                    step_status = initial_step_status()
                    render_agent_pipeline(
                        step_status,
                        placeholder=pipeline_slot,
                        title="AI Agent Pipeline",
                        interactive=False,
                    )

                    step_status["fetch"] = PipelineStepStatus.RUNNING.value
                    render_agent_pipeline(
                        step_status,
                        placeholder=pipeline_slot,
                        title="AI Agent Pipeline",
                        interactive=False,
                    )

                    fetch_service = GoogleAdsFetchService(settings)
                    try:
                        fetch_bundle = fetch_service.build_analyzer_input_from_form(form_request)
                        form_input = fetch_bundle.form_input
                        st.session_state["google_ads_fetch_records"] = fetch_bundle.raw_records
                        pipeline_errors = st.session_state.get("pipeline_step_errors") or {}
                        pipeline_errors.pop("fetch", None)
                        st.session_state["pipeline_step_errors"] = pipeline_errors

                        result = CampaignAnalyzerService().analyze(form_input)
                        customer_id = fetch_service.resolve_customer_id(form_request.account)
                        campaign_bundle = CampaignDailySnapshotService(settings).fetch_snapshot(customer_id)
                        campaign_rows = campaign_bundle.rows
                        campaign_hygiene = campaign_bundle.hygiene

                        step_status["fetch"] = PipelineStepStatus.COMPLETE.value
                    except Exception as fetch_exc:
                        step_status["fetch"] = PipelineStepStatus.ERROR.value
                        st.session_state["google_ads_fetch_records"] = []
                        pipeline_errors = st.session_state.get("pipeline_step_errors") or {}
                        pipeline_errors["fetch"] = str(fetch_exc)
                        st.session_state["pipeline_step_errors"] = pipeline_errors
                        st.session_state["agent_pipeline_status"] = step_status
                        render_agent_pipeline(
                            step_status,
                            placeholder=pipeline_slot,
                            title="AI Agent Pipeline",
                            interactive=False,
                        )
                        st.error(f"Google Ads fetch failed: {fetch_exc}")
                        raise

                    render_agent_pipeline(
                        step_status,
                        placeholder=pipeline_slot,
                        title="AI Agent Pipeline",
                        interactive=False,
                    )

                    st.session_state["campaign_daily_snapshot_rows"] = campaign_rows
                    st.session_state["campaign_daily_hygiene"] = campaign_hygiene
                    st.session_state["analyzer_result"] = result

                    if settings.openrouter_configured:
                        agent_report, step_status, hourly_by_label = run_sequential_agent_pipeline(
                            result,
                            settings,
                            campaign_rows,
                            fetch_service,
                            customer_id,
                            campaign_hygiene=campaign_hygiene,
                            step_status=step_status,
                            ui_placeholder=pipeline_slot,
                        )
                        st.session_state["agent_pipeline_status"] = step_status
                        if hourly_by_label:
                            st.session_state["hourly_rows_by_label"] = hourly_by_label
                        agent_report = run_pipeline_email_alerts(agent_report, settings)
                        st.session_state["agent_report"] = agent_report
                    else:
                        st.session_state["agent_pipeline_status"] = step_status
                        st.session_state.pop("agent_report", None)

                    st.session_state["analyzer_fetched"] = True
                    st.session_state["analyzer_logic_version"] = ANALYZER_LOGIC_VERSION
                    _clear_hourly_extract_session()
                    st.session_state["last_form_key"] = (
                        form_request.account,
                        str(form_request.search_campaigns.start_date),
                        str(form_request.search_campaigns.end_date),
                        form_request.search_campaigns.budget,
                    )
                    st.success("Analyzer complete — tables and AI agent reports loaded.")
                except (ValueError, ImportError) as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Analyzer failed: {exc}")

        if st.session_state.get("analyzer_fetched") and _analyzer_result_is_current(
            st.session_state.get("analyzer_result")
        ):
            pipeline_status = st.session_state.get("agent_pipeline_status")
            if pipeline_status:
                with pipeline_slot.container():
                    render_pipeline_tabs(pipeline_status, settings)
                st.markdown("---")
        elif form_request is None:
            if st.session_state.get("analyzer_result") is not None:
                st.info("Results were refreshed. Click **Run Analyzer** again to load MTD achieve.")
            else:
                st.info("Fill the form and click **Run Analyzer**.")

    with tab_chat:
        render_chat_panel(settings)

    with tab_sample:
        st.markdown("Pre-loaded demo campaigns for dashboard preview.")
        _render_sample_data(settings)


if __name__ == "__main__":
    main()
