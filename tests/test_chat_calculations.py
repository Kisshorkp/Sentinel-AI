"""Tests for chat calculations."""

from __future__ import annotations

import json
from datetime import date

from agents.chat_calculations import build_computed_metrics, run_requested_calculations
from agents.chat_context import build_chat_context
from config.settings import AppSettings
from models.analyzer_input import AnalyzerResult, CampaignFieldInput


def _result() -> AnalyzerResult:
    field = CampaignFieldInput(
        label="Search campaigns",
        budget=1000,
        cost=800,
        mtd_target=400,
        mtd_achieve=450,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 10),
        t1_cost=120,
        t2_cost=100,
        today_cost=150,
        t1_7day_avg_cost=100,
        recent_daily_costs=[40, 40, 40, 90, 90, 90, 90],
    )
    return AnalyzerResult(
        account="123",
        account_start_date=date(2026, 7, 1),
        account_end_date=date(2026, 7, 10),
        fetch_start_date=date(2026, 4, 1),
        fetch_end_date=date(2026, 7, 10),
        fields=[field],
        total_budget=1000,
        total_spend=800,
        total_converted_cost=800,
        total_conversions=1,
        total_conversions_value=0,
        highest_spend_field="Search campaigns",
        lowest_spend_field="Search campaigns",
    )


def test_build_computed_metrics_mtd_variance():
    metrics = build_computed_metrics(_result())
    row = metrics["per_campaign"][0]
    assert row["mtd_variance_amount"] == 50.0
    assert row["budget_utilization_pct"] == 80.0


def test_run_requested_calculations_total_cost():
    context = build_chat_context(
        _result(),
        None,
        None,
        None,
        settings=AppSettings(),
        user_question="what is the total cost?",
    )
    payload = json.loads(context)
    labels = [item["label"] for item in payload["calculation_results"]]
    assert "Total cost" in labels


def test_run_requested_calculations_mtd_variance_for_campaign():
    context = build_chat_context(
        _result(),
        None,
        None,
        None,
        settings=AppSettings(),
        user_question="MTD variance for Search campaigns",
    )
    payload = json.loads(context)
    assert any("MTD variance" in item["label"] for item in payload["calculation_results"])
