"""Sentinel AI — Dashboard (Step 1)."""

from __future__ import annotations

import streamlit as st

from components.alert_panel import render_alert_panel
from components.budget_gauge import render_utilization_gauge
from components.campaign_table import render_campaign_table
from components.metrics_row import render_metrics_row
from components.spend_chart import render_spend_budget_chart
from services.alert_service import AlertService
from services.campaign_data_service import CampaignDataService
from services.spend_analytics_service import SpendAnalyticsService
from utils.formatting import format_currency
from utils.streamlit_helpers import init_app


def main() -> None:
    settings = init_app()

    st.title("Sentinel AI Dashboard")
    st.markdown(
        "Monitor Google Ads campaign spend against permissible limits, "
        "detect overspend early, and quantify business impact for stakeholders."
    )

    try:
        campaigns = CampaignDataService(settings).load_campaigns()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    analytics = SpendAnalyticsService(settings)
    alerts_svc = AlertService(settings)
    summary = analytics.summarize(campaigns)
    alerts = alerts_svc.generate_alerts(campaigns)

    render_metrics_row(summary, settings.app_currency)

    st.divider()
    col_left, col_right = st.columns([2, 1])
    with col_left:
        render_spend_budget_chart(campaigns, settings.app_currency)
    with col_right:
        render_utilization_gauge(
            summary.utilization_pct,
            settings.warning_threshold_pct,
            settings.critical_threshold_pct,
        )

    st.subheader("Real-time Stakeholder Alerts")
    render_alert_panel(alerts)

    st.subheader("Campaign Spend Analysis")
    render_campaign_table(campaigns, settings)

    st.subheader("Business Impact Summary")
    impact_cols = st.columns(3)
    with impact_cols[0]:
        st.metric(
            "Total Monthly Budget",
            format_currency(summary.total_budget, settings.app_currency),
        )
    with impact_cols[1]:
        st.metric(
            "Campaigns Over Budget",
            summary.campaigns_over_budget,
        )
    with impact_cols[2]:
        st.metric(
            "Avg Cost / Conversion",
            format_currency(summary.avg_cost_per_conversion, settings.app_currency),
        )

    st.info(
        "**Hackathon value:** This dashboard addresses the core problem — spend outside "
        "permissible limits causing NR loss — by providing real-time visibility, "
        "stakeholder-specific alerts, and quantified prevented-loss estimates."
    )


if __name__ == "__main__":
    main()
