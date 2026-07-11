"""Manual campaign analyzer input form."""

from __future__ import annotations

from datetime import date

import streamlit as st

from config.settings import AppSettings
from models.analyzer_input import AnalyzerFormRequest, CampaignFieldFormInput, resolve_fetch_end_date
from utils.ui_styles import inject_app_styles, render_analyzer_hero, render_row_label, render_section_chip


CAMPAIGN_FIELDS: list[tuple[str, str]] = [
    ("Search campaigns", "🔍"),
    ("Video campaigns", "📺"),
    ("Demand Gen campaigns", "📣"),
    ("Performance Max campaigns", "🚀"),
]


def _default_dates() -> tuple[date, date]:
    today = date.today()
    month_start = today.replace(day=1)
    return month_start, today


def _field_form(label: str, data: tuple[float, date, date]) -> CampaignFieldFormInput:
    return CampaignFieldFormInput(
        label=label,
        budget=data[0],
        start_date=data[1],
        end_date=data[2],
    )


def render_analyzer_form(settings: AppSettings) -> AnalyzerFormRequest | None:
    inject_app_styles()
    render_analyzer_hero()
    month_start, today = _default_dates()

    with st.form("campaign_analyzer_form", clear_on_submit=False):
        render_section_chip("Account setup")
        acc_col, acc_start_col, acc_end_col = st.columns([2.0, 1.0, 1.0])
        with acc_col:
            default_account = settings.google_ads_customer_id or ""
            account = st.text_input(
                "Account / Customer ID",
                value=default_account,
                placeholder="e.g. 465-793-6931",
            )
        with acc_start_col:
            account_start = st.date_input("Account start", value=month_start, key="acc_start")
        with acc_end_col:
            account_end = st.date_input("Account end", value=today, key="acc_end")

        st.markdown(
            """
            **How it works**
            1. Enter values and dates for each field below  
            2. Click **Run Analyzer**  
            3. App finds the **latest end date** from your form  
            4. Fetches Google Ads data for the **last 90 days** ending on that date
            """
        )

        st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
        render_section_chip("Enter campaign budgets & dates")
        header_cols = st.columns([2.0, 1.2, 1.0, 1.0])
        headers = ["Campaign type", "Budget / limit (editable)", "Start date", "End date"]
        for col, header in zip(header_cols, headers):
            with col:
                st.markdown(f'<div class="grid-header">{header}</div>', unsafe_allow_html=True)

        field_inputs: dict[str, tuple[float, date, date]] = {}
        for label, icon in CAMPAIGN_FIELDS:
            col_label, col_budget, col_start, col_end = st.columns([2.0, 1.2, 1.0, 1.0])
            with col_label:
                render_row_label(icon, label)
            with col_budget:
                budget = st.number_input(
                    f"{label} budget",
                    min_value=0.0,
                    value=0.0,
                    step=1000.0,
                    format="%.2f",
                    key=f"budget_{label}",
                    label_visibility="collapsed",
                )
            with col_start:
                start = st.date_input(
                    f"{label} start",
                    value=month_start,
                    key=f"start_{label}",
                    label_visibility="collapsed",
                )
            with col_end:
                end = st.date_input(
                    f"{label} end",
                    value=today,
                    key=f"end_{label}",
                    label_visibility="collapsed",
                )
            field_inputs[label] = (budget, start, end)

        submitted = st.form_submit_button("Run Analyzer", type="primary", use_container_width=True)

    if not submitted:
        return None

    if not account.strip():
        st.error("Please enter an Account / Customer ID.")
        return None

    try:
        return AnalyzerFormRequest(
            account=account.strip(),
            account_start_date=account_start,
            account_end_date=account_end,
            search_campaigns=_field_form("Search campaigns", field_inputs["Search campaigns"]),
            video_campaigns=_field_form("Video campaigns", field_inputs["Video campaigns"]),
            demand_gen_campaigns=_field_form("Demand Gen campaigns", field_inputs["Demand Gen campaigns"]),
            performance_max_campaigns=_field_form(
                "Performance Max campaigns",
                field_inputs["Performance Max campaigns"],
            ),
        )
    except ValueError as exc:
        st.error(str(exc))
        return None
