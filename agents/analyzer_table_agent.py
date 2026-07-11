"""Agent for Table 1 — Analyzer results."""

from __future__ import annotations

from config.settings import AppSettings
from models.analyzer_input import AnalyzerResult
from models.agent_report import CheckStatus, Severity, TableAgentReport, ThresholdCheck
from agents.llm import invoke_summary


def _worst_severity(checks: list[ThresholdCheck]) -> Severity:
    if any(c.status == CheckStatus.FAIL for c in checks):
        return Severity.CRITICAL
    if any(c.status == CheckStatus.WARNING for c in checks):
        return Severity.WARNING
    return Severity.HEALTHY


def evaluate_analyzer_field(field, settings: AppSettings) -> TableAgentReport:
    checks: list[ThresholdCheck] = []

    budget_used = (field.cost / field.budget * 100) if field.budget > 0 else 0.0
    if field.budget > 0 and budget_used >= settings.critical_threshold_pct:
        checks.append(
            ThresholdCheck(
                rule="budget_used_pct",
                threshold=f">= {settings.critical_threshold_pct}%",
                actual=f"{budget_used:.1f}%",
                status=CheckStatus.FAIL,
                message="Cost exceeds entered budget.",
            )
        )
    elif field.budget > 0 and budget_used >= settings.warning_threshold_pct:
        checks.append(
            ThresholdCheck(
                rule="budget_used_pct",
                threshold=f">= {settings.warning_threshold_pct}%",
                actual=f"{budget_used:.1f}%",
                status=CheckStatus.WARNING,
                message="Budget utilization is high.",
            )
        )
    else:
        checks.append(
            ThresholdCheck(
                rule="budget_used_pct",
                threshold=f"< {settings.warning_threshold_pct}%",
                actual=f"{budget_used:.1f}%",
                status=CheckStatus.PASS,
            )
        )

    if field.mtd_target > 0:
        tolerance = settings.mtd_target_tolerance_pct
        upper_bound = field.mtd_target * (1 + tolerance / 100)
        lower_bound = field.mtd_target * (1 - tolerance / 100)
        mtd_pct = field.mtd_achieve / field.mtd_target * 100

        if field.mtd_achieve > upper_bound:
            checks.append(
                ThresholdCheck(
                    rule="mtd_achieve_above_target",
                    threshold=f"> MTD target + {tolerance}%",
                    actual=f"{mtd_pct:.1f}% of target ({field.mtd_achieve:.2f} vs {field.mtd_target:.2f})",
                    status=CheckStatus.WARNING,
                    message=f"MTD achieve is more than {tolerance}% above MTD target.",
                )
            )
        else:
            checks.append(
                ThresholdCheck(
                    rule="mtd_achieve_above_target",
                    threshold=f"<= MTD target + {tolerance}%",
                    actual=f"{mtd_pct:.1f}% of target",
                    status=CheckStatus.PASS,
                )
            )

        if field.mtd_achieve < lower_bound:
            checks.append(
                ThresholdCheck(
                    rule="mtd_achieve_below_target",
                    threshold=f"< MTD target - {tolerance}%",
                    actual=f"{mtd_pct:.1f}% of target ({field.mtd_achieve:.2f} vs {field.mtd_target:.2f})",
                    status=CheckStatus.WARNING,
                    message=f"MTD achieve is more than {tolerance}% below MTD target.",
                )
            )
        else:
            checks.append(
                ThresholdCheck(
                    rule="mtd_achieve_below_target",
                    threshold=f">= MTD target - {tolerance}%",
                    actual=f"{mtd_pct:.1f}% of target",
                    status=CheckStatus.PASS,
                )
            )

    severity = _worst_severity(checks)
    data = (
        f"Currency: INR (₹); Campaign: {field.label}; Budget: ₹{field.budget:,.2f}; "
        f"Cost: ₹{field.cost:,.2f}; MTD target: ₹{field.mtd_target:,.2f}; "
        f"MTD achieve: ₹{field.mtd_achieve:,.2f}; "
        f"Checks: {[c.model_dump() for c in checks]}"
    )
    summary = invoke_summary(
        settings,
        "You are a Google Ads spend analyst. Summarize in 2-3 sentences using ONLY the data provided. "
        "Use ₹INR for every money amount — never dollars.",
        data,
    )
    return TableAgentReport(
        table_name="Analyzer results",
        campaign_type=field.label,
        campaign_name=field.label,
        checks=checks,
        severity=severity,
        summary=summary,
        budget_amount=field.budget,
        spend_amount=field.cost,
        mtd_target=field.mtd_target,
        mtd_actual=field.mtd_achieve,
        utilization_pct=field.budget_utilization_pct,
        start_date=str(field.start_date) if field.start_date else None,
        end_date=str(field.end_date) if field.end_date else None,
    )


def run_analyzer_table_agent(result: AnalyzerResult, settings: AppSettings) -> list[TableAgentReport]:
    return [evaluate_analyzer_field(field, settings) for field in result.fields]
