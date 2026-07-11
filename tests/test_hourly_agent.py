"""Tests for hourly AI agent overspend rules."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from config.settings import AppSettings
from agents.hourly_agent import evaluate_current_hour_overspend, run_hourly_agent


def _hourly_rows(hour: int, today_cost: float, avg_cost: float) -> list[dict[str, object]]:
    rows = [{"Hour": h, "Today's cost": 0.0, "T-1 7-day avg cost": 0.0} for h in range(0, 24)]
    rows[hour]["Today's cost"] = today_cost
    rows[hour]["T-1 7-day avg cost"] = avg_cost
    return rows


@patch("agents.hourly_agent.invoke_summary", return_value="mock summary")
def test_hourly_agent_triggers_overspend_alert(mock_summary):
    settings = AppSettings(
        app_currency="INR",
        hourly_overspend_min_cost=1000,
        hourly_overspend_vs_7day_pct=50,
    )
    rows = _hourly_rows(hour=13, today_cost=2000, avg_cost=1000)
    now = datetime(2026, 7, 10, 13, 30)

    check = evaluate_current_hour_overspend(rows, settings, now=now)
    assert check.status.value == "fail"
    assert check.rule == "current_hour_overspend"

    report = run_hourly_agent("Demand Gen campaigns", rows, settings, now=now)
    assert report.severity.value == "critical"


@patch("agents.hourly_agent.invoke_summary", return_value="mock summary")
def test_hourly_agent_passes_when_below_min_cost(mock_summary):
    settings = AppSettings(hourly_overspend_min_cost=1000, hourly_overspend_vs_7day_pct=50)
    rows = _hourly_rows(hour=13, today_cost=900, avg_cost=100)
    now = datetime(2026, 7, 10, 13, 30)

    check = evaluate_current_hour_overspend(rows, settings, now=now)
    assert check.status.value == "pass"


@patch("agents.hourly_agent.invoke_summary", return_value="mock summary")
def test_hourly_agent_passes_when_not_50pct_above_avg(mock_summary):
    settings = AppSettings(hourly_overspend_min_cost=1000, hourly_overspend_vs_7day_pct=50)
    rows = _hourly_rows(hour=13, today_cost=1400, avg_cost=1000)
    now = datetime(2026, 7, 10, 13, 30)

    check = evaluate_current_hour_overspend(rows, settings, now=now)
    assert check.status.value == "pass"
