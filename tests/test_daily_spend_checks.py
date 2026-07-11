"""Tests for daily spend check helpers."""

from __future__ import annotations

from datetime import date

from utils.daily_spend_checks import (
    calculate_daily_budget,
    max_consecutive_days_below_budget_pct,
)


def test_calculate_daily_budget():
    assert calculate_daily_budget(1000, date(2026, 7, 1), date(2026, 7, 10)) == 100.0


def test_max_consecutive_days_below_budget_pct():
    daily_budget = 100.0
    costs = [90, 40, 30, 45, 80, 20, 25]
    assert max_consecutive_days_below_budget_pct(costs, daily_budget, 50) == 3
