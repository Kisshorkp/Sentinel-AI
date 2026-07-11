"""Display AI agent checklist and OpenAI summary under tables."""

from __future__ import annotations

import streamlit as st

from models.agent_report import CheckStatus, PipelineAgentReport, Severity, TableAgentReport


def _severity_icon(severity: Severity) -> str:
    return {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(severity.value, "⚪")


def render_table_agent_report(report: TableAgentReport, *, show_summary: bool = True) -> None:
    if report.campaign_name:
        label = f"{report.campaign_name} ({report.campaign_id or 'n/a'})"
    else:
        label = report.campaign_type or report.table_name
    st.markdown(f"**{_severity_icon(report.severity)} AI agent — {label}**")
    passed = sum(1 for c in report.checks if c.status == CheckStatus.PASS)
    st.caption(f"Checklist: {passed}/{len(report.checks)} passed")
    for check in report.checks:
        icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(check.status.value, "•")
        st.markdown(f"{icon} **{check.rule}** — {check.actual} (threshold: {check.threshold})")
        if check.message:
            st.caption(check.message)
    if report.summary and show_summary:
        st.info(report.summary)
    if report.email_log:
        with st.expander("Email alerts", expanded=report.email_sent):
            for line in report.email_log:
                st.caption(line)
            if report.email_sent:
                st.success("Alert email sent for this table.")


def render_pipeline_report(agent_report: PipelineAgentReport | None, table_filter: str | None = None) -> None:
    if agent_report is None:
        return

    if table_filter == "Analyzer results":
        for report in agent_report.analyzer_table:
            render_table_agent_report(report)
        return
    if table_filter == "Daily spend snapshot":
        for report in agent_report.daily_snapshot:
            render_table_agent_report(report)
        return
    if table_filter == "Campaign daily spend snapshot":
        current_type: str | None = None
        for report in agent_report.campaign_daily_snapshot:
            if report.campaign_type != current_type:
                st.markdown(f"**{report.campaign_type}**")
                current_type = report.campaign_type
            render_table_agent_report(report, show_summary=False)
        if agent_report.campaign_daily_overall:
            st.markdown(
                f"**{_severity_icon(agent_report.campaign_daily_overall.severity)} "
                f"Overall — {agent_report.campaign_daily_overall.table_name}**"
            )
            if agent_report.campaign_daily_overall.summary:
                st.info(agent_report.campaign_daily_overall.summary)
            if agent_report.campaign_daily_overall.email_log:
                with st.expander("Email alerts", expanded=agent_report.campaign_daily_overall.email_sent):
                    for line in agent_report.campaign_daily_overall.email_log:
                        st.caption(line)
        return
    if table_filter == "Hourly breakdown" and agent_report.hourly:
        render_table_agent_report(agent_report.hourly)
        return

    st.markdown(f"### {_severity_icon(agent_report.overall_severity)} Overall AI assessment")
    if agent_report.overall_summary:
        st.success(agent_report.overall_summary)
    for line in agent_report.email_log:
        st.caption(line)
