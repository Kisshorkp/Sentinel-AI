"""Quick Google Ads API connection test."""

from __future__ import annotations

import sys
from datetime import date, timedelta

from config.settings import get_settings
from services.google_ads_fetch_service import GoogleAdsFetchService


def main() -> int:
    settings = get_settings()
    missing = settings.google_ads_missing_credentials()
    if missing:
        print("Missing:", ", ".join(missing))
        return 1

    service = GoogleAdsFetchService(settings)
    customer_id = service.resolve_customer_id(settings.google_ads_customer_id)
    end = date.today()
    start, end = service.date_range(end)

    print(f"Testing customer {customer_id} from {start} to {end}...")
    try:
        metrics = service.fetch_metrics_by_channel(customer_id, start, end)
        for label, data in metrics.items():
            if data.cost > 0 or data.converted_cost > 0:
                print(
                    f"  {label}: cost={data.cost}, converted_cost={data.converted_cost}, "
                    f"conversions={data.conversions}"
                )
        total = sum(item.cost for item in metrics.values())
        print(f"OK — total cost fetched: {total:.2f}")
        return 0
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
