"""Tests for account pipeline tab."""

from __future__ import annotations

from datetime import date

from components.account_pipeline_tab import _build_spend_overview_rows
from components.campaign_summary_tabs import format_summary_paragraphs
from models.analyzer_input import AnalyzerResult, CampaignFieldInput


def _field(label: str, budget: float, cost: float, mtd_target: float, mtd_achieve: float) -> CampaignFieldInput:
    return CampaignFieldInput(
        label=label,
        budget=budget,
        cost=cost,
        mtd_target=mtd_target,
        mtd_achieve=mtd_achieve,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 11),
    )


def test_format_summary_paragraphs_splits_sentences():
    text = "First sentence. Second sentence"
    formatted = format_summary_paragraphs(text)
    assert "First sentence." in formatted
    assert "Second sentence." in formatted


def test_build_spend_overview_includes_variance():
    result = AnalyzerResult(
        account="123",
        account_start_date=date(2026, 7, 1),
        account_end_date=date(2026, 7, 11),
        fetch_start_date=date(2026, 7, 1),
        fetch_end_date=date(2026, 7, 11),
        fields=[_field("Search campaigns", 1000, 500, 100, 110)],
        total_budget=1000,
        total_spend=500,
        total_converted_cost=500,
        total_conversions=1,
        total_conversions_value=10,
        highest_spend_field="Search campaigns",
        lowest_spend_field="Search campaigns",
    )
    rows = _build_spend_overview_rows(result)
    assert rows[0]["MTD vs target"] == 10.0
