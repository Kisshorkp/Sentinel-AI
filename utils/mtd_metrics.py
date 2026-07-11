"""MTD achieve date logic (T-1 relative to each field's selected end date)."""

from __future__ import annotations

import calendar
from datetime import date, timedelta


RECENT_AVG_DAYS = 7


def reference_t_dates(today: date | None = None) -> tuple[date, date]:
    """T-1 (yesterday) and T-2 (day before yesterday) relative to today."""
    anchor = today or date.today()
    return anchor - timedelta(days=1), anchor - timedelta(days=2)


def t1_seven_day_window(today: date | None = None) -> tuple[date, date]:
    """Seven-day window ending on T-1 (inclusive)."""
    t1, _ = reference_t_dates(today)
    return t1 - timedelta(days=RECENT_AVG_DAYS - 1), t1


def calculate_t1_seven_day_average(total_cost: float) -> float:
    return round(total_cost / RECENT_AVG_DAYS, 2)


def achieve_end_date(
    field_start: date, field_end: date, today: date | None = None
) -> date | None:
    """
    Last date included in MTD achieve for a field (uses the user's date filter).

    - If end date is today or later: use yesterday (today - 1).
    - If end date is before today: keep the user's end date as-is.

    Returns None when the effective end falls before the field start date.
    """
    anchor = today or date.today()
    if field_end >= anchor:
        achieve_end = anchor - timedelta(days=1)
    else:
        achieve_end = field_end

    if achieve_end < field_start:
        return None
    return achieve_end


def calculate_mtd_target(
    budget: float,
    field_start: date,
    field_end: date,
    achieve_end: date | None,
) -> float:
    """
    Prorate the user's budget day-wise across start/end dates, then sum through achieve_end.

    Example: budget 5000 for Jul 1–10 (10 days) → ₹500/day; through Jul 9 → ₹4500 target.
    """
    if achieve_end is None or budget <= 0:
        return 0.0

    total_days = (field_end - field_start).days + 1
    if total_days <= 0:
        return 0.0

    achieve_days = (achieve_end - field_start).days + 1
    if achieve_days <= 0:
        return 0.0

    daily_budget = budget / total_days
    return round(daily_budget * achieve_days, 2)


def calculate_calendar_mtd_target(budget: float, today: date | None = None) -> float:
    """
    Dashboard platform pacing target for the calendar month:

        MTD Target = (Budget / Number of days of the month) × (T − 1)

    T = today's day-of-month; (T − 1) = days elapsed through yesterday.
    Example: budget 3,10,000 in July (31 days), today = 11 → (310000/31)×10 = 1,00,000.
    """
    anchor = today or date.today()
    days_in_month = calendar.monthrange(anchor.year, anchor.month)[1]
    t_minus_1 = max(anchor.day - 1, 0)
    if budget <= 0 or days_in_month <= 0 or t_minus_1 <= 0:
        return 0.0
    return round((budget / days_in_month) * t_minus_1, 2)
