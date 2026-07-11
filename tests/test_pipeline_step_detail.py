"""Tests for pipeline step detail panel."""

from __future__ import annotations

from components.pipeline_step_detail import preview_records


def test_preview_records_returns_latest_unique_rows():
    records = [
        {"Campaign type": "Search campaigns", "Date": "2026-07-01", "Cost": 1.0},
        {"Campaign type": "Search campaigns", "Date": "2026-07-01", "Cost": 1.0},
        {"Campaign type": "Video campaigns", "Date": "2026-07-03", "Cost": 2.0},
        {"Campaign type": "Search campaigns", "Date": "2026-07-02", "Cost": 3.0},
    ]
    preview = preview_records(records, limit=2)
    assert len(preview) == 2
    assert preview[0]["Date"] == "2026-07-03"
    assert preview[1]["Date"] == "2026-07-02"
