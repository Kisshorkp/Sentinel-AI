"""Tests for campaign-level threshold checks."""

from __future__ import annotations

from datetime import date, datetime

from config.settings import AppSettings
from models.campaign_daily_snapshot import CampaignDailySnapshotRow, DeletedCampaignInfo
from utils.campaign_level_checks import (
    evaluate_campaign_daily_row,
    evaluate_deleted_campaigns,
    normalize_end_date,
)


def _row(**overrides) -> CampaignDailySnapshotRow:
    base = {
        "campaign_type": "Search campaigns",
        "campaign_id": "111",
        "campaign_name": "Brand",
        "t1_date": date(2026, 7, 9),
        "t1_cost": 100.0,
        "t2_date": date(2026, 7, 8),
        "t2_cost": 80.0,
        "today_date": date(2026, 7, 10),
        "today_cost": 50.0,
        "start_date": date(2026, 7, 1),
        "end_date": date(2026, 12, 31),
        "budget_amount": 1000.0,
        "budget_period": "DAILY",
        "primary_status": "ELIGIBLE",
        "last_6h_cost": 25.0,
    }
    base.update(overrides)
    return CampaignDailySnapshotRow(**base)


def test_normalize_end_date_treats_far_future_as_open_ended():
    assert normalize_end_date(date(2037, 12, 30)) is None
    assert normalize_end_date(date(2026, 7, 31)) == date(2026, 7, 31)


def test_start_date_t1_flags_warning():
    settings = AppSettings()
    t1 = date(2026, 7, 9)
    checks = evaluate_campaign_daily_row(
        _row(start_date=t1),
        settings,
        t1_date=t1,
        today_date=date(2026, 7, 10),
        type_avg_budget=1000.0,
    )
    start_check = next(check for check in checks if check.rule == "start_date_t1")
    assert start_check.status.value == "warning"


def test_zero_budget_is_fail():
    settings = AppSettings()
    checks = evaluate_campaign_daily_row(
        _row(budget_amount=0),
        settings,
        t1_date=date(2026, 7, 9),
        today_date=date(2026, 7, 10),
        type_avg_budget=1000.0,
    )
    budget_check = next(check for check in checks if check.rule == "budget_amount_zero")
    assert budget_check.status.value == "fail"


def test_new_campaign_budget_deviation_triggers():
    settings = AppSettings(
        campaign_new_budget_deviation_pct=50.0,
        campaign_new_budget_min_delta=5000.0,
        app_currency="INR",
    )
    t1 = date(2026, 7, 9)
    checks = evaluate_campaign_daily_row(
        _row(start_date=t1, budget_amount=20000.0),
        settings,
        t1_date=t1,
        today_date=date(2026, 7, 10),
        type_avg_budget=10000.0,
    )
    deviation = next(check for check in checks if check.rule == "new_campaign_budget_deviation")
    assert deviation.status.value == "warning"


def test_eligible_zero_recent_spend_triggers():
    settings = AppSettings(campaign_zero_spend_hours=6)
    checks = evaluate_campaign_daily_row(
        _row(primary_status="ELIGIBLE", last_6h_cost=0.0),
        settings,
        t1_date=date(2026, 7, 9),
        today_date=date(2026, 7, 10),
        type_avg_budget=1000.0,
        now=datetime(2026, 7, 10, 14, 0),
    )
    zero_check = next(check for check in checks if check.rule == "eligible_zero_recent_spend")
    assert zero_check.status.value == "warning"


def test_end_date_imminent_flags_yesterday_or_today():
    settings = AppSettings()
    checks = evaluate_campaign_daily_row(
        _row(end_date=date(2026, 7, 10)),
        settings,
        t1_date=date(2026, 7, 9),
        today_date=date(2026, 7, 10),
        type_avg_budget=1000.0,
    )
    end_check = next(check for check in checks if check.rule == "end_date_imminent")
    assert end_check.status.value == "warning"


def test_deleted_campaign_type_check():
    deleted = [
        DeletedCampaignInfo(
            campaign_type="Search campaigns",
            campaign_id="999",
            campaign_name="Removed Brand",
        )
    ]
    check = evaluate_deleted_campaigns("Search campaigns", deleted)
    assert check is not None
    assert check.status.value == "warning"
    assert "999" in check.actual
