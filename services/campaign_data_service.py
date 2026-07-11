"""Campaign data loading service."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from config.settings import AppSettings, DataSource
from models.campaign import CampaignSpend


class CampaignDataService:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def load_campaigns(self) -> list[CampaignSpend]:
        if self.settings.data_source == DataSource.CSV:
            return self._load_from_csv(self.settings.csv_path)
        return self._load_from_csv(self.settings.csv_path)

    def _load_from_csv(self, path: Path) -> list[CampaignSpend]:
        if not path.exists():
            raise FileNotFoundError(f"Campaign data file not found: {path}")

        df = pd.read_csv(path)
        campaigns: list[CampaignSpend] = []
        for row in df.to_dict(orient="records"):
            last_updated = row.get("last_updated")
            if isinstance(last_updated, str):
                last_updated = date.fromisoformat(last_updated)
            campaigns.append(
                CampaignSpend(
                    campaign_id=str(row["campaign_id"]),
                    campaign_name=str(row["campaign_name"]),
                    platform=str(row.get("platform", "Google Ads")),
                    stakeholder=str(row["stakeholder"]),
                    monthly_budget=float(row["monthly_budget"]),
                    spend_mtd=float(row["spend_mtd"]),
                    spend_yesterday=float(row.get("spend_yesterday", 0)),
                    conversions=int(row.get("conversions", 0)),
                    cost_per_conversion=float(row.get("cost_per_conversion", 0)),
                    last_updated=last_updated,
                )
            )
        return campaigns
