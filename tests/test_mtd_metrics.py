"""Tests for MTD achieve calculations."""

from __future__ import annotations

from datetime import date

from utils.mtd_metrics import (
    achieve_end_date,
    calculate_calendar_mtd_target,
    calculate_mtd_target,
    calculate_t1_seven_day_average,
    reference_t_dates,
    t1_seven_day_window,
)


def test_achieve_end_when_end_date_is_today():
    assert achieve_end_date(date(2026, 7, 1), date(2026, 7, 10), today=date(2026, 7, 10)) == date(
        2026, 7, 9
    )


def test_achieve_end_when_end_date_is_in_past():
    assert achieve_end_date(date(2026, 7, 1), date(2026, 7, 9), today=date(2026, 7, 10)) == date(
        2026, 7, 9
    )


def test_achieve_end_when_end_date_is_in_future():
    assert achieve_end_date(date(2026, 7, 1), date(2026, 7, 31), today=date(2026, 7, 10)) == date(
        2026, 7, 9
    )


def test_achieve_end_none_when_t_minus_one_before_start():
    assert achieve_end_date(date(2026, 7, 10), date(2026, 7, 10), today=date(2026, 7, 10)) is None


def test_mtd_target_prorates_daywise_budget():
    target = calculate_mtd_target(5000, date(2026, 7, 1), date(2026, 7, 10), date(2026, 7, 9))
    assert target == 4500.0


def test_calendar_mtd_target_budget_over_days_times_t_minus_1():
    # July has 31 days; today=11 → T-1=10
    # (310000 / 31) * 10 = 100000
    assert calculate_calendar_mtd_target(310000, today=date(2026, 7, 11)) == 100000.0


def test_calendar_mtd_target_day_one_is_zero():
    assert calculate_calendar_mtd_target(310000, today=date(2026, 7, 1)) == 0.0


def test_reference_t_dates():
    t1, t2 = reference_t_dates(today=date(2026, 7, 10))
    assert t1 == date(2026, 7, 9)
    assert t2 == date(2026, 7, 8)


def test_t1_seven_day_window():
    start, end = t1_seven_day_window(today=date(2026, 7, 10))
    assert start == date(2026, 7, 3)
    assert end == date(2026, 7, 9)


def test_calculate_t1_seven_day_average():
    assert calculate_t1_seven_day_average(7000) == 1000.0
