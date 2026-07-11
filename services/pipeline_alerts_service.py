"""Extract pipeline alerts grouped by Account / Daily / Hourly / Campaign-wise."""

from __future__ import annotations

import uuid

from config.settings import AppSettings
from models.agent_report import CheckStatus, PipelineAgentReport, TableAgentReport
from models.campaign import RiskLevel, SpendAlert
from agents.email_agent import send_spend_alert_email


def _severity_from_check(status: CheckStatus) -> str:
    return "critical" if status == CheckStatus.FAIL else "warning"


def _severity_from_risk(risk: RiskLevel) -> str:
    if risk in {RiskLevel.OVER_BUDGET, RiskLevel.CRITICAL}:
        return "critical"
    return "warning"


def _alerts_from_report(report: TableAgentReport, pipeline_step: str) -> list[dict]:
    items: list[dict] = []
    for check in report.checks:
        if check.status == CheckStatus.PASS:
            continue
        title_parts = [pipeline_step.replace("_", " ").title()]
        if report.campaign_type:
            title_parts.append(report.campaign_type.replace(" campaigns", ""))
        if report.campaign_name:
            title_parts.append(report.campaign_name)
        severity = _severity_from_check(check.status)
        items.append(
            {
                "id": str(uuid.uuid4()),
                "pipeline_step": pipeline_step,
                "severity": severity,
                "email_sent": bool(report.email_sent) if severity == "critical" else False,
                "campaign_type": report.campaign_type,
                "campaign_id": report.campaign_id,
                "campaign_name": report.campaign_name,
                "rule": check.rule,
                "threshold": check.threshold,
                "actual": check.actual,
                "message": check.message or report.summary or f"{check.rule}: {check.actual}",
                "title": " · ".join(title_parts),
            }
        )
    return items


def _alerts_from_reports(reports: list[TableAgentReport], pipeline_step: str) -> list[dict]:
    alerts: list[dict] = []
    for report in reports:
        alerts.extend(_alerts_from_report(report, pipeline_step))
    return alerts


def _budget_alerts_as_account(
    spend_alerts: list[SpendAlert],
    settings: AppSettings | None = None,
) -> list[dict]:
    items: list[dict] = []
    for alert in spend_alerts:
        severity = _severity_from_risk(alert.risk_level)
        email_sent = False
        if severity == "critical" and settings is not None:
            email_sent = send_spend_alert_email(alert, settings)
        items.append(
            {
                "id": str(uuid.uuid4()),
                "pipeline_step": "account",
                "severity": severity,
                "email_sent": email_sent,
                "campaign_type": None,
                "campaign_id": alert.campaign_id,
                "campaign_name": alert.campaign_name,
                "rule": "budget_utilization",
                "threshold": "monthly_budget",
                "actual": f"{alert.utilization_pct:.1f}%",
                "message": alert.message,
                "title": alert.campaign_name,
                "stakeholder": alert.stakeholder,
                "utilization_pct": alert.utilization_pct,
                "overspend_amount": alert.overspend_amount,
            }
        )
    return items


def build_pipeline_alerts(
    agent_report: PipelineAgentReport | None,
    spend_alerts: list[SpendAlert] | None = None,
    settings: AppSettings | None = None,
) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {
        "account": [],
        "daily": [],
        "hourly": [],
        "campaign": [],
    }

    if agent_report is not None:
        grouped["account"] = _alerts_from_reports(agent_report.analyzer_table, "account")
        grouped["daily"] = _alerts_from_reports(agent_report.daily_snapshot, "daily")
        grouped["hourly"] = _alerts_from_reports(agent_report.hourly_snapshot, "hourly")
        campaign_items = _alerts_from_reports(agent_report.campaign_daily_snapshot, "campaign")
        campaign_items.extend(_alerts_from_reports(agent_report.campaign_daily_by_type, "campaign"))
        if agent_report.campaign_daily_overall:
            campaign_items.extend(_alerts_from_report(agent_report.campaign_daily_overall, "campaign"))
        grouped["campaign"] = campaign_items

    if not grouped["account"] and spend_alerts:
        grouped["account"] = _budget_alerts_as_account(spend_alerts, settings)

    for key in grouped:
        grouped[key].sort(
            key=lambda item: (0 if item["severity"] == "critical" else 1, item.get("title") or ""),
        )

    return grouped


def count_pipeline_alerts(grouped: dict[str, list[dict]]) -> int:
    return sum(len(items) for items in grouped.values())
