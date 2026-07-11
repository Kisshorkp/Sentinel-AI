"""Campaign-level pre-launch and hygiene threshold checks."""

from __future__ import annotations

from datetime import date, datetime

from config.settings import AppSettings
from models.agent_report import CheckStatus, ThresholdCheck
from models.campaign_daily_snapshot import CampaignDailySnapshotRow, DeletedCampaignInfo
from utils.formatting import format_currency

# Google Ads uses a far-future date when no end date is set.
UNLIMITED_END_DATE = date(2037, 12, 1)


def normalize_end_date(end_date: date | None) -> date | None:
    if end_date is None:
        return None
    if end_date >= UNLIMITED_END_DATE:
        return None
    return end_date


def rolling_last_hours(n: int, now: datetime | None = None) -> list[int]:
    """Clock hours before the current hour (0–23), up to n hours."""
    anchor = now or datetime.now()
    hours: list[int] = []
    for offset in range(1, n + 1):
        hour = anchor.hour - offset
        if hour >= 0:
            hours.append(hour)
    return sorted(hours)


def is_campaign_eligible(primary_status: str) -> bool:
    return primary_status.upper() == "ELIGIBLE"


def format_budget_period(period: str) -> str:
    normalized = (period or "").upper()
    if normalized == "DAILY":
        return "Daily"
    if normalized in {"CUSTOM_PERIOD", "TOTAL", "CAMPAIGN_TOTAL"}:
        return "Total / custom period"
    return period or "Unknown"


def evaluate_start_date_t1(
    row: CampaignDailySnapshotRow,
    t1_date: date,
) -> ThresholdCheck:
    started_yesterday = row.start_date == t1_date
    return ThresholdCheck(
        rule="start_date_t1",
        threshold="start date ≠ T-1",
        actual=str(row.start_date) if row.start_date else "not set",
        status=CheckStatus.WARNING if started_yesterday else CheckStatus.PASS,
        message=(
            f"Campaign started on T-1 ({t1_date}); flag for review before launch."
            if started_yesterday
            else ""
        ),
    )


def evaluate_end_date_null(row: CampaignDailySnapshotRow) -> ThresholdCheck:
    end_date = normalize_end_date(row.end_date)
    is_open_ended = end_date is None
    return ThresholdCheck(
        rule="end_date_null",
        threshold="end date set",
        actual="open-ended (no end date)" if is_open_ended else str(end_date),
        status=CheckStatus.WARNING if is_open_ended else CheckStatus.PASS,
        message="Confirm open-ended campaign is intentional." if is_open_ended else "",
    )


def evaluate_zero_budget(row: CampaignDailySnapshotRow, currency: str) -> ThresholdCheck:
    is_zero = row.budget_amount <= 0
    return ThresholdCheck(
        rule="budget_amount_zero",
        threshold=f"> {format_currency(0, currency)}",
        actual=format_currency(row.budget_amount, currency),
        status=CheckStatus.FAIL if is_zero else CheckStatus.PASS,
        message="Campaign budget is zero." if is_zero else "",
    )


def evaluate_budget_period(row: CampaignDailySnapshotRow) -> ThresholdCheck:
    period_label = format_budget_period(row.budget_period)
    normalized = (row.budget_period or "").upper()
    needs_confirm = not normalized or normalized in {"CUSTOM_PERIOD", "TOTAL", "CAMPAIGN_TOTAL"}
    return ThresholdCheck(
        rule="budget_period_confirm",
        threshold="Daily or Total budget confirmed",
        actual=period_label,
        status=CheckStatus.WARNING if needs_confirm else CheckStatus.PASS,
        message=f"Confirm budget mode: {period_label}." if needs_confirm else "",
    )


def evaluate_new_campaign_budget_deviation(
    row: CampaignDailySnapshotRow,
    t1_date: date,
    type_avg_budget: float | None,
    settings: AppSettings,
) -> ThresholdCheck:
    pct = settings.campaign_new_budget_deviation_pct
    min_delta = settings.campaign_new_budget_min_delta
    currency = settings.app_currency
    threshold_multiplier = 1 + pct / 100

    if row.start_date != t1_date or type_avg_budget is None or type_avg_budget <= 0:
        return ThresholdCheck(
            rule="new_campaign_budget_deviation",
            threshold=(
                f"> {pct}% above type avg and > {format_currency(min_delta, currency)} "
                f"for new campaigns (start = T-1)"
            ),
            actual="not applicable",
            status=CheckStatus.PASS,
        )

    delta = row.budget_amount - type_avg_budget
    pct_above = (delta / type_avg_budget * 100) if type_avg_budget > 0 else 0.0
    triggered = row.budget_amount > type_avg_budget * threshold_multiplier and delta > min_delta

    return ThresholdCheck(
        rule="new_campaign_budget_deviation",
        threshold=(
            f"> {pct}% above type avg and > {format_currency(min_delta, currency)} "
            f"for new campaigns (start = T-1)"
        ),
        actual=(
            f"{format_currency(row.budget_amount, currency)} vs type avg "
            f"{format_currency(type_avg_budget, currency)} ({pct_above:+.1f}%, "
            f"delta {format_currency(delta, currency)})"
        ),
        status=CheckStatus.WARNING if triggered else CheckStatus.PASS,
        message=(
            f"New campaign budget is more than {pct}% above the {row.campaign_type} average "
            f"and exceeds {format_currency(min_delta, currency)}."
            if triggered
            else ""
        ),
    )


def evaluate_eligible_zero_recent_spend(
    row: CampaignDailySnapshotRow,
    settings: AppSettings,
    now: datetime | None = None,
) -> ThresholdCheck:
    hours = settings.campaign_zero_spend_hours
    currency = settings.app_currency
    eligible = is_campaign_eligible(row.primary_status)
    zero_spend = row.last_6h_cost <= 0

    if eligible and zero_spend:
        hour_list = rolling_last_hours(hours, now=now)
        hour_label = ", ".join(str(h) for h in hour_list) if hour_list else "n/a"
        return ThresholdCheck(
            rule="eligible_zero_recent_spend",
            threshold=f"eligible campaign with spend in last {hours} hours",
            actual=f"{format_currency(row.last_6h_cost, currency)} (hours {hour_label})",
            status=CheckStatus.WARNING,
            message=(
                f"Eligible campaign has zero spend in the last {hours} clock hour(s) "
                f"today ({hour_label})."
            ),
        )

    return ThresholdCheck(
        rule="eligible_zero_recent_spend",
        threshold=f"eligible campaign with spend in last {hours} hours",
        actual=(
            f"{format_currency(row.last_6h_cost, currency)}; status {row.primary_status or 'unknown'}"
        ),
        status=CheckStatus.PASS,
    )


def evaluate_end_date_imminent(
    row: CampaignDailySnapshotRow,
    t1_date: date,
    today_date: date,
) -> ThresholdCheck:
    end_date = normalize_end_date(row.end_date)
    if end_date is None:
        return ThresholdCheck(
            rule="end_date_imminent",
            threshold="end date ≠ yesterday or today",
            actual="open-ended",
            status=CheckStatus.PASS,
        )

    ending_soon = end_date in {t1_date, today_date}
    return ThresholdCheck(
        rule="end_date_imminent",
        threshold="end date ≠ yesterday or today",
        actual=str(end_date),
        status=CheckStatus.WARNING if ending_soon else CheckStatus.PASS,
        message=(
            f"Campaign ends on {end_date} (yesterday or today); review and notify stakeholders."
            if ending_soon
            else ""
        ),
    )


def evaluate_deleted_campaigns(
    campaign_type: str,
    deleted: list[DeletedCampaignInfo],
) -> ThresholdCheck | None:
    type_deleted = [item for item in deleted if item.campaign_type == campaign_type]
    if not type_deleted:
        return None

    names = ", ".join(f"{item.campaign_name} ({item.campaign_id})" for item in type_deleted)
    return ThresholdCheck(
        rule="campaign_removed",
        threshold="no campaigns removed since yesterday",
        actual=f"{len(type_deleted)} removed: {names}",
        status=CheckStatus.WARNING,
        message="Campaign ID was present yesterday but is absent today (deleted/removed).",
    )


def evaluate_campaign_daily_row(
    row: CampaignDailySnapshotRow,
    settings: AppSettings,
    *,
    t1_date: date,
    today_date: date,
    type_avg_budget: float | None,
    now: datetime | None = None,
) -> list[ThresholdCheck]:
    currency = settings.app_currency
    return [
        evaluate_start_date_t1(row, t1_date),
        evaluate_end_date_null(row),
        evaluate_zero_budget(row, currency),
        evaluate_budget_period(row),
        evaluate_new_campaign_budget_deviation(row, t1_date, type_avg_budget, settings),
        evaluate_eligible_zero_recent_spend(row, settings, now=now),
        evaluate_end_date_imminent(row, t1_date, today_date),
    ]
