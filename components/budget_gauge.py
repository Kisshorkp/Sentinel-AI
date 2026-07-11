"""Utilization gauge chart."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def render_utilization_gauge(utilization_pct: float, warning_pct: float, critical_pct: float) -> None:
    color = "#22C55E"
    if utilization_pct >= critical_pct:
        color = "#EF4444"
    elif utilization_pct >= warning_pct:
        color = "#F59E0B"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=utilization_pct,
            number={"suffix": "%"},
            title={"text": "Portfolio Budget Utilization"},
            gauge={
                "axis": {"range": [0, 120]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, warning_pct], "color": "#14532D"},
                    {"range": [warning_pct, critical_pct], "color": "#78350F"},
                    {"range": [critical_pct, 120], "color": "#7F1D1D"},
                ],
                "threshold": {
                    "line": {"color": "#F8FAFC", "width": 3},
                    "thickness": 0.8,
                    "value": critical_pct,
                },
            },
        )
    )
    fig.update_layout(template="plotly_dark", height=320, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)
