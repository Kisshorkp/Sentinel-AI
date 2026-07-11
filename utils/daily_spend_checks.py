"""Helpers for daily spend snapshot threshold checks."""

from __future__ import annotations

from datetime import date, timedelta


def calculate_daily_budget(budget: float, field_start: date, field_end: date) -> float:
    """Prorated daily budget across the field's selected date range."""
    total_days = (field_end - field_start).days + 1
    if budget <= 0 or total_days <= 0:
        return 0.0
    return budget / total_days


def max_consecutive_days_below_budget_pct(
    daily_costs: list[float],
    daily_budget: float,
    budget_pct: float,
) -> int:
    """Longest run of days where spend is below budget_pct of daily budget."""
    if daily_budget <= 0 or not daily_costs:
        return 0

    threshold = daily_budget * (budget_pct / 100)
    max_streak = 0
    current = 0
    for cost in daily_costs:
        if cost < threshold:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return max_streak


def iter_days_inclusive(start: date, end: date):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)
