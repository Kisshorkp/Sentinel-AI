"""LangGraph state for analyzer pipeline."""

from __future__ import annotations

from typing import TypedDict

from models.agent_report import PipelineAgentReport, TableAgentReport
from models.analyzer_input import AnalyzerResult


class AnalyzerGraphState(TypedDict, total=False):
    result: AnalyzerResult
    analyzer_reports: list[TableAgentReport]
    daily_reports: list[TableAgentReport]
    agent_report: PipelineAgentReport
