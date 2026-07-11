"""Campaign and spend domain models."""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class RiskLevel(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OVER_BUDGET = "over_budget"


class CampaignSpend(BaseModel):
    campaign_id: str
    campaign_name: str
    platform: str = "Google Ads"
    stakeholder: str
    monthly_budget: float = Field(ge=0)
    spend_mtd: float = Field(ge=0)
    spend_yesterday: float = Field(default=0.0, ge=0)
    conversions: int = Field(default=0, ge=0)
    cost_per_conversion: float = Field(default=0.0, ge=0)
    last_updated: date

    @computed_field  # type: ignore[prop-decorator]
    @property
    def utilization_pct(self) -> float:
        if self.monthly_budget <= 0:
            return 0.0
        return round((self.spend_mtd / self.monthly_budget) * 100, 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def remaining_budget(self) -> float:
        return round(max(self.monthly_budget - self.spend_mtd, 0.0), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def projected_month_end_spend(self) -> float:
        day = self.last_updated.day
        if day <= 0:
            return self.spend_mtd
        daily_avg = self.spend_mtd / day
        return round(daily_avg * 30, 2)

    def risk_level(self, warning_pct: float, critical_pct: float) -> RiskLevel:
        utilization = self.utilization_pct
        if utilization >= critical_pct:
            return RiskLevel.OVER_BUDGET if self.spend_mtd > self.monthly_budget else RiskLevel.CRITICAL
        if utilization >= warning_pct:
            return RiskLevel.WARNING
        return RiskLevel.HEALTHY


class SpendAlert(BaseModel):
    campaign_id: str
    campaign_name: str
    stakeholder: str
    risk_level: RiskLevel
    message: str
    utilization_pct: float
    overspend_amount: float = 0.0


class DashboardSummary(BaseModel):
    total_budget: float
    total_spend_mtd: float
    utilization_pct: float
    campaigns_at_risk: int
    campaigns_over_budget: int
    projected_overspend: float
    prevented_loss_estimate: float
    total_conversions: int
    avg_cost_per_conversion: float
