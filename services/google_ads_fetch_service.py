"""Fetch Google Ads spend data for the campaign analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from clients.google_ads_client import GoogleAdsClientFactory, _normalize_customer_id
from config.settings import AppSettings
from models.analyzer_input import AnalyzerFormInput, CampaignFieldInput, resolve_fetch_end_date
from utils.mtd_metrics import (
    calculate_calendar_mtd_target,
    calculate_t1_seven_day_average,
    reference_t_dates,
    t1_seven_day_window,
)
from utils.daily_spend_checks import iter_days_inclusive

import calendar

CHANNEL_TO_LABEL: dict[str, str] = {
    "SEARCH": "Search campaigns",
    "VIDEO": "Video campaigns",
    "DEMAND_GEN": "Demand Gen campaigns",
    "PERFORMANCE_MAX": "Performance Max campaigns",
}

ANALYZER_LABELS = list(CHANNEL_TO_LABEL.values())

GoogleAdsRawRecord = dict[str, Any]


@dataclass
class AnalyzerFetchResult:
    """Google Ads fetch output plus raw API rows for pipeline preview."""

    form_input: AnalyzerFormInput
    raw_records: list[GoogleAdsRawRecord] = field(default_factory=list)

GAQL_DAILY_METRICS = """
    SELECT
      campaign.advertising_channel_type,
      segments.date,
      metrics.cost_micros,
      metrics.conversions,
      metrics.conversions_value
    FROM campaign
    WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
      AND campaign.status != 'REMOVED'
"""

GAQL_HOURLY_METRICS = """
    SELECT
      campaign.advertising_channel_type,
      segments.date,
      segments.hour,
      metrics.cost_micros
    FROM campaign
    WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
      AND campaign.status != 'REMOVED'
"""


@dataclass
class ChannelMetrics:
    cost: float = 0.0
    converted_cost: float = 0.0
    conversions: float = 0.0
    conversions_value: float = 0.0


@dataclass
class DailyMetricsStore:
    """Daily metrics keyed by campaign label then date."""

    daily: dict[str, dict[date, ChannelMetrics]] = field(default_factory=dict)

    def add_row(
        self,
        label: str,
        day: date,
        cost_micros: int,
        conversions: float,
        conversions_value: float,
    ) -> None:
        bucket = self.daily.setdefault(label, {}).setdefault(day, ChannelMetrics())
        cost = round(bucket.cost + _micros_to_units(cost_micros), 2)
        bucket.cost = cost
        bucket.converted_cost = cost
        bucket.conversions = round(bucket.conversions + conversions, 2)
        bucket.conversions_value = round(bucket.conversions_value + conversions_value, 2)

    def aggregate(self, label: str, start_date: date, end_date: date) -> ChannelMetrics:
        total = ChannelMetrics()
        for day, metrics in self.daily.get(label, {}).items():
            if start_date <= day <= end_date:
                total.cost = round(total.cost + metrics.cost, 2)
                total.converted_cost = round(total.converted_cost + metrics.converted_cost, 2)
                total.conversions = round(total.conversions + metrics.conversions, 2)
                total.conversions_value = round(total.conversions_value + metrics.conversions_value, 2)
        return total

    def day_cost(self, label: str, day: date) -> float:
        return self.daily.get(label, {}).get(day, ChannelMetrics()).cost


@dataclass
class HourlyMetricsStore:
    """Hourly cost keyed by campaign label, date, then hour (0-23)."""

    hourly: dict[str, dict[date, dict[int, float]]] = field(default_factory=dict)

    def add_row(self, label: str, day: date, hour: int, cost_micros: int) -> None:
        bucket = self.hourly.setdefault(label, {}).setdefault(day, {})
        bucket[hour] = round(bucket.get(hour, 0.0) + _micros_to_units(cost_micros), 2)

    def hour_cost(self, label: str, day: date, hour: int) -> float:
        return self.hourly.get(label, {}).get(day, {}).get(hour, 0.0)

    def hour_seven_day_average(
        self, label: str, hour: int, window_start: date, window_end: date
    ) -> float:
        total = 0.0
        day = window_start
        days = 0
        while day <= window_end:
            total += self.hour_cost(label, day, hour)
            days += 1
            day += timedelta(days=1)
        if days <= 0:
            return 0.0
        return round(total / days, 2)


def build_hourly_snapshot_rows(
    store: HourlyMetricsStore,
    label: str,
    t1_date: date,
    t2_date: date,
    today_date: date,
    avg_window_start: date,
    avg_window_end: date,
) -> list[dict[str, object]]:
    """Build 24 hourly rows (hours 0–23) for one campaign type."""
    t1_label = t1_date.isoformat()
    t2_label = t2_date.isoformat()
    rows: list[dict[str, object]] = []
    for hour in range(0, 24):
        rows.append(
            {
                "Hour": hour,
                t2_label: store.hour_cost(label, t2_date, hour),
                t1_label: store.hour_cost(label, t1_date, hour),
                "Today's cost": store.hour_cost(label, today_date, hour),
                "T-1 7-day avg cost": store.hour_seven_day_average(
                    label, hour, avg_window_start, avg_window_end
                ),
            }
        )
    return rows


def _record_from_row(label: str, day: date, cost_micros: int, conversions: float, conversions_value: float) -> GoogleAdsRawRecord:
    return {
        "Campaign type": label,
        "Date": day.isoformat(),
        "Cost": round(_micros_to_units(cost_micros), 2),
        "Conversions": round(conversions, 2),
        "Conv. value": round(conversions_value, 2),
    }



def _micros_to_units(value: int | float) -> float:
    return float(value) / 1_000_000


def _parse_segment_date(value) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


class GoogleAdsFetchService:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.client_factory = GoogleAdsClientFactory(settings)

    def resolve_customer_id(self, account: str) -> str:
        candidate = account.strip() or self.settings.google_ads_customer_id.strip()
        if not candidate:
            raise ValueError(
                "Google Ads customer ID is required. Enter it in the Account field "
                "or set GOOGLE_ADS_CUSTOMER_ID in .env."
            )
        return _normalize_customer_id(candidate)

    def date_range(self, end_date: date) -> tuple[date, date]:
        lookback = max(self.settings.google_ads_lookback_days, 1)
        start_date = end_date - timedelta(days=lookback - 1)
        return start_date, end_date

    def fetch_daily_metrics(
        self, customer_id: str, start_date: date, end_date: date
    ) -> tuple[DailyMetricsStore, list[GoogleAdsRawRecord]]:
        client = self.client_factory.create()
        ga_service = client.get_service("GoogleAdsService")
        query = GAQL_DAILY_METRICS.format(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        store = DailyMetricsStore()
        records: list[GoogleAdsRawRecord] = []
        stream = ga_service.search_stream(customer_id=customer_id, query=query)

        for batch in stream:
            for row in batch.results:
                channel = row.campaign.advertising_channel_type.name
                label = CHANNEL_TO_LABEL.get(channel)
                if not label:
                    continue
                day = _parse_segment_date(row.segments.date)
                store.add_row(
                    label,
                    day,
                    row.metrics.cost_micros,
                    row.metrics.conversions,
                    row.metrics.conversions_value,
                )
                records.append(
                    _record_from_row(
                        label,
                        day,
                        row.metrics.cost_micros,
                        row.metrics.conversions,
                        row.metrics.conversions_value,
                    )
                )

        return store, records

    def fetch_hourly_metrics(
        self, customer_id: str, start_date: date, end_date: date
    ) -> HourlyMetricsStore:
        client = self.client_factory.create()
        ga_service = client.get_service("GoogleAdsService")
        query = GAQL_HOURLY_METRICS.format(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        store = HourlyMetricsStore()
        stream = ga_service.search_stream(customer_id=customer_id, query=query)

        for batch in stream:
            for row in batch.results:
                channel = row.campaign.advertising_channel_type.name
                label = CHANNEL_TO_LABEL.get(channel)
                if not label:
                    continue
                day = _parse_segment_date(row.segments.date)
                store.add_row(label, day, int(row.segments.hour), row.metrics.cost_micros)

        return store

    def fetch_channel_metrics_for_range(
        self, customer_id: str, start_date: date, end_date: date
    ) -> dict[str, ChannelMetrics]:
        """Fetch and aggregate metrics per channel for an exact date range."""
        store, _records = self.fetch_daily_metrics(customer_id, start_date, end_date)
        return {label: store.aggregate(label, start_date, end_date) for label in ANALYZER_LABELS}

    def build_analyzer_input_from_form(self, form) -> AnalyzerFetchResult:
        """Build analyzer input.

        Spend + MTD achieve use the **ongoing calendar month**.
        MTD target = (Budget / days_in_month) × (T − 1).
        """
        fetch_end = resolve_fetch_end_date(form)
        customer_id = self.resolve_customer_id(form.account)
        fetch_start, fetch_end = self.date_range(fetch_end)

        form_by_label = {f.label: f for f in form.campaign_field_forms}
        raw_records: list[GoogleAdsRawRecord] = []

        today_date = date.today()
        month_start = today_date.replace(day=1)
        month_end = today_date.replace(
            day=calendar.monthrange(today_date.year, today_date.month)[1]
        )
        t1_date, t2_date = reference_t_dates(today_date)
        avg_window_start, avg_window_end = t1_seven_day_window(today_date)

        # Ongoing-month spend window (month start → today)
        mtd_store, mtd_records = self.fetch_daily_metrics(customer_id, month_start, today_date)
        raw_records.extend(mtd_records)

        recent_store, recent_records = self.fetch_daily_metrics(
            customer_id, avg_window_start, max(avg_window_end, today_date)
        )
        raw_records.extend(recent_records)

        def field(label: str) -> CampaignFieldInput:
            user = form_by_label[label]
            # Spend = cost in the ongoing month through today
            metrics = mtd_store.aggregate(label, month_start, today_date)

            # MTD achieve = ongoing month through T-1 (yesterday)
            if t1_date >= month_start:
                mtd_achieve_end = t1_date
                mtd_achieve = mtd_store.aggregate(label, month_start, t1_date).cost
            else:
                mtd_achieve_end = None
                mtd_achieve = 0.0

            # MTD Target = (Budget / days_in_month) × (T − 1)
            mtd_target = calculate_calendar_mtd_target(user.budget, today_date)

            seven_day_total = recent_store.aggregate(label, avg_window_start, avg_window_end).cost
            recent_daily_costs = [
                recent_store.day_cost(label, day)
                for day in iter_days_inclusive(avg_window_start, avg_window_end)
            ]

            return CampaignFieldInput(
                label=label,
                budget=user.budget,
                cost=metrics.cost,
                converted_cost=metrics.converted_cost,
                conversions=metrics.conversions,
                conversions_value=metrics.conversions_value,
                mtd_achieve=mtd_achieve,
                mtd_target=mtd_target,
                mtd_achieve_end=mtd_achieve_end,
                t1_date=t1_date,
                t1_cost=recent_store.day_cost(label, t1_date),
                t2_date=t2_date,
                t2_cost=recent_store.day_cost(label, t2_date),
                t1_7day_avg_cost=calculate_t1_seven_day_average(seven_day_total),
                recent_daily_costs=recent_daily_costs,
                today_date=today_date,
                today_cost=recent_store.day_cost(label, today_date),
                start_date=month_start,
                end_date=month_end,
            )

        form_input = AnalyzerFormInput(
            account=customer_id,
            account_start_date=month_start,
            account_end_date=month_end,
            fetch_start_date=fetch_start,
            fetch_end_date=fetch_end,
            search_campaigns=field("Search campaigns"),
            video_campaigns=field("Video campaigns"),
            demand_gen_campaigns=field("Demand Gen campaigns"),
            performance_max_campaigns=field("Performance Max campaigns"),
            data_source="google_ads",
        )
        return AnalyzerFetchResult(form_input=form_input, raw_records=raw_records)
