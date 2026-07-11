"""Campaign table with risk status."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import AppSettings
from models.campaign import CampaignSpend
from utils.formatting import format_currency, risk_label


def render_campaign_table(
    campaigns: list[CampaignSpend], settings: AppSettings
) -> pd.DataFrame:
    rows = []
    for campaign in campaigns:
        risk = campaign.risk_level(settings.warning_threshold_pct, settings.critical_threshold_pct)
        rows.append(
            {
                "Campaign": campaign.campaign_name,
                "Platform": campaign.platform,
                "Stakeholder": campaign.stakeholder,
                "Budget": campaign.monthly_budget,
                "Spend (MTD)": campaign.spend_mtd,
                "Utilization %": campaign.utilization_pct,
                "Projected EOM": campaign.projected_month_end_spend,
                "Conversions": campaign.conversions,
                "Status": risk_label(risk.value),
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.format(
            {
                "Budget": lambda v: format_currency(v, settings.app_currency),
                "Spend (MTD)": lambda v: format_currency(v, settings.app_currency),
                "Projected EOM": lambda v: format_currency(v, settings.app_currency),
                "Utilization %": "{:.1f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    return df
