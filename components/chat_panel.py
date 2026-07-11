"""Streamlit chat panel for Sentinel AI."""

from __future__ import annotations

import streamlit as st

from agents.chat_context import build_chat_context
from agents.chatbot_agent import run_chatbot
from config.settings import AppSettings
from models.agent_report import PipelineAgentReport
from models.analyzer_input import AnalyzerResult


def render_chat_panel(settings: AppSettings) -> None:
    st.markdown("##### AI Chat Assistant")
    if not settings.openrouter_configured:
        st.warning("Add `OPENROUTER_API_KEY` to `.env` to enable the chatbot.")
        return

    result: AnalyzerResult | None = st.session_state.get("analyzer_result")
    if result is None:
        st.info("Run Analyzer first so the chatbot can use your Google Ads data.")
        return

    agent_report: PipelineAgentReport | None = st.session_state.get("agent_report")
    hourly_rows = st.session_state.get("hourly_rows_for_chat")
    extract_label = st.session_state.get("hourly_extract_label")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    tool_cols = st.columns([3, 1])
    with tool_cols[1]:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

    st.caption(
        "Ask questions or request calculations — e.g. *total cost*, "
        "*MTD variance for Search*, *T-1 vs 7-day avg %*, *budget utilization*."
    )

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask questions or request calculations on your spend data...")
    if prompt:
        context = build_chat_context(
            result,
            agent_report,
            hourly_rows,
            extract_label,
            settings=settings,
            user_question=prompt,
        )
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = run_chatbot(prompt, context, settings)
            st.markdown(reply)
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
