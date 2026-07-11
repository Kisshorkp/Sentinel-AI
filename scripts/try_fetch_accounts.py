"""Try Google Ads fetch with optional login customer ID override."""

from __future__ import annotations

import os
import sys
from datetime import date

from config.settings import get_settings
from services.google_ads_fetch_service import GoogleAdsFetchService


def try_fetch(customer_id: str, login_customer_id: str = "") -> None:
    settings = get_settings()
    if login_customer_id:
        os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"] = login_customer_id
        settings = get_settings()

    service = GoogleAdsFetchService(settings)
    end = date.today()
    start, end = service.date_range(end)
    metrics = service.fetch_metrics_by_channel(customer_id, start, end)
    total = sum(v.cost for v in metrics.values())
    print(f"OK customer={customer_id} login={login_customer_id or '(none)'} total={total:.2f}")
    for label, data in metrics.items():
        if data.cost > 0:
            print(f"  {label}: cost={data.cost}, conv={data.conversions}, value={data.conversions_value}")


if __name__ == "__main__":
    attempts = [
        ("4933684198", ""),
        ("2065016284", ""),
        ("4657936931", "4933684198"),
        ("4657936931", "2065016284"),
    ]
    for cid, login in attempts:
        print(f"--- trying client={cid} login={login or 'none'} ---")
        try:
            try_fetch(cid, login)
        except Exception as exc:
            print(f"FAIL: {str(exc)[:180]}")
