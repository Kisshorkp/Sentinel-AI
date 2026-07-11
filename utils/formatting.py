"""Formatting helpers for UI display."""

from __future__ import annotations


def format_currency(value: float, currency: str = "INR") -> str:
    symbol = {"USD": "$", "INR": "₹", "EUR": "€"}.get(currency.upper(), currency + " ")
    return f"{symbol}{value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value:.1f}%"


def risk_label(level: str) -> str:
    return {
        "healthy": "On Track",
        "warning": "At Risk",
        "critical": "Critical",
        "over_budget": "Over Budget",
    }.get(level, level.title())
