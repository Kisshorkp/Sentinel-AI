"""Tests for campaign daily snapshot GAQL helpers."""

from datetime import date

from services.campaign_daily_snapshot_service import _parse_campaign_date


def test_parse_campaign_date_iso_date():
    assert _parse_campaign_date("2026-06-30") == date(2026, 6, 30)


def test_parse_campaign_date_datetime_string():
    assert _parse_campaign_date("2026-06-30 00:00:00") == date(2026, 6, 30)


def test_parse_campaign_date_empty():
    assert _parse_campaign_date(None) is None
    assert _parse_campaign_date("") is None
