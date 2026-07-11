"""Hourly pipeline tab — current-hour overview and per-campaign hourly tables + summaries."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from agents.hourly_agent import current_display_hour
from components.campaign_summary_tabs import campaign_tab_label, render_campaign_summary
from models.agent_report import PipelineAgentReport, TableAgentReport
from utils.formatting import format_currency


def _hour_row(hourly_rows: list[dict[str, object]], hour: int) -> dict[str, object] | None:
    for row in hourly_rows:
        if int(row.get("Hour", 0)) == hour:
            return row
    return None


def _sorted_hourly_rows(hourly_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(hourly_rows, key=lambda row: int(row.get("Hour", 0)))


def _build_hourly_overview_rows(
    hourly_by_label: dict[str, list[dict[str, object]]],
) -> tuple[list[dict[str, object]], int]:
    display_hour = current_display_hour()
    rows: list[dict[str, object]] = []
    for label, hourly_rows in hourly_by_label.items():
        row = _hour_row(hourly_rows, display_hour)
        today_cost = float(row.get("Today's cost", 0) or 0) if row else 0.0
        avg_cost = float(row.get("T-1 7-day avg cost", 0) or 0) if row else 0.0
        pct_vs_avg = ((today_cost - avg_cost) / avg_cost * 100) if avg_cost > 0 else None
        rows.append(
            {
                "Campaign type": label.replace(" campaigns", ""),
                "Current hour": display_hour,
                "Today's cost": today_cost,
                "T-1 7-day avg cost": avg_cost,
                "Vs 7-day avg": pct_vs_avg,
            }
        )
    return rows, display_hour


def _cost_columns(hourly_rows: list[dict[str, object]]) -> tuple[str, ...]:
    if not hourly_rows:
        return ()
    return tuple(column for column in hourly_rows[0].keys() if column != "Hour")


def _hourly_display_columns(columns: list[str]) -> list[str]:
    """Hour, then T-2 date, then T-1 date, then remaining columns."""
    if len(columns) >= 3 and columns[0] == "Hour":
        return [columns[0], columns[2], columns[1], *columns[3:]]
    return columns


def _normalize_hourly_rows(hourly_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Apply display column order even for cached session rows."""
    normalized: list[dict[str, object]] = []
    for row in _sorted_hourly_rows(hourly_rows):
        order = _hourly_display_columns(list(row.keys()))
        normalized.append({key: row[key] for key in order})
    return normalized


def _render_hourly_breakdown_table(hourly_rows: list[dict[str, object]], currency: str) -> None:
    rows = _normalize_hourly_rows(hourly_rows)
    if not rows:
        st.info("No hourly breakdown available for this campaign type.")
        return

    st.markdown("##### Hourly breakdown (hours 0–23)")
    st.caption("Hour 0 = 12:00 AM–12:59 AM · Hour 23 = 11:00 PM–11:59 PM")

    df = pd.DataFrame(rows)
    cost_columns = _cost_columns(rows)
    st.dataframe(
        df.style.format({column: (lambda v, c=currency: format_currency(v, c)) for column in cost_columns}),
        use_container_width=True,
        hide_index=True,
        height=560,
    )


def _hourly_reports(agent_report: PipelineAgentReport | None) -> list[TableAgentReport]:
    if agent_report is None:
        return []
    if agent_report.hourly_snapshot:
        return agent_report.hourly_snapshot
    if agent_report.hourly:
        return [agent_report.hourly]
    return []


def _render_hourly_campaign_panels(
    hourly_by_label: dict[str, list[dict[str, object]]],
    currency: str,
    agent_report: PipelineAgentReport | None,
) -> None:
    """Campaign picker + table + summary (segmented control avoids nested-tab rendering issues)."""
    reports = _hourly_reports(agent_report)
    report_by_label = {report.campaign_type: report for report in reports if report.campaign_type}
    labels = list(hourly_by_label.keys())
    display_labels = [
        campaign_tab_label(report_by_label[label]) if label in report_by_label else label.replace(" campaigns", "")
        for label in labels
    ]
    label_by_display = dict(zip(display_labels, labels))

    st.markdown("###### Hourly breakdown by campaign type")
    selected_display = st.segmented_control(
        "Campaign type",
        options=display_labels,
        default=display_labels[0],
        key="hourly_campaign_picker",
    )
    if not selected_display:
        return

    selected_label = label_by_display[selected_display]
    with st.container(border=True):
        st.markdown(f"**{selected_display}** — full day hourly spend")
        _render_hourly_breakdown_table(hourly_by_label[selected_label], currency)

        report = report_by_label.get(selected_label)
        if report:
            st.markdown("---")
            st.markdown("##### AI summary")
            render_campaign_summary(report)
        elif not reports:
            st.info("AI summaries will appear here after OpenRouter is configured.")


def _render_summary_metrics(
    hourly_by_label: dict[str, list[dict[str, object]]],
    currency: str,
    display_hour: int,
) -> None:
    overview_rows, _ = _build_hourly_overview_rows(hourly_by_label)
    total_today = sum(float(row["Today's cost"]) for row in overview_rows)
    total_avg = sum(float(row["T-1 7-day avg cost"]) for row in overview_rows)
    total_pct = ((total_today - total_avg) / total_avg * 100) if total_avg > 0 else None

    cols = st.columns(4)
    metrics = [
        ("Current hour (0–23)", str(display_hour)),
        ("Total current-hour spend", format_currency(total_today, currency)),
        ("Total same-hour 7-day avg", format_currency(total_avg, currency)),
        ("Vs 7-day avg", f"{total_pct:+.1f}%" if total_pct is not None else "—"),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)


def _render_hourly_overview_table(
    hourly_by_label: dict[str, list[dict[str, object]]],
    currency: str,
    display_hour: int,
) -> None:
    rows, _ = _build_hourly_overview_rows(hourly_by_label)
    if not rows:
        st.info("No hourly spend data available.")
        return

    st.markdown("###### Hourly spend overview by campaign type")
    st.caption(
        f"Current hour = {display_hour} (0–23 clock). "
        "Values show spend for the current clock hour vs the 7-day same-hour average."
    )

    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.format(
            {
                "Today's cost": lambda v: format_currency(v, currency),
                "T-1 7-day avg cost": lambda v: format_currency(v, currency),
                "Vs 7-day avg": lambda v: f"{v:+.1f}%" if v is not None else "—",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_hourly_pipeline_tab(
    hourly_by_label: dict[str, list[dict[str, object]]],
    settings,
    agent_report: PipelineAgentReport | None,
) -> None:
    """Render the Hourly tab: overview metrics/table, then per-campaign tables + summaries."""
    if not hourly_by_label:
        st.info("Hourly data is not loaded yet.")
        return

    currency = settings.app_currency
    _, display_hour = _build_hourly_overview_rows(hourly_by_label)

    st.caption("Current-hour overview plus full 0–23 hourly tables and AI summaries by campaign type.")
    _render_summary_metrics(hourly_by_label, currency, display_hour)
    st.markdown("")
    _render_hourly_overview_table(hourly_by_label, currency, display_hour)
    st.markdown("---")
    _render_hourly_campaign_panels(hourly_by_label, currency, agent_report)
