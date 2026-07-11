"""Build chat context from analyzer session data."""

from __future__ import annotations

import json

from agents.chat_calculations import build_computed_metrics, run_requested_calculations
from config.settings import AppSettings
from models.agent_report import PipelineAgentReport
from models.analyzer_input import AnalyzerResult


def build_chat_context(
    result: AnalyzerResult | None,
    agent_report: PipelineAgentReport | None,
    hourly_rows: list[dict[str, object]] | None,
    extract_label: str | None,
    settings: AppSettings | None = None,
    user_question: str | None = None,
) -> str:
    payload: dict[str, object] = {
        "data_status": {
            "analyzer_loaded": False,
            "daily_loaded": False,
            "hourly_loaded": False,
        },
        "analyzer_table": [],
        "daily_snapshot": [],
        "hourly": None,
        "computed_metrics": {},
        "calculation_results": [],
        "agent_summaries": {},
    }

    if result:
        for field in result.fields:
            payload["analyzer_table"].append(
                {
                    "campaign_type": field.label,
                    "budget": field.budget,
                    "cost": field.cost,
                    "mtd_target": field.mtd_target,
                    "mtd_achieve": field.mtd_achieve,
                    "start_date": str(field.start_date),
                    "end_date": str(field.end_date),
                }
            )
            payload["daily_snapshot"].append(
                {
                    "campaign_type": field.label,
                    "t1_date": str(field.t1_date) if field.t1_date else None,
                    "t1_cost": field.t1_cost,
                    "t2_date": str(field.t2_date) if field.t2_date else None,
                    "t2_cost": field.t2_cost,
                    "today_date": str(field.today_date) if field.today_date else None,
                    "today_cost": field.today_cost,
                    "t1_7day_avg_cost": field.t1_7day_avg_cost,
                    "recent_daily_costs": field.recent_daily_costs,
                }
            )

        payload["data_status"] = {
            "analyzer_loaded": len(payload["analyzer_table"]) > 0,
            "daily_loaded": len(payload["daily_snapshot"]) > 0,
            "hourly_loaded": bool(hourly_rows and extract_label),
        }

        low_daily_pct = settings.low_daily_spend_budget_pct if settings else 50.0
        payload["computed_metrics"] = build_computed_metrics(
            result,
            hourly_rows=hourly_rows,
            extract_label=extract_label,
            low_daily_spend_budget_pct=low_daily_pct,
        )

    if agent_report:
        payload["agent_summaries"] = {
            "overall": agent_report.overall_summary,
            "overall_severity": agent_report.overall_severity.value,
            "analyzer_table": [
                {
                    "campaign_type": r.campaign_type,
                    "severity": r.severity.value,
                    "summary": r.summary,
                    "checks": [c.model_dump() for c in r.checks],
                }
                for r in agent_report.analyzer_table
            ],
            "daily_snapshot": [
                {
                    "campaign_type": r.campaign_type,
                    "severity": r.severity.value,
                    "summary": r.summary,
                    "checks": [c.model_dump() for c in r.checks],
                }
                for r in agent_report.daily_snapshot
            ],
            "hourly": (
                {
                    "campaign_type": agent_report.hourly.campaign_type,
                    "severity": agent_report.hourly.severity.value,
                    "summary": agent_report.hourly.summary,
                    "checks": [c.model_dump() for c in agent_report.hourly.checks],
                }
                if agent_report.hourly
                else None
            ),
        }

    if hourly_rows and extract_label:
        payload["hourly"] = {"campaign_type": extract_label, "rows": hourly_rows[:24]}
        if isinstance(payload["data_status"], dict):
            payload["data_status"]["hourly_loaded"] = True

    if user_question:
        payload["calculation_results"] = run_requested_calculations(user_question, payload)

    return json.dumps(payload, indent=2)


def context_has_analyzer_data(context_json: str) -> bool:
    try:
        payload = json.loads(context_json)
    except json.JSONDecodeError:
        return False
    status = payload.get("data_status") or {}
    if status.get("analyzer_loaded") or status.get("daily_loaded"):
        return True
    return bool(payload.get("analyzer_table") or payload.get("daily_snapshot"))
