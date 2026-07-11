"""Tests for alert service."""

from __future__ import annotations

from datetime import date

from config.settings import AppSettings
from models.campaign import CampaignSpend, RiskLevel
from services.alert_service import AlertService


def test_generates_warning_alert():
    settings = AppSettings(warning_threshold_pct=80, critical_threshold_pct=100)
    campaigns = [
        CampaignSpend(
            campaign_id="1",
            campaign_name="High Spend",
            stakeholder="Marketing",
            monthly_budget=10000,
            spend_mtd=8500,
            last_updated=date(2026, 7, 10),
        )
    ]
    alerts = AlertService(settings).generate_alerts(campaigns)
    assert len(alerts) == 1
    assert alerts[0].risk_level == RiskLevel.WARNING
    assert "Marketing" in alerts[0].message


def test_healthy_campaign_no_alert():
    settings = AppSettings()
    campaigns = [
        CampaignSpend(
            campaign_id="1",
            campaign_name="Healthy",
            stakeholder="Team",
            monthly_budget=10000,
            spend_mtd=3000,
            last_updated=date(2026, 7, 10),
        )
    ]
    alerts = AlertService(settings).generate_alerts(campaigns)
    assert alerts == []
