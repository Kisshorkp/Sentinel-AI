"""Tests for spend analytics service."""

from __future__ import annotations

from datetime import date

from config.settings import AppSettings
from models.campaign import RiskLevel
from services.spend_analytics_service import SpendAnalyticsService


def _campaign(spend: float, budget: float, name: str = "Test") -> object:
    from models.campaign import CampaignSpend

    return CampaignSpend(
        campaign_id="1",
        campaign_name=name,
        stakeholder="Team A",
        monthly_budget=budget,
        spend_mtd=spend,
        last_updated=date(2026, 7, 10),
    )


def test_utilization_calculation():
    campaign = _campaign(5000, 10000)
    assert campaign.utilization_pct == 50.0


def test_risk_level_warning():
    settings = AppSettings(warning_threshold_pct=80, critical_threshold_pct=100)
    campaign = _campaign(8500, 10000)
    assert campaign.risk_level(settings.warning_threshold_pct, settings.critical_threshold_pct) == RiskLevel.WARNING


def test_risk_level_over_budget():
    settings = AppSettings(warning_threshold_pct=80, critical_threshold_pct=100)
    campaign = _campaign(11000, 10000)
    assert campaign.risk_level(settings.warning_threshold_pct, settings.critical_threshold_pct) == RiskLevel.OVER_BUDGET


def test_dashboard_summary():
    settings = AppSettings()
    service = SpendAnalyticsService(settings)
    campaigns = [
        _campaign(9000, 10000, "A"),
        _campaign(11000, 10000, "B"),
    ]
    summary = service.summarize(campaigns)
    assert summary.total_budget == 20000
    assert summary.total_spend_mtd == 20000
    assert summary.campaigns_over_budget == 1
