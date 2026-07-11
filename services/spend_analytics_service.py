"""Spend analytics and dashboard aggregation."""

from __future__ import annotations

from config.settings import AppSettings
from models.campaign import CampaignSpend, DashboardSummary, RiskLevel


class SpendAnalyticsService:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def summarize(self, campaigns: list[CampaignSpend]) -> DashboardSummary:
        total_budget = sum(c.monthly_budget for c in campaigns)
        total_spend = sum(c.spend_mtd for c in campaigns)
        utilization = (total_spend / total_budget * 100) if total_budget else 0.0

        at_risk = 0
        over_budget = 0
        projected_overspend = 0.0
        prevented_loss = 0.0
        total_conversions = sum(c.conversions for c in campaigns)

        for campaign in campaigns:
            risk = campaign.risk_level(
                self.settings.warning_threshold_pct,
                self.settings.critical_threshold_pct,
            )
            if risk in {RiskLevel.WARNING, RiskLevel.CRITICAL, RiskLevel.OVER_BUDGET}:
                at_risk += 1
            if risk == RiskLevel.OVER_BUDGET:
                over_budget += 1
                projected_overspend += max(campaign.spend_mtd - campaign.monthly_budget, 0.0)
            elif campaign.projected_month_end_spend > campaign.monthly_budget:
                projected_overspend += campaign.projected_month_end_spend - campaign.monthly_budget

            if risk in {RiskLevel.WARNING, RiskLevel.CRITICAL}:
                prevented_loss += max(campaign.monthly_budget - campaign.spend_mtd, 0.0) * 0.15

        avg_cpc = (total_spend / total_conversions) if total_conversions else 0.0
        nr_loss = (projected_overspend + prevented_loss) * self.settings.nr_loss_multiplier

        return DashboardSummary(
            total_budget=round(total_budget, 2),
            total_spend_mtd=round(total_spend, 2),
            utilization_pct=round(utilization, 2),
            campaigns_at_risk=at_risk,
            campaigns_over_budget=over_budget,
            projected_overspend=round(projected_overspend, 2),
            prevented_loss_estimate=round(nr_loss, 2),
            total_conversions=total_conversions,
            avg_cost_per_conversion=round(avg_cpc, 2),
        )

    def top_overspend_campaigns(
        self, campaigns: list[CampaignSpend], limit: int = 5
    ) -> list[tuple[CampaignSpend, float]]:
        scored: list[tuple[CampaignSpend, float]] = []
        for campaign in campaigns:
            overspend = max(campaign.spend_mtd - campaign.monthly_budget, 0.0)
            if overspend == 0 and campaign.projected_month_end_spend > campaign.monthly_budget:
                overspend = campaign.projected_month_end_spend - campaign.monthly_budget
            scored.append((campaign, overspend))
        scored.sort(key=lambda item: item[1], reverse=True)
        return [item for item in scored if item[1] > 0][:limit]

    def spend_by_stakeholder(self, campaigns: list[CampaignSpend]) -> dict[str, float]:
        totals: dict[str, float] = {}
        for campaign in campaigns:
            totals[campaign.stakeholder] = totals.get(campaign.stakeholder, 0.0) + campaign.spend_mtd
        return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))
