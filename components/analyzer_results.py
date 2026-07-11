"""Display analyzer results — one table per field date range only."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from models.analyzer_input import AnalyzerResult
from utils.formatting import format_currency


def render_daily_snapshot_table(result: AnalyzerResult, currency: str) -> None:
    if not result.fields:
        return

    sample = result.fields[0]
    t1_label = sample.t1_date.isoformat() if sample.t1_date else "T-1"
    t2_label = sample.t2_date.isoformat() if sample.t2_date else "T-2"

    st.markdown("##### Daily spend snapshot")
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


def render_field_results_table(result: AnalyzerResult, currency: str) -> None:
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

    st.markdown("---")
    render_daily_snapshot_table(result, currency)


# Backward-compatible alias
render_analyzer_results = render_field_results_table
