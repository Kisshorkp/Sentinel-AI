"""Tests for AI table agents (rules only, LLM mocked)."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

from config.settings import AppSettings
from models.analyzer_input import CampaignFieldInput
from agents.analyzer_table_agent import evaluate_analyzer_field
from agents.daily_snapshot_agent import evaluate_daily_field


def _field(**kwargs) -> CampaignFieldInput:
    defaults = dict(
        label="Search campaigns",
        budget=1000,
        cost=900,
        converted_cost=900,
        conversions=1,
        conversions_value=0,
        mtd_achieve=500,
        mtd_target=400,
        mtd_achieve_end=date(2026, 7, 9),
        t1_date=date(2026, 7, 9),
        t1_cost=100,
        t2_date=date(2026, 7, 8),
        t2_cost=80,
        t1_7day_avg_cost=90,
        recent_daily_costs=[40, 40, 40, 40, 90, 90, 90],
        today_date=date(2026, 7, 10),
        today_cost=150,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 10),
    )
    defaults.update(kwargs)
    return CampaignFieldInput(**defaults)


@patch("agents.analyzer_table_agent.invoke_summary", return_value="mock summary")
def test_analyzer_agent_flags_mtd_above_target_by_5pct(mock_summary):
    settings = AppSettings(mtd_target_tolerance_pct=5, warning_threshold_pct=80, critical_threshold_pct=100)
    report = evaluate_analyzer_field(_field(mtd_achieve=430, mtd_target=400), settings)
    assert any(c.rule == "mtd_achieve_above_target" and c.status.value == "warning" for c in report.checks)
    assert any(c.rule == "mtd_achieve_below_target" and c.status.value == "pass" for c in report.checks)


@patch("agents.analyzer_table_agent.invoke_summary", return_value="mock summary")
def test_analyzer_agent_flags_mtd_below_target_by_5pct(mock_summary):
    settings = AppSettings(mtd_target_tolerance_pct=5, warning_threshold_pct=80, critical_threshold_pct=100)
    report = evaluate_analyzer_field(_field(mtd_achieve=370, mtd_target=400), settings)
    assert any(c.rule == "mtd_achieve_below_target" and c.status.value == "warning" for c in report.checks)
    assert any(c.rule == "mtd_achieve_above_target" and c.status.value == "pass" for c in report.checks)


@patch("agents.analyzer_table_agent.invoke_summary", return_value="mock summary")
def test_analyzer_agent_passes_mtd_within_5pct_band(mock_summary):
    settings = AppSettings(mtd_target_tolerance_pct=5, warning_threshold_pct=80, critical_threshold_pct=100)
    report = evaluate_analyzer_field(_field(mtd_achieve=400, mtd_target=400), settings)
    assert all(c.status.value == "pass" for c in report.checks if c.rule.startswith("mtd_achieve"))


@patch("agents.daily_snapshot_agent.invoke_summary", return_value="mock summary")
def test_daily_agent_flags_t1_spend_above_7day_avg(mock_summary):
    settings = AppSettings(daily_spend_vs_7day_tolerance_pct=20)
    report = evaluate_daily_field(_field(t1_cost=120, t1_7day_avg_cost=90), settings)
    assert any(c.rule == "t1_vs_7day_avg" and c.status.value == "warning" for c in report.checks)


@patch("agents.daily_snapshot_agent.invoke_summary", return_value="mock summary")
def test_daily_agent_flags_t1_spend_below_7day_avg(mock_summary):
    settings = AppSettings(daily_spend_vs_7day_tolerance_pct=20)
    report = evaluate_daily_field(_field(t1_cost=60, t1_7day_avg_cost=90), settings)
    assert any(c.rule == "t1_vs_7day_avg" and c.status.value == "warning" for c in report.checks)


@patch("agents.daily_snapshot_agent.invoke_summary", return_value="mock summary")
def test_daily_agent_flags_consecutive_low_spend(mock_summary):
    settings = AppSettings(
        low_daily_spend_budget_pct=50,
        low_daily_spend_consecutive_days=3,
        daily_spend_vs_7day_tolerance_pct=20,
    )
    report = evaluate_daily_field(
        _field(
            budget=1000,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 10),
            recent_daily_costs=[40, 40, 40, 90, 90, 90, 90],
            t1_cost=90,
            t1_7day_avg_cost=90,
        ),
        settings,
    )
    assert any(c.rule == "consecutive_low_daily_spend" and c.status.value == "warning" for c in report.checks)
