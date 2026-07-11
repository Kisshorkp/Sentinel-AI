"""Tests for campaign-level daily spend snapshot."""

from __future__ import annotations

from datetime import date

from services.campaign_daily_snapshot_service import (
    CampaignDailyMetricsStore,
    CampaignMeta,
    build_campaign_daily_snapshot_rows,
)


def test_build_campaign_daily_snapshot_rows_groups_by_type():
    store = CampaignDailyMetricsStore()
    t1 = date(2026, 7, 9)
    t2 = date(2026, 7, 8)
    today = date(2026, 7, 10)
    avg_start = date(2026, 7, 3)
    avg_end = date(2026, 7, 9)

    store.add_row("111", "Brand Search", "Search campaigns", t1, 2_000_000)
    store.add_row("111", "Brand Search", "Search campaigns", t2, 1_000_000)
    store.add_row("111", "Brand Search", "Search campaigns", today, 500_000)
    store.add_row("222", "PMax Main", "Performance Max campaigns", t1, 800_000)

    day = avg_start
    while day <= avg_end:
        if day not in {t1, t2}:
            store.add_row("111", "Brand Search", "Search campaigns", day, 700_000)
        day = date.fromordinal(day.toordinal() + 1)

    metadata = {
        "111": CampaignMeta("Brand Search", "Search campaigns"),
        "222": CampaignMeta("PMax Main", "Performance Max campaigns"),
    }
    rows, deleted = build_campaign_daily_snapshot_rows(
        store, metadata, {}, t1, t2, today, avg_start, avg_end
    )
    assert len(rows) == 2
    assert len(deleted) == 0
    assert rows[0].campaign_type == "Search campaigns"
    assert rows[0].campaign_name == "Brand Search"
    assert rows[0].campaign_id == "111"
    assert rows[0].t1_cost == 2.0
    assert rows[1].campaign_type == "Performance Max campaigns"


def test_build_campaign_daily_snapshot_rows_detects_deleted_campaigns():
    store = CampaignDailyMetricsStore()
    t1 = date(2026, 7, 9)
    t2 = date(2026, 7, 8)
    today = date(2026, 7, 10)
    avg_start = date(2026, 7, 3)
    avg_end = date(2026, 7, 9)

    store.add_row("111", "Brand Search", "Search campaigns", t1, 1_000_000)
    metadata = {"222": CampaignMeta("Still Active", "Search campaigns")}

    rows, deleted = build_campaign_daily_snapshot_rows(
        store, metadata, {}, t1, t2, today, avg_start, avg_end
    )
    assert len(rows) == 2
    assert len(deleted) == 1
    assert deleted[0].campaign_id == "111"
