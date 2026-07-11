"""Tests for shared LLM currency enforcement."""

from __future__ import annotations

from agents.llm import INR_CURRENCY_RULE, _with_currency_data_note, _with_currency_rule
from utils.formatting import format_currency


def test_currency_rule_appended_to_system_prompt():
    system = _with_currency_rule("Summarize spend.")
    assert "INR" in system
    assert "₹" in system
    assert "Never use $" in system or "Never use $, USD" in system
    assert INR_CURRENCY_RULE in system


def test_currency_rule_not_duplicated():
    once = _with_currency_rule("x")
    twice = _with_currency_rule(once)
    assert twice.count("CURRENCY RULE") == 1


def test_user_data_note_mentions_inr():
    note = _with_currency_data_note("Budget: 1000")
    assert "INR" in note
    assert "₹" in note


def test_format_currency_defaults_to_inr():
    assert format_currency(152935.36).startswith("₹")
    assert "$" not in format_currency(100)
