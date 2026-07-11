"""Tests for daily pipeline tab."""

from __future__ import annotations

from datetime import date

from components.daily_pipeline_tab import _build_daily_snapshot_rows
from models.analyzer_input import AnalyzerResult, CampaignFieldInput


def _field(label: str, t1: float, t2: float, today: float, avg: float) -> CampaignFieldInput:
    return CampaignFieldInput(
        label=label,
        budget=1000,
        cost=500,
        mtd_target=100,
        mtd_achieve=110,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 11),
        t1_date=date(2026, 7, 10),
        t2_date=date(2026, 7, 9),
        t1_cost=t1,
        t2_cost=t2,
        today_cost=today,
        t1_7day_avg_cost=avg,
    )


def test_build_daily_snapshot_rows_uses_t_dates():
    result = AnalyzerResult(
        account="123",
        account_start_date=date(2026, 7, 1),
        account_end_date=date(2026, 7, 11),
        fetch_start_date=date(2026, 7, 1),
        fetch_end_date=date(2026, 7, 11),
        fields=[_field("Search campaigns", 10, 8, 12, 9)],
        total_budget=1000,
        total_spend=500,
        total_converted_cost=500,
        total_conversions=1,
        total_conversions_value=10,
        highest_spend_field="Search campaigns",
        lowest_spend_field="Search campaigns",
    )
    rows, t1_label, t2_label = _build_daily_snapshot_rows(result)
    assert t1_label == "2026-07-10"
    assert t2_label == "2026-07-09"
    assert rows[0]["Campaign type"] == "Search"
    assert rows[0][t1_label] == 10
