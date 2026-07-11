"""Models for manual campaign analyzer input."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, computed_field, model_validator


class CampaignFieldFormInput(BaseModel):
    """User-entered values and dates for one campaign type."""

    label: str
    budget: float = Field(ge=0, default=0.0)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_range(self) -> "CampaignFieldFormInput":
        if self.end_date < self.start_date:
            raise ValueError(f"{self.label}: end date must be on or after start date.")
        return self


class CampaignFieldInput(BaseModel):
    label: str
    budget: float = Field(ge=0, default=0.0)
    cost: float = Field(ge=0, default=0.0)
    converted_cost: float = Field(ge=0, default=0.0)
    conversions: float = Field(ge=0, default=0.0)
    conversions_value: float = Field(ge=0, default=0.0)
    mtd_achieve: float = Field(ge=0, default=0.0)
    mtd_target: float = Field(ge=0, default=0.0)
    mtd_achieve_end: date | None = None
    t1_date: date | None = None
    t1_cost: float = Field(ge=0, default=0.0)
    t2_date: date | None = None
    t2_cost: float = Field(ge=0, default=0.0)
    t1_7day_avg_cost: float = Field(ge=0, default=0.0)
    recent_daily_costs: list[float] = Field(default_factory=list)
    today_date: date | None = None
    today_cost: float = Field(ge=0, default=0.0)
    start_date: date
    end_date: date

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    @property
    def daily_average(self) -> float:
        days = self.duration_days
        if days <= 0:
            return 0.0
        return round(self.cost / days, 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cost_per_conversion(self) -> float:
        if self.conversions <= 0:
            return 0.0
        return round(self.cost / self.conversions, 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def budget_utilization_pct(self) -> float:
        if self.budget <= 0:
            return 0.0
        return round((self.cost / self.budget) * 100, 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def value(self) -> float:
        return self.cost


class AnalyzerFormInput(BaseModel):
    account: str = Field(min_length=1)
    account_start_date: date
    account_end_date: date
    fetch_start_date: date
    fetch_end_date: date
    search_campaigns: CampaignFieldInput
    video_campaigns: CampaignFieldInput
    demand_gen_campaigns: CampaignFieldInput
    performance_max_campaigns: CampaignFieldInput
    data_source: str = "manual"

    @property
    def campaign_fields(self) -> list[CampaignFieldInput]:
        return [
            self.search_campaigns,
            self.video_campaigns,
            self.demand_gen_campaigns,
            self.performance_max_campaigns,
        ]

    @property
    def total_budget(self) -> float:
        return round(sum(field.budget for field in self.campaign_fields), 2)

    @property
    def total_spend(self) -> float:
        return round(sum(field.cost for field in self.campaign_fields), 2)

    @property
    def total_converted_cost(self) -> float:
        return round(sum(field.converted_cost for field in self.campaign_fields), 2)

    @property
    def total_conversions(self) -> float:
        return round(sum(field.conversions for field in self.campaign_fields), 2)

    @property
    def total_conversions_value(self) -> float:
        return round(sum(field.conversions_value for field in self.campaign_fields), 2)


class AnalyzerResult(BaseModel):
    account: str
    account_start_date: date
    account_end_date: date
    fetch_start_date: date
    fetch_end_date: date
    fields: list[CampaignFieldInput]
    total_budget: float
    total_spend: float
    total_converted_cost: float
    total_conversions: float
    total_conversions_value: float
    highest_spend_field: str
    lowest_spend_field: str
    data_source: str = "manual"

    @property
    def avg_cost_per_conversion(self) -> float:
        if self.total_conversions <= 0:
            return 0.0
        return round(self.total_spend / self.total_conversions, 2)

    @property
    def budget_utilization_pct(self) -> float:
        if self.total_budget <= 0:
            return 0.0
        return round((self.total_spend / self.total_budget) * 100, 2)


class AnalyzerFormRequest(BaseModel):
    account: str = Field(min_length=1)
    account_start_date: date
    account_end_date: date
    search_campaigns: CampaignFieldFormInput
    video_campaigns: CampaignFieldFormInput
    demand_gen_campaigns: CampaignFieldFormInput
    performance_max_campaigns: CampaignFieldFormInput

    @property
    def campaign_field_forms(self) -> list[CampaignFieldFormInput]:
        return [
            self.search_campaigns,
            self.video_campaigns,
            self.demand_gen_campaigns,
            self.performance_max_campaigns,
        ]

    @property
    def fetch_end_date(self) -> date:
        return resolve_fetch_end_date(self)


def resolve_fetch_end_date(form: AnalyzerFormRequest) -> date:
    """Latest end date across account and all campaign fields."""
    all_end_dates = [form.account_end_date] + [field.end_date for field in form.campaign_field_forms]
    return max(all_end_dates)
