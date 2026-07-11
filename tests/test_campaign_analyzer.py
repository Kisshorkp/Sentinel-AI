"""Tests for campaign analyzer service."""

from __future__ import annotations

from datetime import date

from models.analyzer_input import AnalyzerFormInput, CampaignFieldInput, resolve_fetch_end_date
from services.campaign_analyzer_service import CampaignAnalyzerService


def _field(label: str, cost: float, budget: float = 0) -> CampaignFieldInput:
    return CampaignFieldInput(
        label=label,
        budget=budget,
        cost=cost,
        converted_cost=cost,
        conversions=10,
        conversions_value=cost * 2,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 10),
    )


def test_analyzer_totals_and_ranking():
    form = AnalyzerFormInput(
        account="Test Account",
        account_start_date=date(2026, 7, 1),
        account_end_date=date(2026, 7, 31),
        fetch_start_date=date(2026, 4, 12),
        fetch_end_date=date(2026, 7, 10),
        search_campaigns=_field("Search campaigns", 5000, 10000),
        video_campaigns=_field("Video campaigns", 2000, 5000),
        demand_gen_campaigns=_field("Demand Gen campaigns", 1000, 3000),
        performance_max_campaigns=_field("Performance Max campaigns", 3000, 8000),
    )
    result = CampaignAnalyzerService().analyze(form)
    assert result.total_spend == 11000
    assert result.total_budget == 26000
    assert result.highest_spend_field == "Search campaigns"


def test_fetch_end_date_uses_max():
    from models.analyzer_input import AnalyzerFormRequest, CampaignFieldFormInput

    req = AnalyzerFormRequest(
        account="123",
        account_start_date=date(2026, 1, 1),
        account_end_date=date(2026, 6, 1),
        search_campaigns=CampaignFieldFormInput(
            label="Search campaigns", budget=0, start_date=date(2026, 1, 1), end_date=date(2026, 7, 10)
        ),
        video_campaigns=CampaignFieldFormInput(
            label="Video campaigns", budget=0, start_date=date(2026, 1, 1), end_date=date(2026, 5, 1)
        ),
        demand_gen_campaigns=CampaignFieldFormInput(
            label="Demand Gen campaigns", budget=0, start_date=date(2026, 1, 1), end_date=date(2026, 8, 15)
        ),
        performance_max_campaigns=CampaignFieldFormInput(
            label="Performance Max campaigns", budget=0, start_date=date(2026, 1, 1), end_date=date(2026, 4, 1)
        ),
    )
    assert req.fetch_end_date == date(2026, 8, 15)
    assert resolve_fetch_end_date(req) == date(2026, 8, 15)
