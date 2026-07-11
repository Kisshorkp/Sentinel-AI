"""Daily-wise pipeline tab — daily snapshot table and per-campaign AI summaries."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.campaign_summary_tabs import render_campaign_summary_tabs
from models.agent_report import PipelineAgentReport
from models.analyzer_input import AnalyzerResult
from utils.formatting import format_currency


def _build_daily_snapshot_rows(result: AnalyzerResult) -> tuple[list[dict[str, object]], str, str]:
    sample = result.fields[0] if result.fields else None
    t1_label = sample.t1_date.isoformat() if sample and sample.t1_date else "T-1"
    t2_label = sample.t2_date.isoformat() if sample and sample.t2_date else "T-2"
    rows = [
        {
            "Campaign type": field.label.replace(" campaigns", ""),
            t1_label: field.t1_cost,
            t2_label: field.t2_cost,
            "Today's cost": field.today_cost,
            "T-1 7-day avg cost": field.t1_7day_avg_cost,
        }
        for field in result.fields
    ]
    return rows, t1_label, t2_label


def _render_summary_metrics(result: AnalyzerResult, currency: str, t1_label: str, t2_label: str) -> None:
    cols = st.columns(4)
    metrics = [
        (f"Total {t1_label}", format_currency(sum(f.t1_cost for f in result.fields), currency)),
        (f"Total {t2_label}", format_currency(sum(f.t2_cost for f in result.fields), currency)),
        ("Total today's cost", format_currency(sum(f.today_cost for f in result.fields), currency)),
        (
            "Total T-1 7-day avg",
            format_currency(sum(f.t1_7day_avg_cost for f in result.fields), currency),
        ),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)


def _render_daily_snapshot_table(result: AnalyzerResult, currency: str, t1_label: str, t2_label: str) -> None:
    rows, _, _ = _build_daily_snapshot_rows(result)
    if not rows:
        st.info("No daily spend data available.")
        return

    st.markdown("###### Daily spend snapshot by campaign type")
    st.caption(
        f"T-1 = {t1_label}, T-2 = {t2_label}. "
        f"7-day average = mean daily cost from {t1_label} minus 6 days through {t1_label}."
    )

    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.format(
            {
                t1_label: lambda v: format_currency(v, currency),
                t2_label: lambda v: format_currency(v, currency),
                "Today's cost": lambda v: format_currency(v, currency),
                "T-1 7-day avg cost": lambda v: format_currency(v, currency),
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_daily_pipeline_tab(
    result: AnalyzerResult,
    settings,
    agent_report: PipelineAgentReport | None,
) -> None:
    """Render the Daily-wise tab: metrics, table, then summary tabs."""
    currency = settings.app_currency
    _, t1_label, t2_label = _build_daily_snapshot_rows(result)

    st.caption("Daily spend snapshot and AI summaries by campaign type.")
    _render_summary_metrics(result, currency, t1_label, t2_label)
    st.markdown("")
    _render_daily_snapshot_table(result, currency, t1_label, t2_label)
    st.markdown("---")
    reports = agent_report.daily_snapshot if agent_report else []
    render_campaign_summary_tabs(reports)
