"""HTML critical alert email template (INR) matching Sentinel AI mail design."""

from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

from models.agent_report import CheckStatus, Severity, TableAgentReport, ThresholdCheck
from utils.formatting import format_currency


def _esc(value: object) -> str:
    return html.escape(str(value) if value is not None else "—")


def format_inr(value: float | None) -> str:
    if value is None:
        return "—"
    return format_currency(float(value), "INR")


def _parse_money(text: str) -> float | None:
    """Best-effort extract a numeric amount from check actual/threshold strings."""
    if not text:
        return None
    cleaned = text.replace(",", "").replace("₹", "").replace("$", "")
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _parse_pct(text: str) -> float | None:
    if not text:
        return None
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _status_dot(kind: str) -> str:
    color = {"critical": "#B23A32", "warning": "#B0791A", "healthy": "#2F7D5B"}.get(kind, "#5e6b7a")
    return (
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
        f'background:{color};margin-right:6px;vertical-align:middle;"></span>'
    )


def _section(title: str, body: str) -> str:
    return f"""
    <div style="border:1px solid #E6EBF0;border-radius:12px;margin:0 0 16px 0;overflow:hidden;">
      <div style="padding:12px 16px;background:#F4F6F8;border-bottom:1px solid #E6EBF0;
                  font-size:13px;font-weight:700;color:#16202B;letter-spacing:0.02em;">
        { _esc(title) }
      </div>
      <div style="padding:14px 16px;background:#ffffff;">{body}</div>
    </div>
    """


def _kv_table(rows: list[tuple[str, str]]) -> str:
    cells = "".join(
        f"""
        <tr>
          <td style="padding:8px 0;color:#5e6b7a;font-size:13px;width:38%;">{_esc(k)}</td>
          <td style="padding:8px 0;color:#16202B;font-size:13px;font-weight:600;">{v}</td>
        </tr>
        """
        for k, v in rows
    )
    return f'<table style="width:100%;border-collapse:collapse;">{cells}</table>'


def _utilization_bar(pct: float) -> str:
    width = min(max(pct, 0), 100)
    overflow = pct > 100
    bar_color = "#B23A32" if overflow or pct >= 100 else "#B0791A" if pct >= 80 else "#2F7D5B"
    label = f"{pct:,.1f}% Utilized"
    return f"""
    <div style="margin-top:10px;">
      <div style="height:12px;background:#EEF2F6;border-radius:999px;overflow:hidden;">
        <div style="height:12px;width:{width:.1f}%;background:{bar_color};border-radius:999px;"></div>
      </div>
      <div style="margin-top:6px;font-size:12px;font-weight:700;color:{bar_color};">{_esc(label)}</div>
    </div>
    """


def _alert_type_label(checks: list[ThresholdCheck]) -> str:
    rules = {c.rule for c in checks}
    if "budget_used_pct" in rules or "budget_amount_zero" in rules:
        return "Budget Overspend / Budget Issue"
    if "current_hour_overspend" in rules:
        return "Hourly Overspend"
    if "t1_vs_7day_avg" in rules or "consecutive_low_daily_spend" in rules:
        return "Daily Spend Anomaly"
    if any(r.startswith(("start_", "end_", "budget_", "eligible_", "new_campaign", "campaign_")) for r in rules):
        return "Campaign Hygiene / Setup"
    return "Spend Alert"


def _risk_summary(report: TableAgentReport, failing: list[ThresholdCheck]) -> list[tuple[str, str]]:
    has_budget = any(
        c.rule in {"budget_used_pct", "budget_amount_zero", "mtd_achieve_above_target", "new_campaign_budget_deviation"}
        for c in failing
    )
    has_pace = any(
        c.rule in {"mtd_achieve_above_target", "mtd_achieve_below_target", "t1_vs_7day_avg", "current_hour_overspend"}
        for c in failing
    )
    has_delivery = any(
        c.rule in {"eligible_zero_recent_spend", "consecutive_low_daily_spend", "end_date_imminent", "campaign_removed"}
        for c in failing
    )
    severity = report.severity
    priority = "Immediate" if severity == Severity.CRITICAL else "High" if severity == Severity.WARNING else "Monitor"

    def badge(label: str, kind: str) -> str:
        return f'{_status_dot(kind)} {_esc(label)}'

    return [
        ("Budget", badge("Critical" if has_budget and severity == Severity.CRITICAL else ("At Risk" if has_budget else "Healthy"),
                         "critical" if has_budget and severity == Severity.CRITICAL else ("warning" if has_budget else "healthy"))),
        ("Spend Pace", badge("Off Track" if has_pace else "On Track", "critical" if has_pace else "healthy")),
        ("Delivery", badge("At Risk" if has_delivery else "Healthy", "warning" if has_delivery else "healthy")),
        ("Priority", f'🚨 {_esc(priority)}'),
    ]


def build_ai_insight_prompt(report: TableAgentReport, failing: list[ThresholdCheck], currency: str = "INR") -> str:
    return (
        f"Write 2-3 sentences of AI insight for a critical spend alert email. "
        f"Use {currency} / ₹ amounts only (never $ or USD). "
        f"Mention campaign name if present, what went wrong, approximate magnitude, "
        f"and urge immediate review. No greeting, no sign-off, no subject line.\n\n"
        f"Pipeline: {report.table_name}; Type: {report.campaign_type}; "
        f"Campaign: {report.campaign_name}; ID: {report.campaign_id}; "
        f"Checks: {[c.model_dump() for c in failing[:8]]}; "
        f"Summary: {report.summary or 'n/a'}"
    )


def build_critical_alert_email_html(
    report: TableAgentReport,
    failing: list[ThresholdCheck],
    *,
    ai_insight: str,
    currency: str = "INR",
    detected_at: datetime | None = None,
    meta: dict[str, Any] | None = None,
) -> str:
    """Render the Critical Budget Alert HTML email (screenshot-style), amounts in INR."""
    meta = meta or {}
    when = detected_at or datetime.now()
    detected = when.strftime("%d %b %Y, %I:%M %p")
    campaign_name = report.campaign_name or report.campaign_type or "Account"
    campaign_type = (report.campaign_type or "—").replace(" campaigns", "")
    severity_label = "Critical" if report.severity == Severity.CRITICAL or any(
        c.status == CheckStatus.FAIL for c in failing
    ) else "Warning"
    severity_kind = "critical" if severity_label == "Critical" else "warning"

    start_date = meta.get("start_date") or "—"
    end_date = meta.get("end_date") or "—"
    if isinstance(end_date, str) and end_date[:10] >= "2037-12-01":
        end_date = "Open-ended"
    budget_amount = meta.get("budget_amount")
    budget_period = meta.get("budget_period") or ""
    primary_status = meta.get("primary_status") or "—"
    budget_display = format_inr(budget_amount) if budget_amount is not None else "—"
    if budget_period:
        budget_display = f"{budget_display} ({budget_period})"

    # Prefer explicit meta spend figures; else parse from checks.
    spend = meta.get("spend")
    if spend is None:
        for check in failing:
            if check.rule in {"budget_used_pct", "budget_amount_zero"}:
                spend = _parse_money(check.actual)
                break
    util_pct = meta.get("utilization_pct")
    if util_pct is None:
        for check in failing:
            if check.rule == "budget_used_pct":
                util_pct = _parse_pct(check.actual)
                break
    if util_pct is None and budget_amount and spend is not None and budget_amount > 0:
        util_pct = (float(spend) / float(budget_amount)) * 100

    details_rows = [
        ("Campaign Name", _esc(campaign_name)),
        ("Campaign Type", _esc(campaign_type)),
        ("Campaign ID", _esc(report.campaign_id or "—")),
        ("Start Date", _esc(start_date)),
        ("End Date", _esc(end_date)),
        ("Budget", _esc(budget_display)),
        ("Status", _esc(primary_status)),
        ("Alert Type", f'{_status_dot(severity_kind)} {_esc(_alert_type_label(failing))}'),
        ("Severity", f'{_status_dot(severity_kind)} {_esc(severity_label)}'),
        ("Detected On", _esc(detected)),
        ("Pipeline Step", _esc(report.table_name)),
    ]

    spend_body = f"""
      <div style="font-size:28px;font-weight:700;color:#16202B;margin-bottom:4px;">
        {_esc(f"{util_pct:,.1f}%" if util_pct is not None else "—")}
      </div>
      <div style="font-size:12px;color:#8a97a6;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">
        Budget Utilization
      </div>
      <table style="width:100%;border-collapse:collapse;margin-bottom:8px;">
        <tr>
          <td style="padding:4px 0;color:#5e6b7a;font-size:13px;">Budget Allocated</td>
          <td style="padding:4px 0;text-align:right;font-weight:600;color:#16202B;">{_esc(budget_display)}</td>
        </tr>
        <tr>
          <td style="padding:4px 0;color:#5e6b7a;font-size:13px;">Spend Incurred</td>
          <td style="padding:4px 0;text-align:right;font-weight:600;color:#16202B;">{_esc(format_inr(spend) if spend is not None else "—")}</td>
        </tr>
      </table>
      {_utilization_bar(float(util_pct) if util_pct is not None else 0.0)}
      <p style="margin:10px 0 0;font-size:11px;color:#8a97a6;">All amounts shown in INR (₹).</p>
    """

    risk_rows = _risk_summary(report, failing)
    insight = ai_insight.strip() or (
        f"Our AI monitoring engine flagged <strong>{_esc(campaign_name)}</strong> for critical "
        f"spend / setup anomalies. Immediate review is recommended to prevent further budget leakage."
    )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F4F6F8;font-family:Segoe UI,Arial,sans-serif;color:#16202B;">
  <div style="max-width:640px;margin:24px auto;padding:0 12px;">
    <p style="font-size:14px;color:#5e6b7a;margin:0 0 12px;">Hi Team,</p>
    <h1 style="font-size:22px;margin:0 0 8px;color:#16202B;">🚨 Critical Budget Alert</h1>
    <p style="font-size:14px;color:#5e6b7a;margin:0 0 20px;line-height:1.5;">
      A critical budget anomaly has been detected for the below campaign.
      Amounts are in <strong>INR (₹)</strong>.
    </p>

    {_section("1. Campaign Details", _kv_table(details_rows))}
    {_section("2. Spend Snapshot", spend_body)}
    {_section("3. Risk Summary", _kv_table(risk_rows))}
    {_section("4. AI Insight", f'<div style="font-size:14px;line-height:1.6;color:#16202B;">🤖 {insight}</div>')}

    <p style="font-size:11px;color:#8a97a6;margin:20px 0 0;text-align:center;">
      Sent by Sentinel AI · currency={_esc(currency)}
    </p>
  </div>
</body>
</html>"""


def build_critical_alert_email_text(
    report: TableAgentReport,
    failing: list[ThresholdCheck],
    *,
    ai_insight: str,
    currency: str = "INR",
    meta: dict[str, Any] | None = None,
) -> str:
    """Plain-text fallback for clients that ignore HTML."""
    meta = meta or {}
    lines = [
        "Hi Team,",
        "",
        "CRITICAL BUDGET ALERT",
        "A critical budget anomaly has been detected. Amounts in INR (₹).",
        "",
        f"Campaign: {report.campaign_name or report.campaign_type or 'Account'}",
        f"Type: {report.campaign_type or '—'}",
        f"ID: {report.campaign_id or '—'}",
        f"Start Date: {meta.get('start_date') or '—'}",
        f"End Date: {meta.get('end_date') or '—'}",
        f"Budget: {format_inr(meta.get('budget_amount'))} {meta.get('budget_period') or ''}".strip(),
        f"Status: {meta.get('primary_status') or '—'}",
        "",
        "AI Insight:",
        ai_insight.strip() or report.summary or "Review required.",
        "",
    ]
    return "\n".join(lines)
