"""FastAPI backend for Sentinel AI React UI."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from datetime import date
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.chat_context import build_chat_context
from agents.email_agent import refresh_critical_email_delivery
from agents.chatbot_agent import run_chatbot
from api.session_store import AnalyzerSession, session_store
from utils.fetch_preview import preview_records
from config.settings import AppSettings, get_settings
from models.analyzer_input import AnalyzerFormRequest, CampaignFieldFormInput
from models.agent_report import PipelineAgentReport
from models.campaign import CampaignSpend
from services.alert_service import AlertService
from services.api_pipeline_runner import run_agent_pipeline
from services.campaign_analyzer_service import CampaignAnalyzerService
from services.campaign_daily_snapshot_service import CampaignDailySnapshotService
from services.campaign_data_service import CampaignDataService
from services.email_service import verify_smtp_login
from services.google_ads_fetch_service import GoogleAdsFetchService
from services.pipeline_alerts_service import build_pipeline_alerts, count_pipeline_alerts
from services.spend_analytics_service import SpendAnalyticsService
from utils.formatting import risk_label
from utils.masking import mask_secret
from models.pipeline_steps import PipelineStepStatus, initial_step_status
from services.governance_dashboard_service import build_governance_overview
from services.dashboard_agent_service import build_dashboard_agent_overview

app = FastAPI(title="Sentinel AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CampaignFieldPayload(BaseModel):
    label: str
    budget: float = 0
    start_date: date
    end_date: date


class AnalyzerRunRequest(BaseModel):
    account: str
    account_start_date: date
    account_end_date: date
    search_campaigns: CampaignFieldPayload
    video_campaigns: CampaignFieldPayload
    demand_gen_campaigns: CampaignFieldPayload
    performance_max_campaigns: CampaignFieldPayload


class BudgetAlertsRequest(BaseModel):
    warning_threshold_pct: float = Field(default=80, ge=50, le=95)
    critical_threshold_pct: float = Field(default=100, ge=80, le=110)


class PipelineAlertsRequest(BaseModel):
    session_id: str | None = None
    agent_report: dict[str, Any] | None = None


class ChatRequest(BaseModel):
    session_id: str
    message: str


def _settings() -> AppSettings:
    return get_settings()


def _serialize_campaign(c: CampaignSpend, settings: AppSettings) -> dict[str, Any]:
    risk = c.risk_level(settings.warning_threshold_pct, settings.critical_threshold_pct)
    return {
        "campaign_id": c.campaign_id,
        "campaign_name": c.campaign_name,
        "platform": c.platform,
        "stakeholder": c.stakeholder,
        "monthly_budget": c.monthly_budget,
        "spend_mtd": c.spend_mtd,
        "spend_yesterday": c.spend_yesterday,
        "utilization_pct": c.utilization_pct,
        "projected_month_end_spend": c.projected_month_end_spend,
        "remaining_budget": c.remaining_budget,
        "conversions": c.conversions,
        "cost_per_conversion": c.cost_per_conversion,
        "status": risk.value,
        "status_label": risk_label(risk.value),
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "build": "2026-07-11-gaql-v2"}


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    settings = _settings()
    return {
        "app_title": settings.app_title,
        "app_currency": settings.app_currency,
        "warning_threshold_pct": settings.warning_threshold_pct,
        "critical_threshold_pct": settings.critical_threshold_pct,
        "google_ads_configured": settings.google_ads_configured,
        "google_ads_missing": settings.google_ads_missing_credentials(),
        "openrouter_configured": settings.openrouter_configured,
        "lookback_days": settings.google_ads_lookback_days,
        "default_customer_id": settings.google_ads_customer_id or "",
        "masked_credentials": {
            "developer_token": mask_secret(settings.google_ads_developer_token),
            "client_id": mask_secret(settings.google_ads_client_id),
            "refresh_token": mask_secret(settings.google_ads_refresh_token),
            "customer_id": settings.google_ads_customer_id or "Not set",
        },
    }


@app.get("/api/governance/overview")
def get_governance_overview() -> dict[str, Any]:
    """CXO Overview payload — dashboard page only (sample/demo data)."""
    settings = _settings()
    campaigns = CampaignDataService(settings).load_campaigns()
    analytics = SpendAnalyticsService(settings)
    alerts_svc = AlertService(settings)
    summary = analytics.summarize(campaigns)
    alerts = alerts_svc.generate_alerts(campaigns)
    account_name = settings.app_title.replace("Sentinel AI", "Spend Governance").strip() or "Spend Governance"
    cid = settings.google_ads_customer_id or "465-793-6931"
    return build_governance_overview(
        campaigns,
        summary,
        alerts,
        account_name=f"{account_name} Account",
        account_cid=cid,
    )


@app.get("/api/dashboard-agent/overview")
def get_dashboard_agent_overview() -> dict[str, Any]:
    """Live dashboard: last 7 days Google Ads + isolated LangGraph spend-check agent.

    Separate from Campaign Analysis (`POST /api/analyzer/run`) — does not share sessions.
    """
    settings = _settings()
    try:
        return build_dashboard_agent_overview(settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Dashboard agent failed to fetch or analyze Google Ads data: {exc}",
        ) from exc


@app.get("/api/dashboard")
def get_dashboard() -> dict[str, Any]:
    settings = _settings()
    campaigns = CampaignDataService(settings).load_campaigns()
    analytics = SpendAnalyticsService(settings)
    alerts_svc = AlertService(settings)
    summary = analytics.summarize(campaigns)
    alerts = alerts_svc.generate_alerts(campaigns)

    chart_rows = [
        {
            "campaign": c.campaign_name,
            "spend_mtd": c.spend_mtd,
            "monthly_budget": c.monthly_budget,
            "utilization_pct": c.utilization_pct,
        }
        for c in sorted(campaigns, key=lambda item: item.utilization_pct, reverse=True)
    ]

    return {
        "summary": summary.model_dump(),
        "campaigns": [_serialize_campaign(c, settings) for c in campaigns],
        "alerts": [alert.model_dump() for alert in alerts],
        "chart_rows": chart_rows,
        "currency": settings.app_currency,
    }


@app.get("/api/sample-data")
def get_sample_data(stakeholder: str = "All") -> dict[str, Any]:
    settings = _settings()
    campaigns = CampaignDataService(settings).load_campaigns()
    analytics = SpendAnalyticsService(settings)

    filtered = (
        campaigns
        if stakeholder == "All"
        else [c for c in campaigns if c.stakeholder == stakeholder]
    )
    stakeholder_totals = analytics.spend_by_stakeholder(filtered if stakeholder != "All" else campaigns)
    top_risk = analytics.top_overspend_campaigns(campaigns)

    return {
        "campaigns": [_serialize_campaign(c, settings) for c in filtered],
        "stakeholders": sorted({c.stakeholder for c in campaigns}),
        "stakeholder_totals": stakeholder_totals,
        "top_overspend": [
            {
                "campaign_name": c.campaign_name,
                "stakeholder": c.stakeholder,
                "amount": amount,
            }
            for c, amount in top_risk
        ],
        "currency": settings.app_currency,
    }


@app.post("/api/budget-alerts")
def post_budget_alerts(body: BudgetAlertsRequest) -> dict[str, Any]:
    settings = _settings()
    settings.warning_threshold_pct = body.warning_threshold_pct
    settings.critical_threshold_pct = body.critical_threshold_pct

    campaigns = CampaignDataService(settings).load_campaigns()
    alerts = AlertService(settings).generate_alerts(campaigns)
    grouped = build_pipeline_alerts(None, alerts, settings)

    return {
        "alerts": [alert.model_dump() for alert in alerts],
        "grouped_alerts": grouped,
        "total_count": count_pipeline_alerts(grouped),
        "warning_threshold_pct": body.warning_threshold_pct,
        "critical_threshold_pct": body.critical_threshold_pct,
        "currency": settings.app_currency,
        "has_analyzer_session": session_store.get_latest() is not None,
    }


@app.get("/api/pipeline-alerts")
def get_pipeline_alerts(session_id: str | None = None) -> dict[str, Any]:
    return _pipeline_alerts_response(PipelineAlertsRequest(session_id=session_id))


@app.post("/api/pipeline-alerts")
def post_pipeline_alerts(body: PipelineAlertsRequest | None = None) -> dict[str, Any]:
    return _pipeline_alerts_response(body or PipelineAlertsRequest())


def _resolve_agent_report(
    session_id: str | None,
    agent_report_raw: dict[str, Any] | None,
) -> tuple[PipelineAgentReport | None, str | None]:
    if agent_report_raw:
        return PipelineAgentReport.model_validate(agent_report_raw), session_id

    session = session_store.get(session_id) if session_id else session_store.get_latest()
    resolved_id = session_id or session_store.get_latest_id()
    if session and session.agent_report:
        raw = session.agent_report
        report = raw if isinstance(raw, PipelineAgentReport) else PipelineAgentReport.model_validate(raw)
        return report, resolved_id
    return None, resolved_id


def _pipeline_alerts_response(body: PipelineAlertsRequest) -> dict[str, Any]:
    """Alerts from the latest Run Analyzer pipeline only — no sample CSV fallback."""
    settings = _settings()
    agent_report, session_id = _resolve_agent_report(body.session_id, body.agent_report)

    empty = {"account": [], "daily": [], "hourly": [], "campaign": []}
    smtp_error = verify_smtp_login(settings)

    if agent_report is None:
        return {
            "grouped_alerts": empty,
            "total_count": 0,
            "session_id": session_id,
            "has_analyzer_session": False,
            "currency": settings.app_currency,
            "smtp_configured": settings.smtp_configured,
            "smtp_error": smtp_error,
            "message": "Run the analyzer on Campaign Analysis to load pipeline alerts.",
        }

    if smtp_error is None:
        agent_report = refresh_critical_email_delivery(agent_report, settings)

    if session_id:
        session = session_store.get(session_id)
        if session is not None:
            session.agent_report = agent_report

    grouped = build_pipeline_alerts(agent_report, spend_alerts=None, settings=settings)
    return {
        "grouped_alerts": grouped,
        "total_count": count_pipeline_alerts(grouped),
        "session_id": session_id,
        "has_analyzer_session": True,
        "currency": settings.app_currency,
        "smtp_configured": settings.smtp_configured,
        "smtp_error": smtp_error,
        "message": None,
    }


def _to_form_request(body: AnalyzerRunRequest) -> AnalyzerFormRequest:
    def field(payload: CampaignFieldPayload) -> CampaignFieldFormInput:
        return CampaignFieldFormInput(
            label=payload.label,
            budget=payload.budget,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )

    return AnalyzerFormRequest(
        account=body.account.strip(),
        account_start_date=body.account_start_date,
        account_end_date=body.account_end_date,
        search_campaigns=field(body.search_campaigns.model_copy(update={"label": "Search campaigns"})),
        video_campaigns=field(body.video_campaigns.model_copy(update={"label": "Video campaigns"})),
        demand_gen_campaigns=field(body.demand_gen_campaigns.model_copy(update={"label": "Demand Gen campaigns"})),
        performance_max_campaigns=field(
            body.performance_max_campaigns.model_copy(update={"label": "Performance Max campaigns"})
        ),
    )


def _analyzer_fetch_failed_payload(settings: AppSettings, error: Exception) -> dict[str, Any]:
    """Return pipeline-shaped response when Google Ads fetch fails (matches Streamlit UX)."""
    step_status = initial_step_status()
    step_status["fetch"] = PipelineStepStatus.ERROR.value
    return {
        "session_id": "",
        "analyzer_result": {},
        "agent_report": None,
        "step_status": step_status,
        "pipeline_errors": {"fetch": str(error)},
        "fetch_records_preview": [],
        "fetch_record_count": 0,
        "hourly_rows_by_label": {},
        "campaign_rows": [],
        "campaign_hygiene": {},
        "currency": settings.app_currency,
        "openrouter_configured": settings.openrouter_configured,
    }


@app.post("/api/analyzer/run")
def run_analyzer(body: AnalyzerRunRequest) -> dict[str, Any]:
    settings = _settings()
    if not settings.google_ads_configured:
        raise HTTPException(status_code=400, detail="Configure Google Ads credentials in .env first.")

    form_request = _to_form_request(body)
    fetch_service = GoogleAdsFetchService(settings)

    try:
        fetch_bundle = fetch_service.build_analyzer_input_from_form(form_request)
        result = CampaignAnalyzerService().analyze(fetch_bundle.form_input)
        customer_id = fetch_service.resolve_customer_id(form_request.account)
        campaign_bundle = CampaignDailySnapshotService(settings).fetch_snapshot(customer_id)
    except Exception as exc:
        return _analyzer_fetch_failed_payload(settings, exc)

    agent_report = None
    step_status = initial_step_status()
    step_status["fetch"] = PipelineStepStatus.COMPLETE.value
    hourly_by_label: dict[str, list[dict[str, object]]] = {}
    pipeline_errors: dict[str, str] = {}

    if settings.openrouter_configured:
        agent_report, step_status, hourly_by_label, pipeline_errors = run_agent_pipeline(
            result,
            settings,
            campaign_bundle.rows,
            fetch_service,
            customer_id,
            campaign_hygiene=campaign_bundle.hygiene,
        )
    else:
        step_status = {
            key: PipelineStepStatus.COMPLETE.value if key == "fetch" else PipelineStepStatus.SKIPPED.value
            for key in step_status
        }

    fetch_records = [dict(record) for record in fetch_bundle.raw_records]
    session_id = session_store.create(
        AnalyzerSession(
            analyzer_result=result,
            agent_report=agent_report,
            hourly_rows_by_label=hourly_by_label,
            campaign_rows=campaign_bundle.rows,
            fetch_records=fetch_records,
        )
    )

    return {
        "session_id": session_id,
        "analyzer_result": result.model_dump(mode="json"),
        "agent_report": agent_report.model_dump(mode="json") if agent_report else None,
        "step_status": step_status,
        "pipeline_errors": pipeline_errors,
        "fetch_records_preview": preview_records(fetch_records),
        "fetch_record_count": len(fetch_records),
        "hourly_rows_by_label": hourly_by_label,
        "campaign_rows": [row.model_dump(mode="json") for row in campaign_bundle.rows],
        "campaign_hygiene": campaign_bundle.hygiene.model_dump(mode="json"),
        "currency": settings.app_currency,
        "openrouter_configured": settings.openrouter_configured,
    }


@app.post("/api/chat")
def chat(body: ChatRequest) -> dict[str, Any]:
    settings = _settings()
    if not settings.openrouter_configured:
        raise HTTPException(status_code=400, detail="Add OPENROUTER_API_KEY to .env to enable chat.")

    session = session_store.get(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Analyzer session not found. Run the analyzer first.")

    if session.analyzer_result is None:
        raise HTTPException(status_code=400, detail="Run Analyzer first so the chatbot can use your data.")

    hourly_rows = None
    extract_label = None
    if session.hourly_rows_by_label:
        extract_label = next(iter(session.hourly_rows_by_label), None)
        if extract_label:
            hourly_rows = session.hourly_rows_by_label.get(extract_label)

    context = build_chat_context(
        session.analyzer_result,
        session.agent_report,
        hourly_rows,
        extract_label,
        settings=settings,
        user_question=body.message,
    )
    reply = run_chatbot(body.message, context, settings)
    session_store.append_chat(body.session_id, "user", body.message)
    session_store.append_chat(body.session_id, "assistant", reply)

    return {
        "reply": reply,
        "messages": session.chat_messages,
    }


@app.get("/api/chat/{session_id}")
def get_chat_history(session_id: str) -> dict[str, Any]:
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"messages": session.chat_messages}
