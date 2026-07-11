"""Email alerts triggered by AI agent checks for each pipeline table."""

from __future__ import annotations

import logging
from typing import Any

import yaml

from config.settings import AppSettings
from models.agent_report import CheckStatus, PipelineAgentReport, Severity, TableAgentReport, ThresholdCheck
from models.campaign import RiskLevel, SpendAlert
from agents.llm import invoke_summary
from agents.supervisor import _worst_report
from services.alert_email_template import (
    build_ai_insight_prompt,
    build_critical_alert_email_html,
    build_critical_alert_email_text,
)
from services.email_service import EmailService

logger = logging.getLogger(__name__)

_sent_alert_keys: set[str] = set()

# Cap per-campaign critical emails so Budget Alerts does not flood inboxes.
_MAX_CAMPAIGN_ROW_EMAILS = 15

PIPELINE_STEP_LABELS: dict[str, str] = {
    "Analyzer results": "Account-wise",
    "Daily spend snapshot": "Daily-wise",
    "Hourly breakdown": "Hourly",
    "Campaign daily spend snapshot": "Campaign-wise",
}


def _load_yaml_recipients(settings: AppSettings) -> dict[str, list[str]]:
    path = settings.alert_recipients_path
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    parsed: dict[str, list[str]] = {}
    for key, value in data.items():
        if isinstance(value, list):
            parsed[str(key)] = [str(email) for email in value if email]
    return parsed


def _resolve_recipients(settings: AppSettings, campaign_type: str | None) -> list[str]:
    """Recipients from campaign-type YAML, plus _default and env fallback (deduped)."""
    yaml_map = _load_yaml_recipients(settings)
    recipients: list[str] = []
    for key in ("_default", campaign_type or ""):
        if key and key in yaml_map:
            recipients.extend(yaml_map[key])
    recipients.extend(settings.default_alert_recipients)
    seen: set[str] = set()
    unique: list[str] = []
    for email in recipients:
        lowered = email.lower()
        if lowered not in seen:
            seen.add(lowered)
            unique.append(email)
    return unique


def _critical_checks(report: TableAgentReport) -> list:
    return [c for c in report.checks if c.status == CheckStatus.FAIL]


def _failing_checks(report: TableAgentReport) -> list:
    """Backward-compatible alias — only critical (FAIL) checks trigger email."""
    return _critical_checks(report)


def _step_label(table_name: str) -> str:
    return PIPELINE_STEP_LABELS.get(table_name, table_name)


def _email_subject(report: TableAgentReport, settings: AppSettings) -> str:
    prefix = (settings.email_subject_prefix or "[Parul University (UG)] - [Sentinel AI]").strip()
    step = _step_label(report.table_name)
    campaign = report.campaign_type or "Account"
    if report.campaign_id:
        name = report.campaign_name or "Campaign"
        return f"{prefix} {step} critical alert — {name} (ID {report.campaign_id})"
    return f"{prefix} {step} critical alert — {campaign}"


def _spend_alert_subject(alert: SpendAlert, settings: AppSettings) -> str:
    prefix = (settings.email_subject_prefix or "[Parul University (UG)] - [Sentinel AI]").strip()
    return f"{prefix} Account-wise critical alert — {alert.campaign_name}"


def _table_alert_dedup_key(report: TableAgentReport) -> str:
    failing = _critical_checks(report)
    rules = ",".join(sorted(c.rule for c in failing))
    return (
        f"table:{report.table_name}:{report.campaign_type or ''}:"
        f"{report.campaign_id or ''}:{rules}"
    )


def _report_email_meta(report: TableAgentReport) -> dict[str, Any]:
    return {
        "start_date": report.start_date,
        "end_date": report.end_date,
        "budget_amount": report.budget_amount,
        "budget_period": report.budget_period,
        "primary_status": report.primary_status,
        "spend": report.spend_amount,
        "mtd_target": report.mtd_target,
        "mtd_actual": report.mtd_actual,
        "utilization_pct": report.utilization_pct,
    }


def _build_alert_bodies(report: TableAgentReport, failing: list, settings: AppSettings) -> tuple[str, str]:
    currency = "INR"
    insight = invoke_summary(
        settings,
        "You write concise AI insight blurbs for critical budget alert emails.",
        build_ai_insight_prompt(report, failing, currency=currency),
    )
    meta = _report_email_meta(report)
    html_body = build_critical_alert_email_html(
        report,
        failing,
        ai_insight=insight,
        currency=currency,
        meta=meta,
    )
    text_body = build_critical_alert_email_text(
        report,
        failing,
        ai_insight=insight,
        currency=currency,
        meta=meta,
    )
    return text_body, html_body


def send_table_email_alert(
    report: TableAgentReport,
    settings: AppSettings,
) -> tuple[bool, list[str]]:
    """Send one HTML critical alert email when any check is FAIL."""
    table_name = report.table_name
    campaign = report.campaign_type or "Account"
    failing = _critical_checks(report)

    if not failing:
        return False, []

    dedup_key = _table_alert_dedup_key(report)
    if dedup_key in _sent_alert_keys:
        return True, []

    recipients = _resolve_recipients(settings, report.campaign_type)
    if not recipients:
        logger.warning(
            "[%s / %s] Alerts detected but no recipients configured.",
            _step_label(table_name),
            campaign,
        )
        return False, []

    text_body, html_body = _build_alert_bodies(report, failing, settings)
    subject = _email_subject(report, settings)

    if not settings.smtp_configured:
        logger.info(
            "Alert email (SMTP not configured) — would send to %s | Subject: %s",
            ", ".join(recipients),
            subject,
        )
        return False, []

    try:
        EmailService(settings).send(recipients, subject, text_body, html_body=html_body)
    except Exception:
        logger.exception("Failed to send alert email for %s / %s", _step_label(table_name), campaign)
        return False, []

    _sent_alert_keys.add(dedup_key)
    logger.info(
        "Alert email sent to %s | %s / %s | %s triggered check(s)",
        ", ".join(recipients),
        _step_label(table_name),
        campaign,
        len(failing),
    )
    return True, []


def _spend_alert_dedup_key(alert: SpendAlert) -> str:
    return f"spend:{alert.campaign_id}:budget_utilization"


def send_spend_alert_email(alert: SpendAlert, settings: AppSettings) -> bool:
    """Send HTML critical budget utilization alert (account-wise fallback)."""
    if alert.risk_level not in {RiskLevel.OVER_BUDGET, RiskLevel.CRITICAL}:
        return False

    dedup_key = _spend_alert_dedup_key(alert)
    if dedup_key in _sent_alert_keys:
        return True

    recipients = _resolve_recipients(settings, None)
    if not recipients:
        logger.warning(
            "[Account-wise / %s] Critical budget alert but no recipients configured.",
            alert.campaign_name,
        )
        return False

    report = TableAgentReport(
        table_name="Analyzer results",
        campaign_id=alert.campaign_id,
        campaign_name=alert.campaign_name,
        checks=[
            ThresholdCheck(
                rule="budget_used_pct",
                threshold="<= 100%",
                actual=f"{alert.utilization_pct:.1f}%",
                status=CheckStatus.FAIL,
                message=alert.message,
            )
        ],
        severity=Severity.CRITICAL,
        summary=alert.message,
        spend_amount=alert.overspend_amount,
        utilization_pct=alert.utilization_pct,
        primary_status=alert.stakeholder,
    )

    text_body, html_body = _build_alert_bodies(report, report.checks, settings)
    subject = _spend_alert_subject(alert, settings)

    if not settings.smtp_configured:
        logger.info(
            "Critical budget alert email (SMTP not configured) — would send to %s | Subject: %s",
            ", ".join(recipients),
            subject,
        )
        return False

    try:
        EmailService(settings).send(recipients, subject, text_body, html_body=html_body)
    except Exception:
        logger.exception("Failed to send critical budget alert for %s", alert.campaign_name)
        return False

    _sent_alert_keys.add(dedup_key)
    logger.info(
        "Critical budget alert email sent to %s | Account-wise / %s",
        ", ".join(recipients),
        alert.campaign_name,
    )
    return True


def _refresh_report_email(report: TableAgentReport, settings: AppSettings) -> TableAgentReport:
    if not _critical_checks(report) or report.email_sent:
        return report
    sent, _ = send_table_email_alert(report, settings)
    return report.model_copy(update={"email_sent": sent})


def refresh_critical_email_delivery(
    pipeline: PipelineAgentReport,
    settings: AppSettings,
) -> PipelineAgentReport:
    """Retry unsent critical alert emails (e.g. after SMTP is configured)."""
    updated_analyzer = [_refresh_report_email(r, settings) for r in pipeline.analyzer_table]
    updated_daily = [_refresh_report_email(r, settings) for r in pipeline.daily_snapshot]
    updated_hourly = [_refresh_report_email(r, settings) for r in pipeline.hourly_snapshot]

    updated_campaign: list[TableAgentReport] = []
    campaign_emails = 0
    for report in pipeline.campaign_daily_snapshot:
        if (
            campaign_emails < _MAX_CAMPAIGN_ROW_EMAILS
            and _critical_checks(report)
            and not report.email_sent
        ):
            sent, _ = send_table_email_alert(report, settings)
            if sent:
                campaign_emails += 1
            updated_campaign.append(report.model_copy(update={"email_sent": sent}))
        else:
            updated_campaign.append(report)

    updated_by_type = [_refresh_report_email(r, settings) for r in pipeline.campaign_daily_by_type]
    overall = pipeline.campaign_daily_overall
    if overall is not None:
        overall = _refresh_report_email(overall, settings)

    any_sent = any(
        r.email_sent
        for r in updated_analyzer + updated_daily + updated_hourly + updated_campaign + updated_by_type
    )
    if overall and overall.email_sent:
        any_sent = True

    return pipeline.model_copy(
        update={
            "analyzer_table": updated_analyzer,
            "daily_snapshot": updated_daily,
            "hourly_snapshot": updated_hourly,
            "campaign_daily_snapshot": updated_campaign,
            "campaign_daily_by_type": updated_by_type,
            "campaign_daily_overall": overall,
            "email_sent": pipeline.email_sent or any_sent,
        }
    )


def run_pipeline_email_alerts(
    pipeline: PipelineAgentReport,
    settings: AppSettings,
) -> PipelineAgentReport:
    """Send emails for Account-wise, Daily-wise, Hourly, and Campaign-wise agent checks."""
    # Allow a fresh analyzer run to re-send the same critical alerts.
    _sent_alert_keys.clear()
    any_sent = False

    updated_analyzer: list[TableAgentReport] = []
    for report in pipeline.analyzer_table:
        sent, _ = send_table_email_alert(report, settings)
        any_sent = any_sent or sent
        updated_analyzer.append(report.model_copy(update={"email_sent": sent, "email_log": []}))

    updated_daily: list[TableAgentReport] = []
    for report in pipeline.daily_snapshot:
        sent, _ = send_table_email_alert(report, settings)
        any_sent = any_sent or sent
        updated_daily.append(report.model_copy(update={"email_sent": sent, "email_log": []}))

    updated_hourly_snapshot: list[TableAgentReport] = []
    for report in pipeline.hourly_snapshot:
        sent, _ = send_table_email_alert(report, settings)
        any_sent = any_sent or sent
        updated_hourly_snapshot.append(report.model_copy(update={"email_sent": sent, "email_log": []}))

    updated_campaign_daily: list[TableAgentReport] = []
    campaign_emails = 0
    for report in pipeline.campaign_daily_snapshot:
        if campaign_emails < _MAX_CAMPAIGN_ROW_EMAILS and _critical_checks(report):
            sent, _ = send_table_email_alert(report, settings)
            any_sent = any_sent or sent
            if sent:
                campaign_emails += 1
            updated_campaign_daily.append(report.model_copy(update={"email_sent": sent, "email_log": []}))
        else:
            updated_campaign_daily.append(report.model_copy(update={"email_sent": False, "email_log": []}))

    updated_campaign_by_type: list[TableAgentReport] = []
    for report in pipeline.campaign_daily_by_type:
        sent, _ = send_table_email_alert(report, settings)
        any_sent = any_sent or sent
        updated_campaign_by_type.append(report.model_copy(update={"email_sent": sent, "email_log": []}))

    overall = pipeline.campaign_daily_overall
    overall_sent = False
    if overall and any(_failing_checks(report) for report in updated_campaign_daily):
        overall_sent, _ = send_table_email_alert(overall, settings)
        any_sent = any_sent or overall_sent
        overall = overall.model_copy(update={"email_sent": overall_sent, "email_log": []})

    hourly = _worst_report(updated_hourly_snapshot) if updated_hourly_snapshot else pipeline.hourly

    return pipeline.model_copy(
        update={
            "analyzer_table": updated_analyzer,
            "daily_snapshot": updated_daily,
            "campaign_daily_snapshot": updated_campaign_daily,
            "campaign_daily_by_type": updated_campaign_by_type,
            "campaign_daily_overall": overall,
            "hourly_snapshot": updated_hourly_snapshot,
            "hourly": hourly,
            "email_sent": pipeline.email_sent or any_sent,
            "email_log": [],
        }
    )


def run_email_agent(
    report: TableAgentReport,
    settings: AppSettings,
) -> tuple[bool, list[str]]:
    """Send email for a single table report. Returns (sent, log lines)."""
    return send_table_email_alert(report, settings)
