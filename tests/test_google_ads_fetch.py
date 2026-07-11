"""Tests for Google Ads fetch service."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

from config.settings import AppSettings
from models.analyzer_input import AnalyzerFormRequest, CampaignFieldFormInput
from services.google_ads_fetch_service import DailyMetricsStore, GoogleAdsFetchService


def test_date_range_90_days():
    settings = AppSettings(google_ads_lookback_days=90)
    service = GoogleAdsFetchService(settings)
    end = date(2026, 7, 10)
    start, resolved_end = service.date_range(end)
    assert resolved_end == end
    assert start == date(2026, 4, 12)


def test_daily_aggregate_respects_field_dates():
    store = DailyMetricsStore()
    store.add_row("Search campaigns", date(2026, 7, 1), 1_000_000, 1, 10)
    store.add_row("Search campaigns", date(2026, 7, 2), 2_000_000, 2, 20)
    store.add_row("Search campaigns", date(2026, 7, 3), 5_000_000, 5, 50)

    metrics = store.aggregate("Search campaigns", date(2026, 7, 1), date(2026, 7, 2))
    assert metrics.cost == 3.0
    assert metrics.conversions == 3.0


def test_build_analyzer_input_uses_calendar_month_mtd():
    """Spend/MTD achieve = ongoing month; MTD target = (Budget/days)×(T-1)."""
    settings = AppSettings(
        google_ads_developer_token="dev",
        google_ads_client_id="cid",
        google_ads_client_secret="secret",
        google_ads_refresh_token="refresh",
    )
    service = GoogleAdsFetchService(settings)
    # Form dates intentionally different — calendar month should win for MTD.
    form = AnalyzerFormRequest(
        account="1234567890",
        account_start_date=date(2026, 1, 1),
        account_end_date=date(2026, 7, 10),
        search_campaigns=CampaignFieldFormInput(
            label="Search campaigns", budget=310_000, start_date=date(2026, 7, 1), end_date=date(2026, 7, 2)
        ),
        video_campaigns=CampaignFieldFormInput(
            label="Video campaigns", budget=0, start_date=date(2026, 7, 1), end_date=date(2026, 7, 8)
        ),
        demand_gen_campaigns=CampaignFieldFormInput(
            label="Demand Gen campaigns", budget=0, start_date=date(2026, 7, 1), end_date=date(2026, 7, 6)
        ),
        performance_max_campaigns=CampaignFieldFormInput(
            label="Performance Max campaigns", budget=0, start_date=date(2026, 7, 1), end_date=date(2026, 7, 1)
        ),
    )

    today = date(2026, 7, 11)  # T-1 = Jul 10 → 10 days
    month_start = date(2026, 7, 1)

    def mock_fetch(customer_id, start, end):
        store = DailyMetricsStore()
        records = []
        # Ongoing-month fetch: Jul 1 → Jul 11
        if start == month_start and end == today:
            store.add_row("Search campaigns", date(2026, 7, 1), 1_000_000, 1, 10)
            store.add_row("Search campaigns", date(2026, 7, 10), 2_000_000, 2, 20)
            store.add_row("Search campaigns", date(2026, 7, 11), 4_000_000, 1, 5)  # today
            records.append(
                {"Campaign type": "Search campaigns", "Date": "2026-07-10", "Cost": 2.0, "Conversions": 2.0, "Conv. value": 20.0}
            )
        # 7-day window ending T-1 (Jul 4 → Jul 10)
        if start == date(2026, 7, 4) and end == today:
            store.add_row("Search campaigns", date(2026, 7, 9), 700_000, 1, 1)
            store.add_row("Search campaigns", date(2026, 7, 8), 300_000, 1, 1)
            store.add_row("Search campaigns", date(2026, 7, 10), 400_000, 1, 1)
            store.add_row("Search campaigns", date(2026, 7, 11), 100_000, 1, 1)
        return store, records

    with patch.object(service, "fetch_daily_metrics", side_effect=mock_fetch), patch(
        "services.google_ads_fetch_service.reference_t_dates", return_value=(date(2026, 7, 10), date(2026, 7, 9))
    ), patch("services.google_ads_fetch_service.t1_seven_day_window", return_value=(date(2026, 7, 4), date(2026, 7, 10))), patch(
        "services.google_ads_fetch_service.date"
    ) as mock_date:
        mock_date.today.return_value = today
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
        bundle = service.build_analyzer_input_from_form(form)

    search = bundle.form_input.search_campaigns
    # Spend MTD includes today: 1+2+4 = 7
    assert search.cost == 7.0
    # MTD achieve through T-1 only: 1+2 = 3
    assert search.mtd_achieve == 3.0
    # MTD target = (310000 / 31) * 10 = 100000
    assert search.mtd_target == 100_000.0
    assert search.start_date == month_start
    assert search.end_date == date(2026, 7, 31)
