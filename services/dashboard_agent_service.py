"""Dashboard agent service — fetch last 7 days Google Ads + run isolated checks.

Does not call `api_pipeline_runner` or mutate analyzer sessions.
"""

from __future__ import annotations

import calendar
import logging
from collections import defaultdict
from datetime import date
from typing import Any

from agents.dashboard_agent_graph import run_dashboard_agent
from config.settings import AppSettings
from models.agent_report import CheckStatus, PipelineAgentReport, TableAgentReport
from models.analyzer_input import (
    AnalyzerFormRequest,
    CampaignFieldFormInput,
)
from services.campaign_analyzer_service import CampaignAnalyzerService
from services.campaign_daily_snapshot_service import CampaignDailySnapshotService
from services.google_ads_fetch_service import (
    ANALYZER_LABELS,
    DailyMetricsStore,
    GoogleAdsFetchService,
)
from services.governance_dashboard_service import get_rag_status
from services.pipeline_alerts_service import build_pipeline_alerts, count_pipeline_alerts
from utils.daily_spend_checks import iter_days_inclusive
from utils.mtd_metrics import (
    calculate_calendar_mtd_target,
    calculate_t1_seven_day_average,
    reference_t_dates,
    t1_seven_day_window,
)

logger = logging.getLogger(__name__)

SHORT_LABEL = {
    "Search campaigns": "Search",
    "Video campaigns": "Video",
    "Demand Gen campaigns": "Demand Gen",
    "Performance Max campaigns": "PMax",
}


def _month_bounds(anchor: date | None = None) -> tuple[date, date]:
    today = anchor or date.today()
    start = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    end = today.replace(day=last_day)
    return start, end


def _monthly_budget_from_campaigns(rows, label: str, days_in_month: int) -> float:
    """Sum Google Ads campaign budgets for a channel into a monthly figure."""
    total = 0.0
    for row in rows:
        if row.campaign_type != label:
            continue
        amount = float(row.budget_amount or 0.0)
        period = (row.budget_period or "").upper()
        if period == "DAILY":
            total += amount * days_in_month
        else:
            total += amount
    return round(total, 2)


def _build_auto_form(
    customer_id: str,
    campaign_rows,
    month_start: date,
    month_end: date,
) -> AnalyzerFormRequest:
    days_in_month = calendar.monthrange(month_start.year, month_start.month)[1]

    def field(label: str) -> CampaignFieldFormInput:
        return CampaignFieldFormInput(
            label=label,
            budget=_monthly_budget_from_campaigns(campaign_rows, label, days_in_month),
            start_date=month_start,
            end_date=month_end,
        )

    return AnalyzerFormRequest(
        account=customer_id,
        account_start_date=month_start,
        account_end_date=month_end,
        search_campaigns=field("Search campaigns"),
        video_campaigns=field("Video campaigns"),
        demand_gen_campaigns=field("Demand Gen campaigns"),
        performance_max_campaigns=field("Performance Max campaigns"),
    )


def _count_checks(reports: list[TableAgentReport]) -> dict[str, int]:
    counts = {"pass": 0, "warning": 0, "fail": 0}
    for report in reports:
        for check in report.checks:
            if check.status == CheckStatus.PASS:
                counts["pass"] += 1
            elif check.status == CheckStatus.WARNING:
                counts["warning"] += 1
            else:
                counts["fail"] += 1
    return counts


def _all_reports(report: PipelineAgentReport) -> list[TableAgentReport]:
    items: list[TableAgentReport] = []
    items.extend(report.analyzer_table)
    items.extend(report.daily_snapshot)
    items.extend(report.hourly_snapshot)
    items.extend(report.campaign_daily_snapshot)
    return items


def _health_from_report(report: PipelineAgentReport, utilization: float) -> int:
    score = 100
    score -= min(35, int(max(utilization - 85, 0) * 1.2))
    for r in _all_reports(report):
        for check in r.checks:
            if check.status == CheckStatus.FAIL:
                score -= 8
            elif check.status == CheckStatus.WARNING:
                score -= 3
    return max(0, min(100, score))


def _daily_series(
    store: DailyMetricsStore,
    window_start: date,
    window_end: date,
) -> list[dict[str, Any]]:
    series: list[dict[str, Any]] = []
    for day in iter_days_inclusive(window_start, window_end):
        point: dict[str, Any] = {
            "date": day.isoformat(),
            "day": day.strftime("%a %d"),
            "search": store.day_cost("Search campaigns", day),
            "video": store.day_cost("Video campaigns", day),
            "demandGen": store.day_cost("Demand Gen campaigns", day),
            "pmax": store.day_cost("Performance Max campaigns", day),
            "total": 0.0,
        }
        point["total"] = round(
            point["search"] + point["video"] + point["demandGen"] + point["pmax"], 2
        )
        series.append(point)
    return series


def _spend_by_channel(store: DailyMetricsStore, start: date, end: date) -> dict[str, float]:
    return {
        SHORT_LABEL[label]: round(store.aggregate(label, start, end).cost, 2)
        for label in ANALYZER_LABELS
    }


def _hourly_today_series(
    hourly_rows_by_label: dict[str, list[dict[str, object]]],
) -> list[dict[str, Any]]:
    by_hour: dict[int, dict[str, Any]] = {}
    for label, rows in hourly_rows_by_label.items():
        short = SHORT_LABEL.get(label, label)
        for row in rows:
            hour = int(row.get("Hour", 0))  # type: ignore[arg-type]
            bucket = by_hour.setdefault(
                hour,
                {"hour": hour, "label": f"{hour:02d}:00", "total": 0.0},
            )
            cost = float(row.get("Today's cost") or 0)  # type: ignore[arg-type]
            bucket[short] = cost
            bucket["total"] = round(bucket["total"] + cost, 2)
    return [by_hour[h] for h in sorted(by_hour)]


def _pacing_series(
    store: DailyMetricsStore,
    month_start: date,
    anchor: date,
    total_budget: float,
) -> list[dict[str, Any]]:
    days_in_month = calendar.monthrange(anchor.year, anchor.month)[1]
    daily_target = total_budget / days_in_month if total_budget > 0 else 0.0
    cumulative = 0.0
    series: list[dict[str, Any]] = []
    for day in iter_days_inclusive(month_start, anchor):
        day_spend = sum(store.day_cost(label, day) for label in ANALYZER_LABELS)
        cumulative = round(cumulative + day_spend, 2)
        day_index = (day - month_start).days + 1
        series.append(
            {
                "date": day.isoformat(),
                "day_label": day.strftime("%d %b"),
                "actual_cumulative": cumulative,
                "expected_pace": round(daily_target * day_index, 2),
                "target": round(total_budget, 2),
            }
        )
    return series


def _platform_rows(
    store: DailyMetricsStore,
    form: AnalyzerFormRequest,
    window_start: date,
    window_end: date,
    month_start: date,
    anchor: date,
) -> list[dict[str, Any]]:
    """Platform pacing table — MTD Target = (Budget / days_in_month) × (T−1)."""
    rows: list[dict[str, Any]] = []
    form_by_label = {f.label: f for f in form.campaign_field_forms}
    for label in ANALYZER_LABELS:
        field = form_by_label[label]
        mtd_spend = store.aggregate(label, month_start, anchor).cost
        # MTD Target = (Budget / Number of days of the month) × (T − 1)
        expected = calculate_calendar_mtd_target(field.budget, anchor)
        if expected <= 0 and field.budget > 0:
            expected = field.budget
        deviation = (
            round(((mtd_spend - expected) / expected) * 100, 1) if expected > 0 else 0.0
        )
        trend = [store.day_cost(label, day) for day in iter_days_inclusive(window_start, window_end)]
        rows.append(
            {
                "platform": SHORT_LABEL[label],
                "mtd_spend": mtd_spend,
                "mtd_target": round(expected, 2),
                "expected_pace": round(expected, 2),
                "campaign_count": 0,
                "pacing_pct": deviation,
                "rag": get_rag_status(deviation),
                "trend_7d": trend,
            }
        )
    return rows


def _top_campaigns(campaign_rows, limit: int = 8) -> list[dict[str, Any]]:
    ranked = sorted(
        campaign_rows,
        key=lambda r: float(r.t1_cost or 0) + float(r.today_cost or 0),
        reverse=True,
    )
    out: list[dict[str, Any]] = []
    for row in ranked[:limit]:
        out.append(
            {
                "campaign": row.campaign_name[:40],
                "campaign_type": SHORT_LABEL.get(row.campaign_type, row.campaign_type),
                "spend_7d_proxy": round(
                    sum(row.recent_daily_costs or []) + float(row.today_cost or 0), 2
                ),
                "t1_cost": float(row.t1_cost or 0),
                "budget": float(row.budget_amount or 0),
                "today_cost": float(row.today_cost or 0),
            }
        )
    return out


def _check_level_breakdown(report: PipelineAgentReport) -> dict[str, int]:
    grouped = build_pipeline_alerts(report, spend_alerts=None, settings=None)
    return {
        "Account": len(grouped.get("account") or []),
        "Daily": len(grouped.get("daily") or []),
        "Hourly": len(grouped.get("hourly") or []),
        "Campaign": len(grouped.get("campaign") or []),
    }


def _severity_pie(report: PipelineAgentReport) -> dict[str, int]:
    return _count_checks(_all_reports(report))


def _alert_summary(report: PipelineAgentReport, window_start: date, window_end: date) -> dict:
    grouped = build_pipeline_alerts(report, spend_alerts=None, settings=None)
    all_alerts = []
    for step_alerts in grouped.values():
        all_alerts.extend(step_alerts)

    critical = sum(1 for a in all_alerts if a.get("severity") == "critical")
    warning = sum(1 for a in all_alerts if a.get("severity") == "warning")

    platforms: dict[str, int] = defaultdict(int)
    for a in all_alerts:
        ctype = a.get("campaign_type") or "Account"
        short = SHORT_LABEL.get(ctype, ctype.replace(" campaigns", "") if ctype else "Other")
        platforms[short] += 1

    # Distribute alert volume across the 7-day window for the chart (current run snapshot).
    days = list(iter_days_inclusive(window_start, window_end))
    per_day_crit = critical // max(len(days), 1)
    per_day_warn = warning // max(len(days), 1)
    rem_c, rem_w = critical % max(len(days), 1), warning % max(len(days), 1)
    daily = []
    for i, day in enumerate(days):
        c = per_day_crit + (1 if i < rem_c else 0)
        w = per_day_warn + (1 if i < rem_w else 0)
        daily.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a"),
                "critical": c,
                "warning": w,
                "total": c + w,
            }
        )

    return {
        "yesterday": {
            "total": critical + warning,
            "critical": critical,
            "warning": warning,
            "platforms": dict(platforms),
        },
        "last_7_days": {
            "total": critical + warning,
            "critical": critical,
            "warning": warning,
            "daily": daily,
        },
    }


def build_dashboard_agent_overview(settings: AppSettings) -> dict[str, Any]:
    """Fetch last 7 days Google Ads data, run dashboard agent checks, return UI payload."""
    if not settings.google_ads_configured:
        raise ValueError("Configure Google Ads credentials in .env to load the live dashboard agent.")

    customer_id = settings.google_ads_customer_id.strip()
    if not customer_id:
        raise ValueError("Set GOOGLE_ADS_CUSTOMER_ID in .env.")

    fetch_service = GoogleAdsFetchService(settings)
    customer_id = fetch_service.resolve_customer_id(customer_id)

    today = date.today()
    month_start, month_end = _month_bounds(today)
    avg_window_start, avg_window_end = t1_seven_day_window(today)
    chart_start = avg_window_start
    chart_end = max(avg_window_end, today)

    snapshot_svc = CampaignDailySnapshotService(settings)
    snapshot = snapshot_svc.fetch_snapshot(customer_id)
    campaign_rows = snapshot.rows
    campaign_hygiene = snapshot.hygiene

    form = _build_auto_form(customer_id, campaign_rows, month_start, month_end)

    # MTD window for account pacing + 7-day window for daily checks / charts.
    mtd_store, _ = fetch_service.fetch_daily_metrics(customer_id, month_start, today)
    recent_store, recent_records = fetch_service.fetch_daily_metrics(
        customer_id, chart_start, chart_end
    )

    # Prefer MTD store for cost aggregation; overlay recent daily costs for T-1 checks.
    t1_date, t2_date = reference_t_dates(today)
    form_by_label = {f.label: f for f in form.campaign_field_forms}

    from models.analyzer_input import AnalyzerFormInput, CampaignFieldInput

    def build_field(label: str) -> CampaignFieldInput:
        user = form_by_label[label]
        metrics = mtd_store.aggregate(label, user.start_date, min(user.end_date, today))
        mtd_achieve_end = t1_date if t1_date >= month_start else None
        mtd_achieve = (
            mtd_store.aggregate(label, month_start, mtd_achieve_end).cost
            if mtd_achieve_end
            else 0.0
        )
        mtd_target = calculate_calendar_mtd_target(user.budget, today)
        seven_day_total = recent_store.aggregate(label, avg_window_start, avg_window_end).cost
        return CampaignFieldInput(
            label=label,
            budget=user.budget,
            cost=metrics.cost,
            converted_cost=metrics.converted_cost,
            conversions=metrics.conversions,
            conversions_value=metrics.conversions_value,
            mtd_achieve=mtd_achieve,
            mtd_target=mtd_target,
            mtd_achieve_end=mtd_achieve_end,
            t1_date=t1_date,
            t1_cost=recent_store.day_cost(label, t1_date),
            t2_date=t2_date,
            t2_cost=recent_store.day_cost(label, t2_date),
            t1_7day_avg_cost=calculate_t1_seven_day_average(seven_day_total),
            recent_daily_costs=[
                recent_store.day_cost(label, day)
                for day in iter_days_inclusive(avg_window_start, avg_window_end)
            ],
            today_date=today,
            today_cost=recent_store.day_cost(label, today),
            start_date=user.start_date,
            end_date=user.end_date,
        )

    form_input = AnalyzerFormInput(
        account=customer_id,
        account_start_date=month_start,
        account_end_date=month_end,
        fetch_start_date=chart_start,
        fetch_end_date=chart_end,
        search_campaigns=build_field("Search campaigns"),
        video_campaigns=build_field("Video campaigns"),
        demand_gen_campaigns=build_field("Demand Gen campaigns"),
        performance_max_campaigns=build_field("Performance Max campaigns"),
        data_source="google_ads_dashboard_agent",
    )
    result = CampaignAnalyzerService().analyze(form_input)

    agent_report, hourly_rows_by_label, errors = run_dashboard_agent(
        result,
        settings,
        campaign_rows,
        fetch_service,
        customer_id,
        campaign_hygiene=campaign_hygiene,
    )

    total_budget = result.total_budget
    total_spend = result.total_spend
    utilization = result.budget_utilization_pct
    expected_pace = sum(f.mtd_target for f in result.fields)
    deviation = (
        round(((sum(f.mtd_achieve for f in result.fields) - expected_pace) / expected_pace) * 100, 1)
        if expected_pace > 0
        else 0.0
    )
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    projected = round(total_spend / max(today.day, 1) * days_in_month, 2) if today.day else total_spend
    projected_delta = round(projected - total_budget, 2) if total_budget > 0 else 0.0

    severity_counts = _severity_pie(agent_report)
    level_breakdown = _check_level_breakdown(agent_report)
    alerts = _alert_summary(agent_report, avg_window_start, avg_window_end)
    critical = alerts["yesterday"]["critical"]
    warning = alerts["yesterday"]["warning"]

    rag = get_rag_status(deviation)
    direction = "ahead of" if deviation > 0 else "behind" if deviation < 0 else "aligned with"
    if projected_delta > 0:
        tail = f"projected to overspend by ₹{projected_delta:,.0f} by month-end"
    elif projected_delta < 0:
        tail = f"projected to underspend by ₹{abs(projected_delta):,.0f} by month-end"
    else:
        tail = "projected to finish on target by month-end"
    headline = (
        f"Account is pacing {abs(deviation):.1f}% {direction} target — {tail}."
        if abs(deviation) >= 0.5
        else f"Account is pacing in line with target — {tail}."
    )
    if agent_report.overall_summary:
        headline = agent_report.overall_summary.split("\n")[0][:280]

    platform_rows = _platform_rows(
        mtd_store, form, avg_window_start, avg_window_end, month_start, today
    )
    # Attach campaign counts
    type_counts: dict[str, int] = defaultdict(int)
    for row in campaign_rows:
        type_counts[SHORT_LABEL.get(row.campaign_type, row.campaign_type)] += 1
    for prow in platform_rows:
        prow["campaign_count"] = type_counts.get(prow["platform"], 0)

    grouped = build_pipeline_alerts(agent_report, spend_alerts=None, settings=settings)

    return {
        "source": "dashboard_agent",
        "account_name": "Google Ads Account",
        "account_cid": customer_id,
        "context_line": f"Last 7 days · {chart_start.isoformat()} → {chart_end.isoformat()}",
        "anchor_date": today.isoformat(),
        "window_start": chart_start.isoformat(),
        "window_end": chart_end.isoformat(),
        "scorecard": {
            "health_score": _health_from_report(agent_report, utilization),
            "mtd_spend": total_spend,
            "mtd_target": round(expected_pace or total_budget, 2),
            "deviation_pct": deviation,
            "rag": rag,
            "critical_alerts": critical,
            "warning_alerts": warning,
            "managed_spend_mtd": total_spend,
            "headline": headline,
            "projected_delta": projected_delta,
        },
        "platform_rows": platform_rows,
        "pacing_series": _pacing_series(mtd_store, month_start, today, total_budget),
        "alert_summary": alerts,
        "agent": {
            "overall_severity": agent_report.overall_severity.value,
            "overall_summary": agent_report.overall_summary,
            "errors": errors,
            "check_severity": severity_counts,
            "check_by_level": level_breakdown,
            "grouped_alerts": grouped,
            "alert_count": count_pipeline_alerts(grouped),
        },
        "charts": {
            "spend_by_channel": _spend_by_channel(recent_store, chart_start, chart_end),
            "daily_spend_series": _daily_series(recent_store, chart_start, chart_end),
            "hourly_today": _hourly_today_series(hourly_rows_by_label),
            "top_campaigns": _top_campaigns(campaign_rows),
            "check_severity": severity_counts,
            "check_by_level": level_breakdown,
        },
        "currency": settings.app_currency,
        "openrouter_configured": settings.openrouter_configured,
        "fetch_record_count": len(recent_records),
        "campaign_count": len(campaign_rows),
    }
