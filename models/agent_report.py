"""Models for AI agent threshold checks and summaries."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class Severity(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class ThresholdCheck(BaseModel):
    rule: str
    threshold: str
    actual: str
    status: CheckStatus
    message: str = ""


class TableAgentReport(BaseModel):
    table_name: str
    campaign_type: str | None = None
    campaign_id: str | None = None
    campaign_name: str | None = None
    checks: list[ThresholdCheck] = Field(default_factory=list)
    severity: Severity = Severity.HEALTHY
    summary: str = ""
    email_sent: bool = False
    email_log: list[str] = Field(default_factory=list)
    # Optional enrichment for structured alert emails (campaign-wise)
    start_date: str | None = None
    end_date: str | None = None
    budget_amount: float | None = None
    budget_period: str | None = None
    primary_status: str | None = None
    spend_amount: float | None = None
    mtd_target: float | None = None
    mtd_actual: float | None = None
    utilization_pct: float | None = None


class PipelineAgentReport(BaseModel):
    analyzer_table: list[TableAgentReport] = Field(default_factory=list)
    daily_snapshot: list[TableAgentReport] = Field(default_factory=list)
    hourly_snapshot: list[TableAgentReport] = Field(default_factory=list)
    campaign_daily_snapshot: list[TableAgentReport] = Field(default_factory=list)
    campaign_daily_by_type: list[TableAgentReport] = Field(default_factory=list)
    campaign_daily_overall: TableAgentReport | None = None
    hourly: TableAgentReport | None = None
    overall_severity: Severity = Severity.HEALTHY
    overall_summary: str = ""
    email_sent: bool = False
    email_log: list[str] = Field(default_factory=list)
