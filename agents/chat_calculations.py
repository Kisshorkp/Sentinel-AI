"""Deterministic metrics and calculations for the chatbot."""

from __future__ import annotations

import re
from typing import Any

from models.analyzer_input import AnalyzerResult
from utils.daily_spend_checks import calculate_daily_budget, max_consecutive_days_below_budget_pct


def _pct(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator * 100, 2)


def _round(value: float | None, places: int = 2) -> float | None:
    if value is None:
        return None
    return round(value, places)


def build_computed_metrics(
    result: AnalyzerResult,
    hourly_rows: list[dict[str, object]] | None = None,
    extract_label: str | None = None,
    low_daily_spend_budget_pct: float = 50.0,
) -> dict[str, Any]:
    """Pre-compute derived metrics the chatbot can use for accurate answers."""
    per_campaign: list[dict[str, Any]] = []
    total_budget = 0.0
    total_cost = 0.0
    total_mtd_target = 0.0
    total_mtd_achieve = 0.0

    for field in result.fields:
        daily_budget = calculate_daily_budget(field.budget, field.start_date, field.end_date)
        mtd_variance = field.mtd_achieve - field.mtd_target
        mtd_variance_pct = _pct(field.mtd_achieve, field.mtd_target)
        mtd_gap_pct = _round((mtd_variance_pct - 100) if mtd_variance_pct is not None else None)

        t1_vs_7day_pct = _pct(field.t1_cost, field.t1_7day_avg_cost)
        today_vs_7day_pct = _pct(field.today_cost, field.t1_7day_avg_cost)
        t1_vs_t2_dod_pct = (
            _round((field.t1_cost - field.t2_cost) / field.t2_cost * 100)
            if field.t2_cost > 0
            else None
        )

        low_spend_streak = max_consecutive_days_below_budget_pct(
            field.recent_daily_costs or [field.t2_cost, field.t1_cost, field.today_cost],
            daily_budget,
            low_daily_spend_budget_pct,
        )

        entry = {
            "campaign_type": field.label,
            "budget_utilization_pct": _pct(field.cost, field.budget),
            "remaining_budget": _round(field.budget - field.cost),
            "mtd_variance_amount": _round(mtd_variance),
            "mtd_variance_pct_of_target": mtd_gap_pct,
            "mtd_achieve_pct_of_target": mtd_variance_pct,
            "daily_budget_prorated": _round(daily_budget),
            "t1_pct_of_daily_budget": _pct(field.t1_cost, daily_budget),
            "today_pct_of_daily_budget": _pct(field.today_cost, daily_budget),
            "t1_vs_7day_avg_pct": t1_vs_7day_pct,
            "today_vs_7day_avg_pct": today_vs_7day_pct,
            "t1_vs_t2_change_pct": t1_vs_t2_dod_pct,
            "consecutive_low_spend_days": low_spend_streak,
            "recent_daily_costs_sum": _round(sum(field.recent_daily_costs)),
        }
        per_campaign.append(entry)
        total_budget += field.budget
        total_cost += field.cost
        total_mtd_target += field.mtd_target
        total_mtd_achieve += field.mtd_achieve

    hourly_metrics: dict[str, Any] | None = None
    if hourly_rows and extract_label:
        current_hour_row = _current_hour_row(hourly_rows)
        if current_hour_row:
            today_cost = float(current_hour_row.get("Today's cost", 0) or 0)
            avg_cost = float(current_hour_row.get("T-1 7-day avg cost", 0) or 0)
            hourly_metrics = {
                "campaign_type": extract_label,
                "current_hour": current_hour_row.get("Hour"),
                "current_hour_today_cost": today_cost,
                "current_hour_7day_avg": avg_cost,
                "current_hour_vs_7day_avg_pct": _pct(today_cost, avg_cost),
                "current_hour_vs_7day_diff": _round(today_cost - avg_cost),
            }

    return {
        "account": result.account,
        "currency_note": "All amounts are in INR (₹). Never display $ or USD.",
        "totals": {
            "total_budget": _round(total_budget),
            "total_cost": _round(total_cost),
            "total_remaining_budget": _round(total_budget - total_cost),
            "total_budget_utilization_pct": _pct(total_cost, total_budget),
            "total_mtd_target": _round(total_mtd_target),
            "total_mtd_achieve": _round(total_mtd_achieve),
            "total_mtd_variance_amount": _round(total_mtd_achieve - total_mtd_target),
            "total_mtd_variance_pct_of_target": _round(
                _pct(total_mtd_achieve, total_mtd_target) - 100
                if total_mtd_target > 0
                else None
            ),
        },
        "per_campaign": per_campaign,
        "rankings": {
            "highest_spend_campaign": result.highest_spend_field,
            "lowest_spend_campaign": result.lowest_spend_field,
        },
        "hourly": hourly_metrics,
        "formulas": {
            "budget_utilization_pct": "cost / budget * 100",
            "mtd_variance_amount": "mtd_achieve - mtd_target",
            "mtd_variance_pct_of_target": "(mtd_achieve / mtd_target * 100) - 100",
            "daily_budget_prorated": "budget / days_in_date_range",
            "t1_vs_7day_avg_pct": "t1_cost / t1_7day_avg_cost * 100",
            "today_vs_7day_avg_pct": "today_cost / t1_7day_avg_cost * 100",
            "t1_vs_t2_change_pct": "(t1_cost - t2_cost) / t2_cost * 100",
        },
    }


def _current_hour_row(hourly_rows: list[dict[str, object]]) -> dict[str, object] | None:
    from agents.hourly_agent import current_display_hour

    hour = current_display_hour()
    for row in hourly_rows:
        if int(row.get("Hour", 0)) == hour:
            return row
    return None


def _match_campaign(question: str, campaign_types: list[str]) -> str | None:
    q = question.lower()
    for label in campaign_types:
        key = label.lower().replace(" campaigns", "")
        if key in q or label.lower() in q:
            return label
    return None


def run_requested_calculations(question: str, payload: dict[str, Any]) -> list[dict[str, str]]:
    """Run targeted calculations based on the user's question (accurate Python math)."""
    results: list[dict[str, str]] = []
    q = question.lower()
    metrics = payload.get("computed_metrics") or {}
    per_campaign = metrics.get("per_campaign") or []
    totals = metrics.get("totals") or {}
    campaigns = [row["campaign_type"] for row in payload.get("analyzer_table", [])]
    matched = _match_campaign(question, campaigns)

    def add(label: str, formula: str, value: Any) -> None:
        if value is None:
            return
        results.append({"label": label, "formula": formula, "result": str(value)})

    if any(word in q for word in ("total", "sum", "overall", "all campaign")):
        if "budget" in q and "util" not in q:
            add("Total budget", "sum(budget)", totals.get("total_budget"))
        if "cost" in q or "spend" in q:
            add("Total cost", "sum(cost)", totals.get("total_cost"))
        if "mtd" in q and "achieve" in q:
            add("Total MTD achieve", "sum(mtd_achieve)", totals.get("total_mtd_achieve"))
        if "mtd" in q and "target" in q:
            add("Total MTD target", "sum(mtd_target)", totals.get("total_mtd_target"))
        if "remaining" in q or "left" in q:
            add("Total remaining budget", "total_budget - total_cost", totals.get("total_remaining_budget"))
        if "util" in q or "used" in q or "utilization" in q:
            add(
                "Total budget utilization %",
                "total_cost / total_budget * 100",
                totals.get("total_budget_utilization_pct"),
            )

    if "mtd" in q and any(word in q for word in ("variance", "difference", "gap", "vs", "compare")):
        if matched:
            row = next((r for r in per_campaign if r["campaign_type"] == matched), None)
            if row:
                add(
                    f"{matched} MTD variance (amount)",
                    "mtd_achieve - mtd_target",
                    row.get("mtd_variance_amount"),
                )
                add(
                    f"{matched} MTD variance (% of target)",
                    "(mtd_achieve / mtd_target * 100) - 100",
                    row.get("mtd_variance_pct_of_target"),
                )
        else:
            add(
                "Total MTD variance (amount)",
                "total_mtd_achieve - total_mtd_target",
                totals.get("total_mtd_variance_amount"),
            )
            add(
                "Total MTD variance (% of target)",
                "(total_mtd_achieve / total_mtd_target * 100) - 100",
                totals.get("total_mtd_variance_pct_of_target"),
            )

    if any(word in q for word in ("7-day", "7 day", "average", "avg")) and "hour" not in q:
        target_rows = [r for r in per_campaign if r["campaign_type"] == matched] if matched else per_campaign
        for row in target_rows:
            label = row["campaign_type"]
            if "today" in q:
                add(
                    f"{label} today vs 7-day avg %",
                    "today_cost / t1_7day_avg_cost * 100",
                    row.get("today_vs_7day_avg_pct"),
                )
            else:
                add(
                    f"{label} T-1 vs 7-day avg %",
                    "t1_cost / t1_7day_avg_cost * 100",
                    row.get("t1_vs_7day_avg_pct"),
                )

    if any(word in q for word in ("day over day", "dod", "t-1", "t-2", "t1", "t2")):
        target_rows = [r for r in per_campaign if r["campaign_type"] == matched] if matched else per_campaign
        for row in target_rows:
            add(
                f"{row['campaign_type']} T-1 vs T-2 change %",
                "(t1_cost - t2_cost) / t2_cost * 100",
                row.get("t1_vs_t2_change_pct"),
            )

    if "budget" in q and ("util" in q or "used" in q or "%" in q):
        target_rows = [r for r in per_campaign if r["campaign_type"] == matched] if matched else per_campaign
        for row in target_rows:
            add(
                f"{row['campaign_type']} budget utilization %",
                "cost / budget * 100",
                row.get("budget_utilization_pct"),
            )

    if "daily budget" in q or "prorated" in q:
        target_rows = [r for r in per_campaign if r["campaign_type"] == matched] if matched else per_campaign
        for row in target_rows:
            add(
                f"{row['campaign_type']} daily budget (prorated)",
                "budget / days_in_range",
                row.get("daily_budget_prorated"),
            )

    if "percent" in q or "percentage" in q or "%" in q:
        numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", question)]
        if len(numbers) >= 2 and "of" in q:
            part, whole = numbers[0], numbers[1]
            if whole > 0:
                add(
                    f"{part} as % of {whole}",
                    f"{part} / {whole} * 100",
                    _round(part / whole * 100),
                )

    hourly = metrics.get("hourly")
    if hourly and "hour" in q:
        add(
            f"{hourly.get('campaign_type')} current hour vs 7-day avg %",
            "current_hour_today_cost / current_hour_7day_avg * 100",
            hourly.get("current_hour_vs_7day_avg_pct"),
        )
        add(
            f"{hourly.get('campaign_type')} current hour spend diff vs avg",
            "current_hour_today_cost - current_hour_7day_avg",
            hourly.get("current_hour_vs_7day_diff"),
        )

    return results
