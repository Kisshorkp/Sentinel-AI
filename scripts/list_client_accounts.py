"""List client accounts under a Google Ads manager (MCC) account."""

from __future__ import annotations

import sys

from clients.google_ads_client import GoogleAdsClientFactory, _normalize_customer_id
from config.settings import get_settings

GAQL_CLIENT_ACCOUNTS = """
    SELECT
      customer_client.client_customer,
      customer_client.descriptive_name,
      customer_client.manager,
      customer_client.status
    FROM customer_client
    WHERE customer_client.level <= 1
      AND customer_client.status = 'ENABLED'
"""


def main() -> int:
    settings = get_settings()
    login_id = _normalize_customer_id(settings.google_ads_login_customer_id or settings.google_ads_customer_id)
    client = GoogleAdsClientFactory(settings).create()
    ga_service = client.get_service("GoogleAdsService")
    stream = ga_service.search_stream(customer_id=login_id, query=GAQL_CLIENT_ACCOUNTS)

    print(f"Client accounts under manager {login_id}:")
    for batch in stream:
        for row in batch.results:
            cc = row.customer_client
            if cc.manager:
                continue
            cid = cc.client_customer.split("/")[-1]
            formatted = f"{cid[:3]}-{cid[3:6]}-{cid[6:]}"
            print(f"  {formatted}  {cc.descriptive_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
