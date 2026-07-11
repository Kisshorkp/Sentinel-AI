"""Tests for campaign pipeline tab."""

from __future__ import annotations

from datetime import date

from components.campaign_pipeline_tab import _type_campaign_table_rows
from models.campaign_daily_snapshot import CampaignDailySnapshotRow


def _row(name: str, campaign_type: str = "Search campaigns") -> CampaignDailySnapshotRow:
    return CampaignDailySnapshotRow(
        campaign_type=campaign_type,
        campaign_id="123",
        campaign_name=name,
        t1_date=date(2026, 7, 9),
        t1_cost=100,
        t2_date=date(2026, 7, 8),
        t2_cost=80,
        today_date=date(2026, 7, 10),
        today_cost=120,
        t1_7day_avg_cost=90,
    )


def test_type_campaign_table_rows_maps_fields():
    rows = _type_campaign_table_rows([_row("Brand")], "2026-07-09", "2026-07-08")
    assert rows[0]["Campaign"] == "Brand"
    assert rows[0]["2026-07-09"] == 100
