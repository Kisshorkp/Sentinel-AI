"""Google Ads API client factory."""

from __future__ import annotations

from typing import Any

from config.settings import AppSettings


class GoogleAdsClientFactory:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def create(self) -> Any:
        missing = self.settings.google_ads_missing_credentials()
        if missing:
            raise ValueError(
                "Google Ads API credentials are incomplete. Missing: "
                + ", ".join(missing)
            )

        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError as exc:
            raise ImportError(
                "google-ads package is not installed. Run: pip install google-ads"
            ) from exc

        config: dict[str, str | bool] = {
            "developer_token": self.settings.google_ads_developer_token,
            "client_id": self.settings.google_ads_client_id,
            "client_secret": self.settings.google_ads_client_secret,
            "refresh_token": self.settings.google_ads_refresh_token,
            "use_proto_plus": True,
        }
        if self.settings.google_ads_login_customer_id.strip():
            config["login_customer_id"] = _normalize_customer_id(
                self.settings.google_ads_login_customer_id
            )

        return GoogleAdsClient.load_from_dict(config)


def _normalize_customer_id(customer_id: str) -> str:
    return customer_id.replace("-", "").strip()
