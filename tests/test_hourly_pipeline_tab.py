"""Tests for hourly pipeline tab."""

from __future__ import annotations

from unittest.mock import patch

from components.hourly_pipeline_tab import _build_hourly_overview_rows, _hourly_display_columns


@patch("components.hourly_pipeline_tab.current_display_hour", return_value=12)
def test_build_hourly_overview_rows_includes_variance(_mock_hour):
    hourly_by_label = {
        "Search campaigns": [
            {"Hour": 12, "Today's cost": 120.0, "T-1 7-day avg cost": 100.0},
        ],
        "Video campaigns": [
            {"Hour": 12, "Today's cost": 50.0, "T-1 7-day avg cost": 40.0},
        ],
    }

    rows, display_hour = _build_hourly_overview_rows(hourly_by_label)

    assert display_hour == 12
    assert len(rows) == 2
    assert rows[0]["Campaign type"] == "Search"
    assert rows[0]["Vs 7-day avg"] == 20.0


def test_hourly_display_columns_swaps_t1_and_t2_dates():
    columns = ["Hour", "2026-07-10", "2026-07-09", "Today's cost", "T-1 7-day avg cost"]
    assert _hourly_display_columns(columns) == [
        "Hour",
        "2026-07-09",
        "2026-07-10",
        "Today's cost",
        "T-1 7-day avg cost",
    ]


def test_normalize_hourly_rows_reorders_cached_data():
    from components.hourly_pipeline_tab import _normalize_hourly_rows

    rows = [
        {
            "Hour": 0,
            "2026-07-10": 10.0,
            "2026-07-09": 5.0,
            "Today's cost": 1.0,
            "T-1 7-day avg cost": 2.0,
        }
    ]
    normalized = _normalize_hourly_rows(rows)
    assert list(normalized[0].keys()) == [
        "Hour",
        "2026-07-09",
        "2026-07-10",
        "Today's cost",
        "T-1 7-day avg cost",
    ]
