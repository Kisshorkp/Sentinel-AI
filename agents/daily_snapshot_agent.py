"""Agent for Table 2 — Daily spend snapshot."""

from __future__ import annotations

from config.settings import AppSettings
from models.analyzer_input import AnalyzerResult
from models.agent_report import CheckStatus, Severity, TableAgentReport, ThresholdCheck
from agents.llm import invoke_summary
from utils.daily_spend_checks import (
    calculate_daily_budget,
    max_consecutive_days_below_budget_pct,
)


def _worst_severity(checks: list[ThresholdCheck]) -> Severity:
    if any(c.status == CheckStatus.FAIL for c in checks):
        return Severity.CRITICAL
    if any(c.status == CheckStatus.WARNING for c in checks):
        return Severity.WARNING
    return Severity.HEALTHY


def _daily_cost_series(field) -> list[float]:
    if field.recent_daily_costs:
        return field.recent_daily_costs
    costs = [field.t2_cost, field.t1_cost]
    if field.today_date is not None:
        costs.append(field.today_cost)
    return costs


def evaluate_daily_field(field, settings: AppSettings) -> TableAgentReport:
    checks: list[ThresholdCheck] = []
    tolerance = settings.daily_spend_vs_7day_tolerance_pct

    if field.t1_7day_avg_cost > 0:
        deviation_pct = (field.t1_cost - field.t1_7day_avg_cost) / field.t1_7day_avg_cost * 100
        if deviation_pct > tolerance:
            checks.append(
                ThresholdCheck(
                    rule="t1_vs_7day_avg",
                    threshold=f"within ±{tolerance}% of 7-day avg",
                    actual=f"{deviation_pct:+.1f}% ({field.t1_cost:.2f} vs avg {field.t1_7day_avg_cost:.2f})",
                    status=CheckStatus.WARNING,
                    message=f"T-1 spend is more than {tolerance}% above the last 7-day daily average.",
                )
            )
        elif deviation_pct < -tolerance:
            checks.append(
                ThresholdCheck(
                    rule="t1_vs_7day_avg",
                    threshold=f"within ±{tolerance}% of 7-day avg",
                    actual=f"{deviation_pct:+.1f}% ({field.t1_cost:.2f} vs avg {field.t1_7day_avg_cost:.2f})",
                    status=CheckStatus.WARNING,
                    message=f"T-1 spend is more than {tolerance}% below the last 7-day daily average.",
                )
            )
        else:
            checks.append(
                ThresholdCheck(
                    rule="t1_vs_7day_avg",
                    threshold=f"within ±{tolerance}% of 7-day avg",
                    actual=f"{deviation_pct:+.1f}%",
                    status=CheckStatus.PASS,
                )
            )

    daily_budget = calculate_daily_budget(field.budget, field.start_date, field.end_date)
    daily_costs = _daily_cost_series(field)
    min_days = settings.low_daily_spend_consecutive_days
    budget_pct = settings.low_daily_spend_budget_pct

    if daily_budget > 0 and daily_costs:
        streak = max_consecutive_days_below_budget_pct(daily_costs, daily_budget, budget_pct)
        threshold_spend = daily_budget * (budget_pct / 100)
        if streak >= min_days:
            checks.append(
                ThresholdCheck(
                    rule="consecutive_low_daily_spend",
                    threshold=f"< {budget_pct}% of daily budget ({threshold_spend:.2f}) for {min_days}+ days",
                    actual=f"{streak} consecutive day(s)",
                    status=CheckStatus.WARNING,
                    message=(
                        f"Daily spend stayed below {budget_pct}% of prorated daily budget "
                        f"for {streak} consecutive days."
                    ),
                )
            )
        else:
            checks.append(
                ThresholdCheck(
                    rule="consecutive_low_daily_spend",
                    threshold=f"< {budget_pct}% of daily budget for {min_days}+ consecutive days",
                    actual=f"{streak} consecutive day(s)",
                    status=CheckStatus.PASS,
                )
            )

    severity = _worst_severity(checks)
    data = (
        f"Currency: INR (₹); Campaign: {field.label}; "
        f"T-1 cost: ₹{field.t1_cost:,.2f}; T-2 cost: ₹{field.t2_cost:,.2f}; "
        f"Today: ₹{field.today_cost:,.2f}; 7-day avg: ₹{field.t1_7day_avg_cost:,.2f}; "
        f"Daily budget: ₹{daily_budget:,.2f}; Recent daily costs (INR): {daily_costs}; "
        f"Checks: {[c.model_dump() for c in checks]}"
    )
    summary = invoke_summary(
        settings,
        "You are a Google Ads spend analyst. Summarize daily snapshot trends in 2-3 sentences. "
        "Use ₹INR for every money amount — never dollars.",
        data,
    )
    return TableAgentReport(
        table_name="Daily spend snapshot",
        campaign_type=field.label,
        checks=checks,
        severity=severity,
        summary=summary,
    )


def run_daily_snapshot_agent(result: AnalyzerResult, settings: AppSettings) -> list[TableAgentReport]:
    return [evaluate_daily_field(field, settings) for field in result.fields]
