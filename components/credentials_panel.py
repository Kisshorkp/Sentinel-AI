"""Google Ads credentials status panel."""

from __future__ import annotations

import streamlit as st

from config.settings import AppSettings
from utils.masking import mask_secret


def render_google_ads_credentials_info(settings: AppSettings) -> None:
    missing = settings.google_ads_missing_credentials()
    configured = settings.google_ads_configured

    with st.expander("Google Ads API credentials (add to .env)", expanded=not configured):
        st.markdown(
            """
            **Required credentials** to fetch **Cost**, **Converted Cost**, **Conversions**,
            and **Conversion Value** from Google Ads:

            | Variable | Where to get it |
            |----------|-----------------|
            | `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads → Tools → **API Center** |
            | `GOOGLE_ADS_CLIENT_ID` | Google Cloud Console → **OAuth 2.0 Client ID** |
            | `GOOGLE_ADS_CLIENT_SECRET` | Same OAuth client in Google Cloud Console |
            | `GOOGLE_ADS_REFRESH_TOKEN` | OAuth flow with scope `https://www.googleapis.com/auth/adwords` |
            | `GOOGLE_ADS_CUSTOMER_ID` | Google Ads account ID (10 digits, dashes optional) |
            | `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | Manager (MCC) ID — only if using a manager account |
            """
        )

        if configured:
            st.success("OAuth credentials are set in `.env`.")
            cols = st.columns(2)
            with cols[0]:
                st.text(f"Developer token: {mask_secret(settings.google_ads_developer_token)}")
                st.text(f"Client ID: {mask_secret(settings.google_ads_client_id)}")
            with cols[1]:
                st.text(f"Refresh token: {mask_secret(settings.google_ads_refresh_token)}")
                default_customer = settings.google_ads_customer_id or "Not set (use form field)"
                st.text(f"Customer ID: {default_customer}")
        else:
            st.warning("Missing in `.env`: " + ", ".join(missing))

        st.caption(
            f"Run Analyzer fetches the last {settings.google_ads_lookback_days} days ending on your selected date. "
            "If using an MCC/manager account, set `GOOGLE_ADS_LOGIN_CUSTOMER_ID` to the manager ID."
        )
