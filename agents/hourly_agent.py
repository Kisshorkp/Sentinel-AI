"""Agent for Table 3 — Hourly breakdown."""

from __future__ import annotations

from datetime import datetime

from config.settings import AppSettings
from models.agent_report import CheckStatus, Severity, TableAgentReport, ThresholdCheck
from agents.llm import invoke_summary
from utils.formatting import format_currency


def current_display_hour(now: datetime | None = None) -> int:
    """Return current clock hour as 0–23 (0 = midnight hour)."""
    anchor = now or datetime.now()
    return anchor.hour


def _find_current_hour_row(
    hourly_rows: list[dict[str, object]],
    display_hour: int,
) -> dict[str, object] | None:
    for row in hourly_rows:
        if int(row.get("Hour", 0)) == display_hour:
            return row
    return None


def evaluate_current_hour_overspend(
    hourly_rows: list[dict[str, object]],
    settings: AppSettings,
    now: datetime | None = None,
) -> ThresholdCheck:
    """Alert when current hour spend exceeds min cost and is >50% above 7-day same-hour avg."""
    display_hour = current_display_hour(now)
    row = _find_current_hour_row(hourly_rows, display_hour)
    currency = settings.app_currency
    min_cost = settings.hourly_overspend_min_cost
    pct = settings.hourly_overspend_vs_7day_pct
    threshold_multiplier = 1 + pct / 100

    if row is None:
        return ThresholdCheck(
            rule="current_hour_overspend",
            threshold=f"> {format_currency(min_cost, currency)} and > {pct}% above 7-day avg",
            actual=f"hour {display_hour} not found",
            status=CheckStatus.PASS,
        )

    today_cost = float(row.get("Today's cost", 0) or 0)
    seven_day_avg = float(row.get("T-1 7-day avg cost", 0) or 0)
    pct_vs_avg = ((today_cost - seven_day_avg) / seven_day_avg * 100) if seven_day_avg > 0 else 0.0

    if today_cost > min_cost and seven_day_avg > 0 and today_cost > seven_day_avg * threshold_multiplier:
        return ThresholdCheck(
            rule="current_hour_overspend",
            threshold=(
                f"> {format_currency(min_cost, currency)} and > {pct}% above "
                f"same-hour avg (T-1 to T-7)"
            ),
            actual=(
                f"Hour {display_hour}: {format_currency(today_cost, currency)} vs avg "
                f"{format_currency(seven_day_avg, currency)} ({pct_vs_avg:+.1f}%)"
            ),
            status=CheckStatus.FAIL,
            message=(
                f"Overspend alert: hour {display_hour} today is {format_currency(today_cost, currency)}, "
                f"more than {pct}% above the 7-day average for this hour."
            ),
        )

    if today_cost > min_cost and seven_day_avg <= 0:
        return ThresholdCheck(
            rule="current_hour_overspend",
            threshold=(
                f"> {format_currency(min_cost, currency)} and > {pct}% above "
                f"same-hour avg (T-1 to T-7)"
            ),
            actual=(
                f"Hour {display_hour}: {format_currency(today_cost, currency)} "
                f"(no 7-day baseline for this hour)"
            ),
            status=CheckStatus.PASS,
            message="Spend exceeds minimum but no 7-day same-hour average to compare.",
        )

    return ThresholdCheck(
        rule="current_hour_overspend",
        threshold=(
            f"> {format_currency(min_cost, currency)} and > {pct}% above "
            f"same-hour avg (T-1 to T-7)"
        ),
        actual=(
            f"Hour {display_hour}: {format_currency(today_cost, currency)} vs avg "
            f"{format_currency(seven_day_avg, currency)} ({pct_vs_avg:+.1f}%)"
        ),
        status=CheckStatus.PASS,
    )


def run_hourly_agent(
    campaign_type: str,
    hourly_rows: list[dict[str, object]],
    settings: AppSettings,
    now: datetime | None = None,
) -> TableAgentReport:
    checks = [evaluate_current_hour_overspend(hourly_rows, settings, now=now)]

    severity = Severity.CRITICAL if any(c.status == CheckStatus.FAIL for c in checks) else (
        Severity.WARNING if any(c.status == CheckStatus.WARNING for c in checks) else Severity.HEALTHY
    )
    data = (
        f"Currency: INR (₹); Campaign: {campaign_type}; Current hour: {current_display_hour(now)}; "
        f"Checks: {[c.model_dump() for c in checks]}"
    )
    summary = invoke_summary(
        settings,
        "Summarize the current-hour spend check for this hourly breakdown in 2-3 sentences. "
        "Use ₹INR for every money amount — never dollars.",
        data,
    )
    return TableAgentReport(
        table_name="Hourly breakdown",
        campaign_type=campaign_type,
        checks=checks,
        severity=severity,
        summary=summary,
    )
