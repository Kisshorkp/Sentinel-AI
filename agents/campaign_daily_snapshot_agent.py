"""Agent for campaign-level daily spend snapshot table (checks configurable)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from config.settings import AppSettings
from models.agent_report import CheckStatus, Severity, TableAgentReport, ThresholdCheck
from models.campaign_daily_snapshot import (
    CampaignDailyHygieneContext,
    CampaignDailySnapshotRow,
    DeletedCampaignInfo,
)
from agents.llm import invoke_summary
from services.google_ads_fetch_service import ANALYZER_LABELS
from utils.campaign_level_checks import evaluate_campaign_daily_row, evaluate_deleted_campaigns
from utils.mtd_metrics import reference_t_dates

# Keep LLM prompts well under model context limits (e.g. 128k) with hundreds of campaigns.
_MAX_TOP_SPEND_CAMPAIGNS = 12
_MAX_ISSUE_CAMPAIGNS = 20
_MAX_ISSUE_CHECKS = 40
_MAX_DELETED_LIST = 15


def _worst_severity(checks: list[ThresholdCheck]) -> Severity:
    if any(c.status == CheckStatus.FAIL for c in checks):
        return Severity.CRITICAL
    if any(c.status == CheckStatus.WARNING for c in checks):
        return Severity.WARNING
    return Severity.HEALTHY


def _max_report_severity(reports: list[TableAgentReport]) -> Severity:
    order = {Severity.HEALTHY: 0, Severity.WARNING: 1, Severity.CRITICAL: 2}
    worst = Severity.HEALTHY
    for report in reports:
        if order[report.severity] > order[worst]:
            worst = report.severity
    return worst


def _type_avg_budgets(rows: list[CampaignDailySnapshotRow]) -> dict[str, float]:
    by_type: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.budget_amount > 0:
            by_type[row.campaign_type].append(row.budget_amount)
    return {
        campaign_type: round(sum(values) / len(values), 2)
        for campaign_type, values in by_type.items()
        if values
    }


def _compact_llm_payload(
    campaign_type: str,
    rows: list[CampaignDailySnapshotRow],
    campaign_reports: list[TableAgentReport],
    *,
    deleted_campaigns: list[DeletedCampaignInfo] | None = None,
    type_checks: list[ThresholdCheck] | None = None,
) -> str:
    """Aggregate campaign + check data for LLM — never dump every row/check."""
    severity_counts = {"healthy": 0, "warning": 0, "critical": 0}
    for report in campaign_reports:
        severity_counts[report.severity.value] = severity_counts.get(report.severity.value, 0) + 1

    total_t1 = round(sum(r.t1_cost for r in rows), 2)
    total_today = round(sum(r.today_cost for r in rows), 2)
    total_avg = round(sum(r.t1_7day_avg_cost for r in rows), 2)
    zero_today = sum(1 for r in rows if r.today_cost <= 0)
    zero_budget = sum(1 for r in rows if r.budget_amount <= 0)

    ranked = sorted(
        rows,
        key=lambda r: float(r.t1_cost or 0) + float(r.today_cost or 0),
        reverse=True,
    )
    top_spend = [
        {
            "name": r.campaign_name[:60],
            "id": r.campaign_id,
            "t1": r.t1_cost,
            "today": r.today_cost,
            "avg7d": r.t1_7day_avg_cost,
            "budget": r.budget_amount,
            "status": r.primary_status,
        }
        for r in ranked[:_MAX_TOP_SPEND_CAMPAIGNS]
    ]

    issue_reports = [
        report
        for report in campaign_reports
        if report.severity in {Severity.WARNING, Severity.CRITICAL}
    ]
    issue_reports.sort(
        key=lambda r: (0 if r.severity == Severity.CRITICAL else 1, r.campaign_name or "")
    )

    issue_checks: list[dict] = []
    for report in issue_reports[:_MAX_ISSUE_CAMPAIGNS]:
        failing = [c for c in report.checks if c.status != CheckStatus.PASS]
        if not failing:
            continue
        issue_checks.append(
            {
                "name": (report.campaign_name or "")[:60],
                "id": report.campaign_id,
                "severity": report.severity.value,
                "issues": [
                    {
                        "rule": c.rule,
                        "status": c.status.value,
                        "actual": c.actual[:120],
                        "message": (c.message or "")[:160],
                    }
                    for c in failing[:4]
                ],
            }
        )
        if len(issue_checks) >= _MAX_ISSUE_CHECKS:
            break

    deleted = deleted_campaigns or []
    deleted_preview = [
        {"name": d.campaign_name[:60], "id": d.campaign_id, "type": d.campaign_type}
        for d in deleted[:_MAX_DELETED_LIST]
    ]

    type_level = [
        {
            "rule": c.rule,
            "status": c.status.value,
            "actual": c.actual[:160],
            "message": (c.message or "")[:160],
        }
        for c in (type_checks or [])
        if c.status != CheckStatus.PASS
    ]

    omitted_campaigns = max(0, len(rows) - len(top_spend))
    omitted_issues = max(0, len(issue_reports) - len(issue_checks))

    return (
        f"Campaign type: {campaign_type}\n"
        f"Currency: INR (₹) — all money fields below are Indian Rupees\n"
        f"Totals: campaigns={len(rows)}, t1_spend=₹{total_t1}, today_spend=₹{total_today}, "
        f"sum_7day_avg=₹{total_avg}, zero_today_spend={zero_today}, zero_budget={zero_budget}\n"
        f"Severity counts: {severity_counts}\n"
        f"Top spend campaigns (max {_MAX_TOP_SPEND_CAMPAIGNS}, omitted={omitted_campaigns}): {top_spend}\n"
        f"Campaigns with warnings/fails (max {_MAX_ISSUE_CAMPAIGNS}, omitted={omitted_issues}): {issue_checks}\n"
        f"Type-level checks: {type_level}\n"
        f"Deleted since yesterday (showing {len(deleted_preview)} of {len(deleted)}): {deleted_preview}"
    )


def evaluate_campaign_daily_row_report(
    row: CampaignDailySnapshotRow,
    settings: AppSettings,
    *,
    t1_date: date,
    today_date: date,
    type_avg_budget: float | None,
    now: datetime | None = None,
) -> TableAgentReport:
    checks = evaluate_campaign_daily_row(
        row,
        settings,
        t1_date=t1_date,
        today_date=today_date,
        type_avg_budget=type_avg_budget,
        now=now,
    )
    return TableAgentReport(
        table_name="Campaign daily spend snapshot",
        campaign_type=row.campaign_type,
        campaign_id=row.campaign_id,
        campaign_name=row.campaign_name,
        checks=checks,
        severity=_worst_severity(checks),
        summary="",
        start_date=str(row.start_date) if row.start_date else None,
        end_date=str(row.end_date) if row.end_date else None,
        budget_amount=row.budget_amount,
        budget_period=row.budget_period or None,
        primary_status=row.primary_status or None,
        spend_amount=round(float(row.t1_cost or 0) + float(row.today_cost or 0), 2),
    )


def build_campaign_type_summary_report(
    campaign_type: str,
    rows: list[CampaignDailySnapshotRow],
    campaign_reports: list[TableAgentReport],
    settings: AppSettings,
    *,
    deleted_campaigns: list[DeletedCampaignInfo] | None = None,
) -> TableAgentReport:
    """One AI summary covering all campaigns within a campaign type."""
    type_checks: list[ThresholdCheck] = []
    deleted_check = evaluate_deleted_campaigns(campaign_type, deleted_campaigns or [])
    if deleted_check is not None:
        type_checks.append(deleted_check)

    summary = invoke_summary(
        settings,
        (
            f"You are a Google Ads spend analyst. Write ONE overall summary (3-5 sentences) "
            f"for all {campaign_type} campaigns in the campaign daily spend snapshot. "
            "Cover pre-launch/setup validation (start/end dates, budget, budget mode) and "
            "hygiene anomalies (zero recent spend, ending campaigns, removed campaigns). "
            "Mention notable spend levels and trends vs 7-day averages. "
            "Do not write separate summaries per campaign. "
            "The payload is intentionally aggregated (top spenders + failing checks only). "
            "Use ₹INR for every money amount — never dollars or USD."
        ),
        "Currency: INR (₹)\n"
        + _compact_llm_payload(
            campaign_type,
            rows,
            campaign_reports,
            deleted_campaigns=deleted_campaigns,
            type_checks=type_checks,
        ),
    )

    severities = [_max_report_severity(campaign_reports)]
    if type_checks:
        severities.append(_worst_severity(type_checks))
    combined_severity = max(
        severities,
        key=lambda s: {Severity.HEALTHY: 0, Severity.WARNING: 1, Severity.CRITICAL: 2}[s],
    )

    return TableAgentReport(
        table_name="Campaign daily spend snapshot",
        campaign_type=campaign_type,
        checks=type_checks,
        severity=combined_severity,
        summary=summary,
    )


def build_campaign_daily_overall_report(
    rows: list[CampaignDailySnapshotRow],
    campaign_reports: list[TableAgentReport],
    settings: AppSettings,
    *,
    deleted_campaigns: list[DeletedCampaignInfo] | None = None,
) -> TableAgentReport:
    """One overall AI summary for the entire campaign daily spend snapshot table."""
    type_checks: list[ThresholdCheck] = []
    if deleted_campaigns:
        names = ", ".join(
            f"{item.campaign_name} ({item.campaign_id}, {item.campaign_type})"
            for item in deleted_campaigns[:_MAX_DELETED_LIST]
        )
        extra = len(deleted_campaigns) - min(len(deleted_campaigns), _MAX_DELETED_LIST)
        actual = f"{len(deleted_campaigns)} removed: {names}"
        if extra > 0:
            actual += f" (+{extra} more)"
        type_checks.append(
            ThresholdCheck(
                rule="campaign_removed",
                threshold="no campaigns removed since yesterday",
                actual=actual,
                status=CheckStatus.WARNING,
                message="Campaign IDs present yesterday are absent today (deleted/removed).",
            )
        )

    by_type_rows: dict[str, list[CampaignDailySnapshotRow]] = defaultdict(list)
    by_type_reports: dict[str, list[TableAgentReport]] = defaultdict(list)
    for row in rows:
        by_type_rows[row.campaign_type].append(row)
    for report in campaign_reports:
        if report.campaign_type:
            by_type_reports[report.campaign_type].append(report)

    type_rollups = []
    for label in ANALYZER_LABELS:
        type_rows = by_type_rows.get(label) or []
        if not type_rows:
            continue
        type_reps = by_type_reports.get(label) or []
        type_rollups.append(
            {
                "type": label,
                "campaigns": len(type_rows),
                "t1_spend": round(sum(r.t1_cost for r in type_rows), 2),
                "today_spend": round(sum(r.today_cost for r in type_rows), 2),
                "severity": _max_report_severity(type_reps).value if type_reps else "healthy",
                "warning_or_fail": sum(
                    1 for r in type_reps if r.severity in {Severity.WARNING, Severity.CRITICAL}
                ),
            }
        )

    compact = (
        f"Portfolio rollup by type: {type_rollups}\n"
        + _compact_llm_payload(
            "All campaigns",
            rows,
            campaign_reports,
            deleted_campaigns=deleted_campaigns,
            type_checks=type_checks,
        )
    )

    summary = invoke_summary(
        settings,
        (
            "You are a Google Ads spend analyst. Write ONE executive summary (3-5 sentences) "
            "for the full campaign daily spend snapshot across all campaign types. "
            "Highlight the riskiest types, spend vs 7-day averages, and hygiene issues. "
            "Do not list individual campaigns unless critical. "
            "The payload is intentionally aggregated. "
            "Use ₹INR for every money amount — never dollars or USD."
        ),
        "Currency: INR (₹)\n" + compact,
    )

    severities = [_max_report_severity(campaign_reports)]
    if type_checks:
        severities.append(_worst_severity(type_checks))
    combined = max(
        severities,
        key=lambda s: {Severity.HEALTHY: 0, Severity.WARNING: 1, Severity.CRITICAL: 2}[s],
    )

    return TableAgentReport(
        table_name="Campaign daily spend snapshot",
        campaign_type="All campaigns",
        checks=type_checks,
        severity=combined,
        summary=summary,
    )


def run_campaign_daily_snapshot_agent(
    rows: list[CampaignDailySnapshotRow],
    settings: AppSettings,
    hygiene: CampaignDailyHygieneContext | None = None,
    now: datetime | None = None,
) -> tuple[list[TableAgentReport], TableAgentReport | None, list[TableAgentReport]]:
    t1_date, _ = reference_t_dates()
    today_date = date.today()
    if hygiene and hygiene.t1_date:
        t1_date = hygiene.t1_date
    if hygiene and hygiene.today_date:
        today_date = hygiene.today_date
    deleted = hygiene.deleted_campaigns if hygiene else []
    type_avg = _type_avg_budgets(rows)

    campaign_reports = [
        evaluate_campaign_daily_row_report(
            row,
            settings,
            t1_date=t1_date,
            today_date=today_date,
            type_avg_budget=type_avg.get(row.campaign_type),
            now=now,
        )
        for row in rows
    ]
    if not campaign_reports:
        return [], None, []

    by_type: list[TableAgentReport] = []
    for campaign_type in ANALYZER_LABELS:
        type_rows = [row for row in rows if row.campaign_type == campaign_type]
        if not type_rows:
            continue
        type_reports = [report for report in campaign_reports if report.campaign_type == campaign_type]
        by_type.append(
            build_campaign_type_summary_report(
                campaign_type,
                type_rows,
                type_reports,
                settings,
                deleted_campaigns=deleted,
            )
        )

    overall = build_campaign_daily_overall_report(
        rows, campaign_reports, settings, deleted_campaigns=deleted
    )
    return campaign_reports, overall, by_type
