"""Tests for hourly metrics store."""

from __future__ import annotations

from datetime import date

from services.google_ads_fetch_service import HourlyMetricsStore, build_hourly_snapshot_rows


def test_build_hourly_snapshot_rows():
    store = HourlyMetricsStore()
    t1 = date(2026, 7, 9)
    t2 = date(2026, 7, 8)
    today = date(2026, 7, 10)
    avg_start = date(2026, 7, 3)
    avg_end = date(2026, 7, 9)
    label = "Search campaigns"

    store.add_row(label, t1, 9, 1_000_000)
    store.add_row(label, t2, 9, 500_000)
    store.add_row(label, today, 9, 250_000)
    day = avg_start
    while day <= avg_end:
        if day not in {t1, t2}:
            store.add_row(label, day, 9, 700_000)
        day = date.fromordinal(day.toordinal() + 1)

    rows = build_hourly_snapshot_rows(store, label, t1, t2, today, avg_start, avg_end)
    assert len(rows) == 24
    assert rows[9]["Hour"] == 9
    assert rows[9][t1.isoformat()] == 1.0
    assert rows[9][t2.isoformat()] == 0.5
    assert rows[9]["Today's cost"] == 0.25
    assert rows[9]["T-1 7-day avg cost"] == round((1.0 + 0.5 + 0.7 * 5) / 7, 2)
