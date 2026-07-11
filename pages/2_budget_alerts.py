"""Budget alerts and threshold configuration page."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from components.alert_panel import render_alert_panel
from services.alert_service import AlertService
from services.campaign_data_service import CampaignDataService
from utils.formatting import format_currency
from utils.streamlit_helpers import init_page


def main() -> None:
    settings = init_page()

    st.title("Budget Alerts")
    st.markdown(
        "Review campaigns approaching or exceeding permissible spend limits. "
        "Alerts are grouped for stakeholder notification."
    )

    warning_pct = st.slider(
        "Warning threshold (% of budget)",
        min_value=50,
        max_value=95,
        value=int(settings.warning_threshold_pct),
        step=5,
    )
    critical_pct = st.slider(
        "Critical threshold (% of budget)",
        min_value=80,
        max_value=110,
        value=int(settings.critical_threshold_pct),
        step=5,
    )

    settings.warning_threshold_pct = float(warning_pct)
    settings.critical_threshold_pct = float(critical_pct)

    campaigns = CampaignDataService(settings).load_campaigns()
    alerts = AlertService(settings).generate_alerts(campaigns)

    st.subheader(f"Active Alerts ({len(alerts)})")
    render_alert_panel(alerts)

    if alerts:
        st.subheader("Stakeholder Notification Preview")
        for alert in alerts:
            with st.expander(f"Notify {alert.stakeholder} — {alert.campaign_name}"):
                st.markdown(
                    f"**Subject:** Spend Alert — {alert.campaign_name}\n\n"
                    f"**Message:** {alert.message}\n\n"
                    f"**Utilization:** {alert.utilization_pct:.1f}%\n\n"
                    f"**Overspend:** {format_currency(alert.overspend_amount, settings.app_currency)}"
                )


if __name__ == "__main__":
    main()
