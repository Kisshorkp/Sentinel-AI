"""Shared per-campaign-type AI summary tabs for pipeline steps."""

from __future__ import annotations

import streamlit as st

from models.agent_report import Severity, TableAgentReport

_SEVERITY_LABEL = {
    Severity.HEALTHY: ("Healthy", "🟢"),
    Severity.WARNING: ("At risk", "🟡"),
    Severity.CRITICAL: ("Critical", "🔴"),
}


def campaign_short_name(report: TableAgentReport) -> str:
    return (report.campaign_type or report.table_name).replace(" campaigns", "")


def campaign_tab_label(report: TableAgentReport) -> str:
    name = campaign_short_name(report)
    _, icon = _SEVERITY_LABEL.get(report.severity, ("", "⚪"))
    return f"{icon} {name}"


def format_summary_paragraphs(summary: str) -> str:
    text = summary.strip()
    if not text:
        return ""
    parts = [part.strip() for part in text.replace("\n", " ").split(". ") if part.strip()]
    return "\n\n".join(f"{part}{'' if part.endswith('.') else '.'}" for part in parts)


def render_campaign_summary(report: TableAgentReport) -> None:
    severity_name, severity_icon = _SEVERITY_LABEL.get(report.severity, ("Unknown", "⚪"))
    campaign_name = campaign_short_name(report)

    if report.severity == Severity.HEALTHY:
        st.success(f"{severity_icon} **{campaign_name}** — {severity_name}")
    elif report.severity == Severity.WARNING:
        st.warning(f"{severity_icon} **{campaign_name}** — {severity_name}")
    else:
        st.error(f"{severity_icon} **{campaign_name}** — {severity_name}")

    if report.summary:
        st.markdown(format_summary_paragraphs(report.summary))
    else:
        st.info("No AI summary is available for this campaign type yet.")


def render_campaign_summary_tabs(
    reports: list[TableAgentReport],
    *,
    empty_message: str = "AI summaries will appear here after OpenRouter is configured.",
) -> None:
    if not reports:
        st.info(empty_message)
        return

    st.markdown("###### AI summary by campaign type")
    tab_labels = [campaign_tab_label(report) for report in reports]
    campaign_tabs = st.tabs(tab_labels)
    for tab, report in zip(campaign_tabs, reports):
        with tab:
            render_campaign_summary(report)
