"""Account-wise pipeline tab — MTD overview and per-campaign AI summaries."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.campaign_summary_tabs import render_campaign_summary_tabs
from models.agent_report import PipelineAgentReport
from models.analyzer_input import AnalyzerResult, CampaignFieldInput
from utils.formatting import format_currency, format_percent


def _mtd_variance_pct(field: CampaignFieldInput) -> float | None:
    if field.mtd_target <= 0:
        return None
    return round(((field.mtd_achieve - field.mtd_target) / field.mtd_target) * 100, 1)


def _build_spend_overview_rows(result: AnalyzerResult) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for field in result.fields:
        budget_used = field.budget_utilization_pct if field.budget > 0 else None
        mtd_var = _mtd_variance_pct(field)
        rows.append(
            {
                "Campaign type": field.label.replace(" campaigns", ""),
                "Budget": field.budget,
                "Spend (MTD)": field.cost,
                "MTD target": field.mtd_target,
                "MTD achieve": field.mtd_achieve,
                "Budget used": budget_used,
                "MTD vs target": mtd_var,
            }
        )
    return rows


def _render_summary_metrics(result: AnalyzerResult, currency: str) -> None:
    cols = st.columns(4)
    metrics = [
        ("Total budget", format_currency(result.total_budget, currency)),
        ("Total spend", format_currency(result.total_spend, currency)),
        ("Total MTD target", format_currency(sum(f.mtd_target for f in result.fields), currency)),
        ("Total MTD achieve", format_currency(sum(f.mtd_achieve for f in result.fields), currency)),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)


def _render_spend_overview_table(result: AnalyzerResult, currency: str) -> None:
    rows = _build_spend_overview_rows(result)
    if not rows:
        st.info("No account-wise spend data available.")
        return

    df = pd.DataFrame(rows)
    st.markdown("###### Spend overview by campaign type")
    st.caption("MTD target and achieve use the analyzer date window. Budget used = spend ÷ entered budget.")

    st.dataframe(
        df.style.format(
            {
                "Budget": lambda v: format_currency(v, currency),
                "Spend (MTD)": lambda v: format_currency(v, currency),
                "MTD target": lambda v: format_currency(v, currency),
                "MTD achieve": lambda v: format_currency(v, currency),
                "Budget used": lambda v: format_percent(v) if v is not None else "—",
                "MTD vs target": lambda v: f"{v:+.1f}%" if v is not None else "—",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_account_pipeline_tab(
    result: AnalyzerResult,
    settings,
    agent_report: PipelineAgentReport | None,
) -> None:
    """Render the Account-wise tab: metrics, table, then summary tabs."""
    currency = settings.app_currency
    st.caption("Account-level MTD spend and AI summaries by campaign type.")

    _render_summary_metrics(result, currency)
    st.markdown("")
    _render_spend_overview_table(result, currency)
    st.markdown("---")
    reports = agent_report.analyzer_table if agent_report else []
    render_campaign_summary_tabs(reports)
