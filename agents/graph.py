"""LangGraph pipeline: run table agents after analyzer fetch."""

from __future__ import annotations

from config.settings import AppSettings
from models.agent_report import PipelineAgentReport
from models.analyzer_input import AnalyzerResult
from agents.analyzer_table_agent import run_analyzer_table_agent
from agents.daily_snapshot_agent import run_daily_snapshot_agent
from agents.supervisor import run_supervisor


def run_analyzer_pipeline(result: AnalyzerResult, settings: AppSettings) -> PipelineAgentReport:
    """Run analyzer + daily agents, then supervisor. Uses LangGraph when available."""
    try:
        return _run_with_langgraph(result, settings)
    except ImportError:
        return _run_direct(result, settings)


def _run_direct(result: AnalyzerResult, settings: AppSettings) -> PipelineAgentReport:
    analyzer_reports = run_analyzer_table_agent(result, settings)
    daily_reports = run_daily_snapshot_agent(result, settings)
    return run_supervisor(analyzer_reports, daily_reports, [], settings)


def _run_with_langgraph(result: AnalyzerResult, settings: AppSettings) -> PipelineAgentReport:
    from langgraph.graph import END, START, StateGraph

    from agents.state import AnalyzerGraphState

    def analyzer_node(state: AnalyzerGraphState) -> AnalyzerGraphState:
        reports = run_analyzer_table_agent(state["result"], settings)
        return {"analyzer_reports": reports}

    def daily_node(state: AnalyzerGraphState) -> AnalyzerGraphState:
        reports = run_daily_snapshot_agent(state["result"], settings)
        return {"daily_reports": reports}

    def supervisor_node(state: AnalyzerGraphState) -> AnalyzerGraphState:
        report = run_supervisor(
            state.get("analyzer_reports", []),
            state.get("daily_reports", []),
            [],
            settings,
        )
        return {"agent_report": report}

    graph = StateGraph(AnalyzerGraphState)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("daily", daily_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_edge(START, "analyzer")
    graph.add_edge("analyzer", "daily")
    graph.add_edge("daily", "supervisor")
    graph.add_edge("supervisor", END)

    app = graph.compile()
    final = app.invoke({"result": result})
    return final["agent_report"]
