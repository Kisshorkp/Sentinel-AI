"""Render campaign-level daily spend snapshot grouped by campaign type."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.agent_summary_panel import render_pipeline_report
from models.agent_report import PipelineAgentReport
from models.campaign_daily_snapshot import CampaignDailySnapshotRow
from services.google_ads_fetch_service import ANALYZER_LABELS
from utils.formatting import format_currency


def _cost_formatters(currency: str, t1_label: str, t2_label: str) -> dict:
    return {
        t1_label: lambda v: format_currency(v, currency),
        t2_label: lambda v: format_currency(v, currency),
        "Today's cost": lambda v: format_currency(v, currency),
        "T-1 7-day avg cost": lambda v: format_currency(v, currency),
    }


def render_campaign_daily_snapshot_table(
    rows: list[CampaignDailySnapshotRow],
    currency: str,
    agent_report: PipelineAgentReport | None = None,
) -> None:
    if not rows:
        st.info("No campaign-level daily data returned from Google Ads.")
        return

    sample = rows[0]
    t1_label = sample.t1_date.isoformat() if sample.t1_date else "T-1"
    t2_label = sample.t2_date.isoformat() if sample.t2_date else "T-2"

    st.markdown("##### Campaign daily spend snapshot")
    render_pipeline_anchor("campaign")
    st.caption(
        f"Individual campaigns grouped by type. T-1 = {t1_label}, T-2 = {t2_label}. "
        f"7-day average = mean daily cost from {t1_label} minus 6 days through {t1_label}."
    )

    for campaign_type in ANALYZER_LABELS:
        type_rows = [row for row in rows if row.campaign_type == campaign_type]
        if not type_rows:
            continue

        st.markdown(f"**{campaign_type}**")
        table_rows = [
            {
                "Campaign name": row.campaign_name,
                "Campaign ID": row.campaign_id,
                t1_label: row.t1_cost,
                t2_label: row.t2_cost,
                "Today's cost": row.today_cost,
                "T-1 7-day avg cost": row.t1_7day_avg_cost,
            }
            for row in type_rows
        ]
        df = pd.DataFrame(table_rows)
        st.dataframe(
            df.style.format(_cost_formatters(currency, t1_label, t2_label)),
            use_container_width=True,
            hide_index=True,
        )

    if agent_report and (
        agent_report.campaign_daily_snapshot or agent_report.campaign_daily_overall
    ):
        st.markdown("---")
        render_pipeline_report(agent_report, table_filter="Campaign daily spend snapshot")
