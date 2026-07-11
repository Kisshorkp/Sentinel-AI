"""Analyze campaign spend inputs against Google Ads data."""

from __future__ import annotations

from models.analyzer_input import AnalyzerFormInput, AnalyzerResult, CampaignFieldInput


class CampaignAnalyzerService:
    def analyze(self, form_input: AnalyzerFormInput) -> AnalyzerResult:
        fields = form_input.campaign_fields
        sorted_fields = sorted(fields, key=lambda item: item.cost, reverse=True)
        highest = sorted_fields[0]
        lowest = sorted_fields[-1]

        return AnalyzerResult(
            account=form_input.account,
            account_start_date=form_input.account_start_date,
            account_end_date=form_input.account_end_date,
            fetch_start_date=form_input.fetch_start_date,
            fetch_end_date=form_input.fetch_end_date,
            fields=fields,
            total_budget=form_input.total_budget,
            total_spend=form_input.total_spend,
            total_converted_cost=form_input.total_converted_cost,
            total_conversions=form_input.total_conversions,
            total_conversions_value=form_input.total_conversions_value,
            highest_spend_field=highest.label,
            lowest_spend_field=lowest.label,
            data_source=form_input.data_source,
        )

    def share_pct(self, field: CampaignFieldInput, total: float) -> float:
        if total <= 0:
            return 0.0
        return round((field.cost / total) * 100, 2)
