"""Alert panel for stakeholder notifications."""

from __future__ import annotations

import streamlit as st

from models.campaign import RiskLevel, SpendAlert


def render_alert_panel(alerts: list[SpendAlert]) -> None:
    if not alerts:
        st.success("All campaigns are within permissible spend limits.")
        return

    for alert in alerts:
        if alert.risk_level == RiskLevel.OVER_BUDGET:
            st.error(f"**{alert.campaign_name}** — {alert.message}")
        elif alert.risk_level == RiskLevel.CRITICAL:
            st.warning(f"**{alert.campaign_name}** — {alert.message}")
        else:
            st.info(f"**{alert.campaign_name}** — {alert.message}")
