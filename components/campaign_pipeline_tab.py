"""Campaign-wise pipeline tab — campaign tables and per-type AI summaries."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.campaign_summary_tabs import campaign_tab_label, render_campaign_summary
from models.agent_report import PipelineAgentReport
from models.campaign_daily_snapshot import CampaignDailySnapshotRow
from services.google_ads_fetch_service import ANALYZER_LABELS
from utils.formatting import format_currency


def _date_labels(rows: list[CampaignDailySnapshotRow]) -> tuple[str, str]:
    sample = rows[0]
    t1_label = sample.t1_date.isoformat() if sample.t1_date else "T-1"
    t2_label = sample.t2_date.isoformat() if sample.t2_date else "T-2"
    return t1_label, t2_label


def _type_campaign_table_rows(
    type_rows: list[CampaignDailySnapshotRow],
    t1_label: str,
    t2_label: str,
) -> list[dict[str, object]]:
    return [
        {
            "Campaign": row.campaign_name,
            "Campaign ID": row.campaign_id,
            t1_label: row.t1_cost,
            t2_label: row.t2_cost,
            "Today's cost": row.today_cost,
            "T-1 7-day avg cost": row.t1_7day_avg_cost,
        }
        for row in type_rows
    ]


def _render_summary_metrics(rows: list[CampaignDailySnapshotRow], currency: str) -> None:
    cols = st.columns(4)
    metrics = [
        ("Total campaigns", str(len(rows))),
        ("Campaign types", str(len({row.campaign_type for row in rows}))),
        ("Total today's cost", format_currency(sum(row.today_cost for row in rows), currency)),
        ("Total T-1 cost", format_currency(sum(row.t1_cost for row in rows), currency)),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)


def _render_type_campaign_table(
    type_rows: list[CampaignDailySnapshotRow],
    currency: str,
    t1_label: str,
    t2_label: str,
) -> None:
    if not type_rows:
        st.info("No campaigns available for this type.")
        return

    st.markdown("##### Campaign daily spend snapshot")
    st.caption(
        f"All campaigns in this type. T-1 = {t1_label}, T-2 = {t2_label}. "
        f"7-day average = mean daily cost from {t1_label} minus 6 days through {t1_label}."
    )

    df = pd.DataFrame(_type_campaign_table_rows(type_rows, t1_label, t2_label))
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


def _campaign_type_reports(agent_report: PipelineAgentReport | None) -> list:
    if agent_report is None:
        return []
    if agent_report.campaign_daily_by_type:
        return agent_report.campaign_daily_by_type
    if agent_report.campaign_daily_overall:
        return [agent_report.campaign_daily_overall]
    return []


def _render_campaign_type_panels(
    rows: list[CampaignDailySnapshotRow],
    currency: str,
    agent_report: PipelineAgentReport | None,
) -> None:
    t1_label, t2_label = _date_labels(rows)
    reports = _campaign_type_reports(agent_report)
    report_by_type = {report.campaign_type: report for report in reports if report.campaign_type}

    labels = [label for label in ANALYZER_LABELS if any(row.campaign_type == label for row in rows)]
    if not labels:
        st.info("No campaign types available.")
        return

    display_labels = [
        campaign_tab_label(report_by_type[label]) if label in report_by_type else label.replace(" campaigns", "")
        for label in labels
    ]
    label_by_display = dict(zip(display_labels, labels))

    st.markdown("###### Campaign data by type")
    selected_display = st.segmented_control(
        "Campaign type",
        options=display_labels,
        default=display_labels[0],
        key="campaign_type_picker",
    )
    if not selected_display:
        return

    selected_label = label_by_display[selected_display]
    type_rows = [row for row in rows if row.campaign_type == selected_label]

    with st.container(border=True):
        st.markdown(f"**{selected_display}** — all campaigns")
        _render_type_campaign_table(type_rows, currency, t1_label, t2_label)

        report = report_by_type.get(selected_label)
        if report and report.summary:
            st.markdown("---")
            st.markdown("##### AI summary (all campaigns in this type)")
            render_campaign_summary(report)
        elif not reports:
            st.info("AI summaries will appear here after OpenRouter is configured.")


def render_campaign_pipeline_tab(
    rows: list[CampaignDailySnapshotRow],
    settings,
    agent_report: PipelineAgentReport | None,
) -> None:
    """Render Campaign-wise tab: metrics, then per-type tables + one summary per type."""
    if not rows:
        st.info("No campaign-level records available.")
        return

    currency = settings.app_currency
    st.caption("Campaign-level daily spend with one AI summary per campaign type.")
    _render_summary_metrics(rows, currency)
    st.markdown("---")
    _render_campaign_type_panels(rows, currency, agent_report)
