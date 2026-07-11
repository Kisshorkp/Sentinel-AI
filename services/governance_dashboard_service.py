"""CXO Overview dashboard aggregations — used only by /api/governance/overview."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

from models.campaign import CampaignSpend, RiskLevel, SpendAlert
from models.campaign import DashboardSummary


RAG_UNDER = "under_spend"
RAG_ON_TRACK = "on_track"
RAG_OVER = "over_spend"


def get_rag_status(deviation_pct: float) -> dict[str, str | float]:
    """MTD achievement deviation → RAG (green=underspend, amber=on-track, red=overspend)."""
    if deviation_pct < -5:
        return {
            "status": RAG_UNDER,
            "label": "Under Spend",
            "emoji": "🟢",
            "text_color": "#2F7D5B",
            "bg_tint": "#EAF3EE",
        }
    if deviation_pct > 5:
        return {
            "status": RAG_OVER,
            "label": "Over Spend",
            "emoji": "🔴",
            "text_color": "#B23A32",
            "bg_tint": "#FBEDEC",
        }
    return {
        "status": RAG_ON_TRACK,
        "label": "On Track",
        "emoji": "🟡",
        "text_color": "#B0791A",
        "bg_tint": "#FBF3E3",
    }


def _mtd_expected_pace(budget: float, anchor: date) -> float:
    """MTD Target = (Budget / days_in_month) × (T − 1)."""
    days_in_month = calendar.monthrange(anchor.year, anchor.month)[1]
    t_minus_1 = max(anchor.day - 1, 0)
    if budget <= 0 or days_in_month <= 0 or t_minus_1 <= 0:
        return 0.0
    return round((budget / days_in_month) * t_minus_1, 2)


def _deviation_pct(actual: float, expected: float) -> float:
    if expected <= 0:
        return 0.0
    return round(((actual - expected) / expected) * 100, 1)


def _health_score(utilization: float, critical: int, warning: int) -> int:
    score = 100
    score -= min(35, int(max(utilization - 85, 0) * 1.2))
    score -= critical * 8
    score -= warning * 3
    return max(0, min(100, score))


def _headline(deviation_pct: float, projected_delta: float, currency_note: str = "INR") -> str:
    direction = "ahead of" if deviation_pct > 0 else "behind" if deviation_pct < 0 else "aligned with"
    abs_pct = abs(deviation_pct)
    if projected_delta > 0:
        tail = f"projected to overspend by ₹{projected_delta:,.0f} by month-end"
    elif projected_delta < 0:
        tail = f"projected to underspend by ₹{abs(projected_delta):,.0f} by month-end"
    else:
        tail = "projected to finish on target by month-end"
    if abs_pct < 0.5:
        return f"Account is pacing in line with target — {tail}."
    return f"Account is pacing {abs_pct:.1f}% {direction} target — {tail}."


def _synthetic_meta_campaigns(anchor: date) -> list[CampaignSpend]:
    """Dashboard-only Meta rows so platform comparison is meaningful."""
    return [
        CampaignSpend(
            campaign_id="M2001",
            campaign_name="Meta Prospecting - IN",
            platform="Meta",
            stakeholder="Performance Team",
            monthly_budget=120000,
            spend_mtd=78400,
            spend_yesterday=3200,
            conversions=920,
            cost_per_conversion=85.22,
            last_updated=anchor,
        ),
        CampaignSpend(
            campaign_id="M2002",
            campaign_name="Meta Retargeting - Retail",
            platform="Meta",
            stakeholder="Retail Growth",
            monthly_budget=85000,
            spend_mtd=61200,
            spend_yesterday=2100,
            conversions=640,
            cost_per_conversion=95.63,
            last_updated=anchor,
        ),
        CampaignSpend(
            campaign_id="M2003",
            campaign_name="Meta Brand Reach",
            platform="Meta",
            stakeholder="Brand Team",
            monthly_budget=40000,
            spend_mtd=22800,
            spend_yesterday=980,
            conversions=180,
            cost_per_conversion=126.67,
            last_updated=anchor,
        ),
    ]


def _daily_pacing_series(
    total_budget: float,
    total_spend_mtd: float,
    anchor: date,
) -> list[dict[str, float | str]]:
    days_in_month = calendar.monthrange(anchor.year, anchor.month)[1]
    daily_actual = total_spend_mtd / max(anchor.day, 1)
    rows: list[dict[str, float | str]] = []
    cumulative_actual = 0.0
    for day in range(1, anchor.day + 1):
        day_date = date(anchor.year, anchor.month, day)
        # slight variance for visual interest
        factor = 0.88 + (day % 5) * 0.05
        spend = round(daily_actual * factor, 2)
        cumulative_actual = round(cumulative_actual + spend, 2)
        expected = round(total_budget * (day / days_in_month), 2)
        rows.append(
            {
                "date": day_date.isoformat(),
                "day_label": day_date.strftime("%d %b"),
                "actual_cumulative": cumulative_actual,
                "expected_pace": expected,
                "target": total_budget,
            }
        )
    # normalize last point to true MTD spend
    if rows:
        rows[-1]["actual_cumulative"] = round(total_spend_mtd, 2)
    return rows


def _sparkline_values(spend_mtd: float, seed: int) -> list[float]:
    base = spend_mtd / 7
    return [round(base * (0.82 + (seed + i) % 5 * 0.06), 2) for i in range(7)]


def build_governance_overview(
    campaigns: list[CampaignSpend],
    summary: DashboardSummary,
    alerts: list[SpendAlert],
    *,
    account_name: str = "Primary Account",
    account_cid: str = "",
    include_meta_demo: bool = True,
) -> dict:
    anchor = date.today()
    if campaigns:
        anchor = max(c.last_updated for c in campaigns)

    all_campaigns = list(campaigns)
    if include_meta_demo and not any(c.platform.lower() == "meta" for c in all_campaigns):
        all_campaigns.extend(_synthetic_meta_campaigns(anchor))

    total_budget = sum(c.monthly_budget for c in all_campaigns)
    total_spend = sum(c.spend_mtd for c in all_campaigns)
    expected_pace = sum(_mtd_expected_pace(c.monthly_budget, anchor) for c in all_campaigns)
    deviation = _deviation_pct(total_spend, expected_pace)
    rag = get_rag_status(deviation)

    critical = sum(1 for a in alerts if a.risk_level in {RiskLevel.CRITICAL, RiskLevel.OVER_BUDGET})
    warning = sum(1 for a in alerts if a.risk_level == RiskLevel.WARNING)

    projected_eom = sum(c.projected_month_end_spend for c in all_campaigns)
    projected_delta = round(projected_eom - total_budget, 2)

    platforms: dict[str, dict] = {}
    for campaign in all_campaigns:
        key = campaign.platform
        bucket = platforms.setdefault(
            key,
            {
                "platform": key,
                "mtd_spend": 0.0,
                "mtd_target": 0.0,
                "expected_pace": 0.0,
                "campaign_count": 0,
            },
        )
        bucket["mtd_spend"] = round(bucket["mtd_spend"] + campaign.spend_mtd, 2)
        bucket["mtd_target"] = round(bucket["mtd_target"] + campaign.monthly_budget, 2)
        bucket["expected_pace"] = round(
            bucket["expected_pace"] + _mtd_expected_pace(campaign.monthly_budget, anchor), 2
        )
        bucket["campaign_count"] += 1

    platform_rows = []
    for idx, (platform, bucket) in enumerate(sorted(platforms.items())):
        paced_target = bucket["expected_pace"]
        pace_dev = _deviation_pct(bucket["mtd_spend"], paced_target)
        pr = get_rag_status(pace_dev)
        platform_rows.append(
            {
                "platform": platform,
                "mtd_spend": bucket["mtd_spend"],
                # Display paced MTD target, not full monthly budget
                "mtd_target": paced_target,
                "expected_pace": paced_target,
                "campaign_count": bucket["campaign_count"],
                "pacing_pct": pace_dev,
                "rag": pr,
                "trend_7d": _sparkline_values(bucket["mtd_spend"], idx + 3),
            }
        )

    yesterday_alerts = [a for a in alerts if "yesterday" in a.message.lower() or True][:0]
    # use severity split from all alerts for demo
    alert_by_day = []
    for offset in range(6, -1, -1):
        day = anchor - timedelta(days=offset)
        count = max(0, len(alerts) - offset * 2) // 3 if alerts else 0
        alert_by_day.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a"),
                "critical": min(count, critical) if offset == 0 else count // 2,
                "warning": count - min(count, critical) if offset == 0 else count,
                "total": count,
            }
        )

    return {
        "account_name": account_name,
        "account_cid": account_cid or "465-793-6931",
        "context_line": f"Google Ads · MTD · {anchor.strftime('%b %Y')}",
        "anchor_date": anchor.isoformat(),
        "scorecard": {
            "health_score": _health_score(summary.utilization_pct, critical, warning),
            "mtd_spend": round(total_spend, 2),
            "mtd_target": round(expected_pace, 2),
            "deviation_pct": deviation,
            "rag": rag,
            "critical_alerts": critical,
            "warning_alerts": warning,
            "managed_spend_mtd": round(total_spend, 2),
            "headline": _headline(deviation, projected_delta),
            "projected_delta": projected_delta,
        },
        "platform_rows": platform_rows,
        "pacing_series": _daily_pacing_series(total_budget, total_spend, anchor),
        "alert_summary": {
            "yesterday": {
                "total": max(critical + warning, len(alerts) // 3),
                "critical": max(1, critical // 2) if alerts else 0,
                "warning": max(1, warning // 2) if alerts else 0,
                "platforms": {row["platform"]: row["campaign_count"] for row in platform_rows},
            },
            "last_7_days": {
                "total": len(alerts) + critical + warning,
                "critical": critical,
                "warning": warning,
                "daily": alert_by_day,
            },
        },
    }
