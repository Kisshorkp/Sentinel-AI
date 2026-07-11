"""Spend vs budget chart."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from models.campaign import CampaignSpend


def render_spend_budget_chart(campaigns: list[CampaignSpend], currency: str) -> None:
    rows = [
        {
            "Campaign": c.campaign_name,
            "Spend (MTD)": c.spend_mtd,
            "Monthly Budget": c.monthly_budget,
            "Utilization %": c.utilization_pct,
        }
        for c in sorted(campaigns, key=lambda item: item.utilization_pct, reverse=True)
    ]
    df = pd.DataFrame(rows)

    fig = px.bar(
        df,
        x="Campaign",
        y=["Spend (MTD)", "Monthly Budget"],
        barmode="group",
        title="Campaign Spend vs Monthly Budget",
        labels={"value": f"Amount ({currency})", "variable": "Metric"},
        color_discrete_sequence=["#2563EB", "#64748B"],
    )
    fig.update_layout(
        template="plotly_dark",
        height=420,
        xaxis_tickangle=-35,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)
