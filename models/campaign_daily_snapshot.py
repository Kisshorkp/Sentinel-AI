"""Models for campaign-level daily spend snapshot rows."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class DeletedCampaignInfo(BaseModel):
    """Campaign that appeared on T-1 but is missing from today's active set."""

    campaign_type: str
    campaign_id: str
    campaign_name: str


class CampaignDailyHygieneContext(BaseModel):
    """Type-level hygiene data for campaign checks."""

    deleted_campaigns: list[DeletedCampaignInfo] = Field(default_factory=list)
    t1_date: date | None = None
    today_date: date | None = None


class CampaignDailySnapshotRow(BaseModel):
    """One Google Ads campaign row in the daily spend snapshot table."""

    campaign_type: str
    campaign_id: str
    campaign_name: str
    t1_date: date | None = None
    t1_cost: float = Field(ge=0, default=0.0)
    t2_date: date | None = None
    t2_cost: float = Field(ge=0, default=0.0)
    today_date: date | None = None
    today_cost: float = Field(ge=0, default=0.0)
    t1_7day_avg_cost: float = Field(ge=0, default=0.0)
    recent_daily_costs: list[float] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    budget_amount: float = Field(ge=0, default=0.0)
    budget_period: str = ""
    primary_status: str = ""
    last_6h_cost: float = Field(ge=0, default=0.0)


class CampaignDailySnapshotBundle(BaseModel):
    """Campaign snapshot rows plus hygiene context for agent checks."""

    rows: list[CampaignDailySnapshotRow] = Field(default_factory=list)
    hygiene: CampaignDailyHygieneContext = Field(default_factory=CampaignDailyHygieneContext)
