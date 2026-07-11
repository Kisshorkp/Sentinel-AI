"""Chatbot agent — answers questions using analyzer data context."""

from __future__ import annotations

from config.settings import AppSettings
from agents.chat_context import context_has_analyzer_data
from agents.llm import invoke_summary


def _chatbot_system_prompt(context_json: str) -> str:
    has_analyzer = context_has_analyzer_data(context_json)
    base = (
        "You are Sentinel AI assistant — a Google Ads spend analyst chatbot.\n"
        "Answer using ONLY the JSON context below. Be helpful, concise, and actionable.\n"
        "CURRENCY: All amounts are INR. Always display money as ₹… Never use $ or USD.\n\n"
        "Capabilities:\n"
        "1. Answer questions about campaigns, spend, MTD, and daily/hourly data.\n"
        "2. Perform calculations on the loaded data when the user asks (percentages, "
        "differences, totals, comparisons, averages).\n"
        "3. Render markdown tables when the user asks for table format.\n\n"
        "Calculation rules:\n"
        "- Prefer exact numbers from `computed_metrics` and `calculation_results`.\n"
        "- When calculating, show: Formula → Inputs → Result.\n"
        "- Use formulas documented in `computed_metrics.formulas` when relevant.\n"
        "- If `calculation_results` is non-empty, use those verified results in your answer.\n"
        "- Do not invent numbers; derive everything from context.\n"
        "- Format money results with ₹ (INR).\n\n"
    )
    if has_analyzer:
        base += (
            "IMPORTANT: Analyzer data IS already loaded.\n"
            "- Use `analyzer_table` for raw budget, cost, MTD target, MTD achieve.\n"
            "- Use `daily_snapshot` for T-1, T-2, today, and 7-day average daily spend.\n"
            "- Use `computed_metrics` for pre-calculated percentages, variances, and totals.\n"
            "- Use `agent_summaries` for AI check results and severity.\n"
            "- Do NOT tell the user to Run Analyzer — they already ran it.\n"
            "- Only mention Extract hourly if the user asks about hour-by-hour breakdown AND "
            "`data_status.hourly_loaded` is false.\n"
        )
    else:
        base += (
            "No analyzer data is loaded yet. Tell the user to fill the form and click "
            "Run Analyzer on the Google Ads Analyzer tab first.\n"
        )
    return base


def run_chatbot(user_message: str, context_json: str, settings: AppSettings) -> str:
    if not user_message.strip():
        return (
            "Ask me anything about your data — e.g.:\n"
            "- *Show daily snapshot in a table*\n"
            "- *What is MTD achieve vs target for Search campaigns?*\n"
            "- *Calculate total budget utilization %*\n"
            "- *How much is T-1 spend above the 7-day average for Demand Gen?*"
        )

    if not context_has_analyzer_data(context_json):
        return (
            "No analyzer data is loaded yet. Go to the **Google Ads Analyzer** tab, "
            "fill the form, and click **Run Analyzer**. Then return here to chat."
        )

    system = _chatbot_system_prompt(context_json)
    user = (
        f"Context:\n{context_json}\n\n"
        f"User question: {user_message}\n\n"
        "If the question involves math, show your calculation steps using the context numbers."
    )
    return invoke_summary(settings, system, user)
