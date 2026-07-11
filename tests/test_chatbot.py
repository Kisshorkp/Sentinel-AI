"""Tests for chatbot context and gating."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

from agents.chat_context import build_chat_context, context_has_analyzer_data
from agents.chatbot_agent import run_chatbot
from config.settings import AppSettings
from models.analyzer_input import AnalyzerResult, CampaignFieldInput


def _result() -> AnalyzerResult:
    field = CampaignFieldInput(
        label="Search campaigns",
        budget=1000,
        cost=500,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 10),
        t1_cost=100,
        t2_cost=80,
        today_cost=120,
        t1_7day_avg_cost=90,
    )
    return AnalyzerResult(
        account="123",
        account_start_date=date(2026, 7, 1),
        account_end_date=date(2026, 7, 10),
        fetch_start_date=date(2026, 4, 1),
        fetch_end_date=date(2026, 7, 10),
        fields=[field],
        total_budget=1000,
        total_spend=500,
        total_converted_cost=500,
        total_conversions=1,
        total_conversions_value=0,
        highest_spend_field="Search campaigns",
        lowest_spend_field="Search campaigns",
    )


def test_context_has_analyzer_data_after_run():
    context = build_chat_context(_result(), None, None, None)
    assert context_has_analyzer_data(context) is True


def test_context_missing_when_no_result():
    context = build_chat_context(None, None, None, None)
    assert context_has_analyzer_data(context) is False


def test_chatbot_does_not_ask_to_run_analyzer_when_data_loaded():
    context = build_chat_context(_result(), None, None, None)
    settings = AppSettings(openrouter_api_key="test")

    reply = run_chatbot("daily data in table format", context, settings)
    assert "Run Analyzer" not in reply


@patch("agents.chatbot_agent.invoke_summary", return_value="| Campaign | Cost |\n|---|---|")
def test_chatbot_calls_llm_when_data_loaded(mock_invoke):
    context = build_chat_context(_result(), None, None, None)
    settings = AppSettings(openrouter_api_key="test")

    reply = run_chatbot("show daily snapshot", context, settings)

    assert "| Campaign |" in reply
    mock_invoke.assert_called_once()
    system_prompt = mock_invoke.call_args[0][1]
    assert "Do NOT tell the user to Run Analyzer" in system_prompt
