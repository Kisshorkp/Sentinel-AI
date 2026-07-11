"""List Google Ads accounts accessible with current credentials."""

from __future__ import annotations

import sys

from clients.google_ads_client import GoogleAdsClientFactory
from config.settings import get_settings


def main() -> int:
    settings = get_settings()
    if settings.google_ads_missing_credentials():
        print("Missing credentials in .env")
        return 1

    client = GoogleAdsClientFactory(settings).create()
    service = client.get_service("CustomerService")
    response = service.list_accessible_customers()
    print("Accessible customer IDs:")
    for resource in response.resource_names:
        customer_id = resource.split("/")[-1]
        formatted = f"{customer_id[:3]}-{customer_id[3:6]}-{customer_id[6:]}"
        print(f"  {formatted}  (raw: {customer_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
