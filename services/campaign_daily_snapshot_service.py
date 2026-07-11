"""Fetch and build campaign-level daily spend snapshot (grouped by campaign type)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from clients.google_ads_client import GoogleAdsClientFactory
from config.settings import AppSettings
from models.campaign_daily_snapshot import (
    CampaignDailyHygieneContext,
    CampaignDailySnapshotBundle,
    CampaignDailySnapshotRow,
    DeletedCampaignInfo,
)
from services.google_ads_fetch_service import CHANNEL_TO_LABEL, ANALYZER_LABELS
from utils.campaign_level_checks import rolling_last_hours
from utils.daily_spend_checks import iter_days_inclusive
from utils.mtd_metrics import (
    calculate_t1_seven_day_average,
    reference_t_dates,
    t1_seven_day_window,
)

GAQL_CAMPAIGN_DAILY_METRICS = """
    SELECT
      campaign.id,
      campaign.name,
      campaign.advertising_channel_type,
      segments.date,
      metrics.cost_micros
    FROM campaign
    WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
      AND campaign.status != 'REMOVED'
"""

GAQL_CAMPAIGN_METADATA = """
    SELECT
      campaign.id,
      campaign.name,
      campaign.advertising_channel_type,
      campaign.start_date_time,
      campaign.end_date_time,
      campaign.primary_status,
      campaign_budget.amount_micros,
      campaign_budget.period
    FROM campaign
    WHERE campaign.status != 'REMOVED'
"""

# Fallback when the Ads API version does not expose start/end date-time fields.
GAQL_CAMPAIGN_METADATA_MIN = """
    SELECT
      campaign.id,
      campaign.name,
      campaign.advertising_channel_type,
      campaign.primary_status,
      campaign_budget.amount_micros,
      campaign_budget.period
    FROM campaign
    WHERE campaign.status != 'REMOVED'
"""

GAQL_CAMPAIGN_HOURLY_TODAY = """
    SELECT
      campaign.id,
      segments.hour,
      metrics.cost_micros
    FROM campaign
    WHERE segments.date = '{today_date}'
      AND campaign.status != 'REMOVED'
"""


def _micros_to_units(value: int | float) -> float:
    return float(value) / 1_000_000


def _parse_segment_date(value) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _parse_campaign_date(value) -> date | None:
    """Parse campaign.start_date_time / end_date_time (date or yyyy-MM-dd HH:mm:ss)."""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if " " in text:
        text = text.split(" ", 1)[0]
    return date.fromisoformat(text)


@dataclass
class CampaignMeta:
    campaign_name: str
    campaign_type: str
    start_date: date | None = None
    end_date: date | None = None
    budget_amount: float = 0.0
    budget_period: str = ""
    primary_status: str = ""


@dataclass
class CampaignDailyMetricsStore:
    """Daily cost keyed by campaign id, with name and channel type metadata."""

    campaigns: dict[str, dict[str, object]] = field(default_factory=dict)
    daily: dict[str, dict[date, float]] = field(default_factory=dict)

    def add_row(
        self,
        campaign_id: str,
        campaign_name: str,
        campaign_type: str,
        day: date,
        cost_micros: int,
    ) -> None:
        self.campaigns[campaign_id] = {
            "campaign_name": campaign_name,
            "campaign_type": campaign_type,
        }
        bucket = self.daily.setdefault(campaign_id, {})
        bucket[day] = round(bucket.get(day, 0.0) + _micros_to_units(cost_micros), 2)

    def day_cost(self, campaign_id: str, day: date) -> float:
        return self.daily.get(campaign_id, {}).get(day, 0.0)

    def aggregate_cost(self, campaign_id: str, start_date: date, end_date: date) -> float:
        total = 0.0
        for day, cost in self.daily.get(campaign_id, {}).items():
            if start_date <= day <= end_date:
                total = round(total + cost, 2)
        return total

    def campaign_ids_on_date(self, day: date) -> set[str]:
        return {campaign_id for campaign_id, days in self.daily.items() if day in days}


def build_campaign_daily_snapshot_rows(
    store: CampaignDailyMetricsStore,
    metadata: dict[str, CampaignMeta],
    hourly_costs: dict[str, float],
    t1_date: date,
    t2_date: date,
    today_date: date,
    avg_window_start: date,
    avg_window_end: date,
) -> tuple[list[CampaignDailySnapshotRow], list[DeletedCampaignInfo]]:
    """Build snapshot rows for all campaigns, ordered by campaign type then name."""
    rows: list[CampaignDailySnapshotRow] = []
    type_order = {label: idx for idx, label in enumerate(ANALYZER_LABELS)}
    all_campaign_ids = set(store.campaigns) | set(metadata)

    yesterday_ids = store.campaign_ids_on_date(t1_date)
    today_ids = set(metadata)
    deleted: list[DeletedCampaignInfo] = []
    for campaign_id in sorted(yesterday_ids - today_ids):
        meta = store.campaigns.get(campaign_id, {})
        campaign_type = str(meta.get("campaign_type", ""))
        if campaign_type not in type_order:
            continue
        deleted.append(
            DeletedCampaignInfo(
                campaign_type=campaign_type,
                campaign_id=campaign_id,
                campaign_name=str(meta.get("campaign_name", campaign_id)),
            )
        )

    for campaign_id in all_campaign_ids:
        meta = metadata.get(campaign_id)
        store_meta = store.campaigns.get(campaign_id, {})
        campaign_type = (meta.campaign_type if meta else str(store_meta.get("campaign_type", "")))
        if campaign_type not in type_order:
            continue

        campaign_name = meta.campaign_name if meta else str(store_meta.get("campaign_name", campaign_id))
        seven_day_total = store.aggregate_cost(campaign_id, avg_window_start, avg_window_end)
        rows.append(
            CampaignDailySnapshotRow(
                campaign_type=campaign_type,
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                t1_date=t1_date,
                t1_cost=store.day_cost(campaign_id, t1_date),
                t2_date=t2_date,
                t2_cost=store.day_cost(campaign_id, t2_date),
                today_date=today_date,
                today_cost=store.day_cost(campaign_id, today_date),
                t1_7day_avg_cost=calculate_t1_seven_day_average(seven_day_total),
                recent_daily_costs=[
                    store.day_cost(campaign_id, day)
                    for day in iter_days_inclusive(avg_window_start, avg_window_end)
                ],
                start_date=meta.start_date if meta else None,
                end_date=meta.end_date if meta else None,
                budget_amount=meta.budget_amount if meta else 0.0,
                budget_period=meta.budget_period if meta else "",
                primary_status=meta.primary_status if meta else "",
                last_6h_cost=hourly_costs.get(campaign_id, 0.0),
            )
        )

    rows.sort(key=lambda row: (type_order[row.campaign_type], row.campaign_name.lower()))
    return rows, deleted


class CampaignDailySnapshotService:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.client_factory = GoogleAdsClientFactory(settings)

    def fetch_store(self, customer_id: str, start_date: date, end_date: date) -> CampaignDailyMetricsStore:
        client = self.client_factory.create()
        ga_service = client.get_service("GoogleAdsService")
        query = GAQL_CAMPAIGN_DAILY_METRICS.format(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        store = CampaignDailyMetricsStore()
        stream = ga_service.search_stream(customer_id=customer_id, query=query)

        for batch in stream:
            for row in batch.results:
                channel = row.campaign.advertising_channel_type.name
                campaign_type = CHANNEL_TO_LABEL.get(channel)
                if not campaign_type:
                    continue
                campaign_id = str(row.campaign.id)
                store.add_row(
                    campaign_id,
                    row.campaign.name,
                    campaign_type,
                    _parse_segment_date(row.segments.date),
                    row.metrics.cost_micros,
                )
        return store

    def fetch_metadata(self, customer_id: str) -> dict[str, CampaignMeta]:
        client = self.client_factory.create()
        ga_service = client.get_service("GoogleAdsService")
        metadata: dict[str, CampaignMeta] = {}

        def _ingest(stream, *, include_dates: bool) -> None:
            for batch in stream:
                for row in batch.results:
                    channel = row.campaign.advertising_channel_type.name
                    campaign_type = CHANNEL_TO_LABEL.get(channel)
                    if not campaign_type:
                        continue
                    campaign_id = str(row.campaign.id)
                    start_date = (
                        _parse_campaign_date(row.campaign.start_date_time) if include_dates else None
                    )
                    end_date = (
                        _parse_campaign_date(row.campaign.end_date_time) if include_dates else None
                    )
                    metadata[campaign_id] = CampaignMeta(
                        campaign_name=row.campaign.name,
                        campaign_type=campaign_type,
                        start_date=start_date,
                        end_date=end_date,
                        budget_amount=_micros_to_units(row.campaign_budget.amount_micros),
                        budget_period=row.campaign_budget.period.name,
                        primary_status=row.campaign.primary_status.name,
                    )

        try:
            stream = ga_service.search_stream(customer_id=customer_id, query=GAQL_CAMPAIGN_METADATA)
            _ingest(stream, include_dates=True)
        except Exception:
            # Older/newer API field mismatches (start_date vs start_date_time) — retry without dates.
            stream = ga_service.search_stream(
                customer_id=customer_id, query=GAQL_CAMPAIGN_METADATA_MIN
            )
            _ingest(stream, include_dates=False)
        return metadata

    def fetch_last_hours_spend(
        self,
        customer_id: str,
        today_date: date,
        hours: int,
        now: datetime | None = None,
    ) -> dict[str, float]:
        client = self.client_factory.create()
        ga_service = client.get_service("GoogleAdsService")
        query = GAQL_CAMPAIGN_HOURLY_TODAY.format(today_date=today_date.isoformat())
        target_hours = set(rolling_last_hours(hours, now=now))
        totals: dict[str, float] = {}

        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in stream:
            for row in batch.results:
                hour = int(row.segments.hour)
                if target_hours and hour not in target_hours:
                    continue
                campaign_id = str(row.campaign.id)
                totals[campaign_id] = round(
                    totals.get(campaign_id, 0.0) + _micros_to_units(row.metrics.cost_micros),
                    2,
                )
        return totals

    def fetch_snapshot(self, customer_id: str) -> CampaignDailySnapshotBundle:
        t1_date, t2_date = reference_t_dates()
        today_date = date.today()
        avg_window_start, avg_window_end = t1_seven_day_window()
        fetch_start = min(avg_window_start, t2_date)
        fetch_end = max(avg_window_end, today_date)

        store = self.fetch_store(customer_id, fetch_start, fetch_end)
        metadata = self.fetch_metadata(customer_id)
        hourly_costs = self.fetch_last_hours_spend(
            customer_id,
            today_date,
            self.settings.campaign_zero_spend_hours,
        )
        rows, deleted = build_campaign_daily_snapshot_rows(
            store,
            metadata,
            hourly_costs,
            t1_date,
            t2_date,
            today_date,
            avg_window_start,
            avg_window_end,
        )
        return CampaignDailySnapshotBundle(
            rows=rows,
            hygiene=CampaignDailyHygieneContext(
                deleted_campaigns=deleted,
                t1_date=t1_date,
                today_date=today_date,
            ),
        )
