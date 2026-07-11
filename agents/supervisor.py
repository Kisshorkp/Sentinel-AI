"""Merge agent reports and produce overall summary."""

from __future__ import annotations

from config.settings import AppSettings
from models.agent_report import PipelineAgentReport, Severity, TableAgentReport
from agents.llm import invoke_summary


def _max_severity(reports: list[TableAgentReport]) -> Severity:
    order = {Severity.HEALTHY: 0, Severity.WARNING: 1, Severity.CRITICAL: 2}
    worst = Severity.HEALTHY
    for report in reports:
        if order[report.severity] > order[worst]:
            worst = report.severity
    return worst


def _worst_report(reports: list[TableAgentReport]) -> TableAgentReport | None:
    if not reports:
        return None
    order = {Severity.HEALTHY: 0, Severity.WARNING: 1, Severity.CRITICAL: 2}
    return max(reports, key=lambda report: order[report.severity])


def run_supervisor(
    analyzer_reports: list[TableAgentReport],
    daily_reports: list[TableAgentReport],
    hourly_reports: list[TableAgentReport] | None,
    settings: AppSettings,
) -> PipelineAgentReport:
    hourly_reports = hourly_reports or []
    all_reports = analyzer_reports + daily_reports + hourly_reports
    overall = _max_severity(all_reports)

    bullet_lines = []
    for report in all_reports:
        bullet_lines.append(f"{report.table_name} / {report.campaign_type}: {report.severity.value}")

    summary = invoke_summary(
        settings,
        "Write a brief executive summary (3-4 sentences) of Sentinel AI findings for stakeholders. "
        "Use ₹INR for every money amount — never dollars or USD.",
        "Currency: INR (₹)\n" + "\n".join(bullet_lines),
    )
    return PipelineAgentReport(
        analyzer_table=analyzer_reports,
        daily_snapshot=daily_reports,
        hourly_snapshot=hourly_reports,
        hourly=_worst_report(hourly_reports),
        overall_severity=overall,
        overall_summary=summary,
    )
