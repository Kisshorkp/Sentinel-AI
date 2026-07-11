"""Alert generation for overspend and budget risk."""

from __future__ import annotations

from config.settings import AppSettings
from models.campaign import CampaignSpend, RiskLevel, SpendAlert


class AlertService:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def generate_alerts(self, campaigns: list[CampaignSpend]) -> list[SpendAlert]:
        alerts: list[SpendAlert] = []
        for campaign in campaigns:
            risk = campaign.risk_level(
                self.settings.warning_threshold_pct,
                self.settings.critical_threshold_pct,
            )
            if risk == RiskLevel.HEALTHY:
                continue

            overspend = max(campaign.spend_mtd - campaign.monthly_budget, 0.0)
            message = self._build_message(campaign, risk, overspend)
            alerts.append(
                SpendAlert(
                    campaign_id=campaign.campaign_id,
                    campaign_name=campaign.campaign_name,
                    stakeholder=campaign.stakeholder,
                    risk_level=risk,
                    message=message,
                    utilization_pct=campaign.utilization_pct,
                    overspend_amount=round(overspend, 2),
                )
            )

        priority = {
            RiskLevel.OVER_BUDGET: 0,
            RiskLevel.CRITICAL: 1,
            RiskLevel.WARNING: 2,
            RiskLevel.HEALTHY: 3,
        }
        alerts.sort(key=lambda alert: (priority[alert.risk_level], -alert.utilization_pct))
        return alerts

    def _build_message(self, campaign: CampaignSpend, risk: RiskLevel, overspend: float) -> str:
        if risk == RiskLevel.OVER_BUDGET:
            return (
                f"{campaign.campaign_name} exceeded budget by "
                f"{overspend:,.2f}. Notify {campaign.stakeholder} immediately."
            )
        if risk == RiskLevel.CRITICAL:
            return (
                f"{campaign.campaign_name} is at {campaign.utilization_pct:.1f}% of budget. "
                f"Projected month-end: {campaign.projected_month_end_spend:,.2f}."
            )
        return (
            f"{campaign.campaign_name} reached {campaign.utilization_pct:.1f}% of monthly budget. "
            f"Review pacing with {campaign.stakeholder}."
        )
