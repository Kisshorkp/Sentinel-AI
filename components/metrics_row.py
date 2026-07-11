"""KPI metric cards row."""

from __future__ import annotations

import streamlit as st

from models.campaign import DashboardSummary
from utils.formatting import format_currency, format_percent


def render_metrics_row(summary: DashboardSummary, currency: str) -> None:
    cols = st.columns(5)
    metrics: list[tuple[str, str, str | None]] = [
        ("Total Spend (MTD)", format_currency(summary.total_spend_mtd, currency), None),
        ("Budget Utilization", format_percent(summary.utilization_pct), None),
        ("Campaigns at Risk", str(summary.campaigns_at_risk), "inverse"),
        ("Projected Overspend", format_currency(summary.projected_overspend, currency), "inverse"),
        ("NR Loss Prevented*", format_currency(summary.prevented_loss_estimate, currency), "normal"),
    ]
    for col, (label, value, delta_color) in zip(cols, metrics):
        with col:
            if delta_color:
                st.metric(label=label, value=value, delta_color=delta_color)
            else:
                st.metric(label=label, value=value)
    st.caption(
        "*Estimated net revenue protected through early detection and stakeholder alerts."
    )
