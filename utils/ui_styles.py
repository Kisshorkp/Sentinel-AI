"""Shared Streamlit UI styles."""

from __future__ import annotations

import streamlit as st


def inject_app_styles() -> None:
    st.markdown(
        """
        <style>
        .analyzer-hero {
            background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 55%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
        }
        .analyzer-hero h3 {
            margin: 0 0 0.35rem 0;
            font-size: 1.35rem;
            color: #f8fafc;
        }
        .analyzer-hero p {
            margin: 0;
            color: #94a3b8;
            font-size: 0.92rem;
        }
        div[data-testid="stForm"] {
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 1.1rem 1.25rem 1.25rem;
            background: #111827;
        }
        .grid-header {
            color: #64748b;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            padding: 0.15rem 0 0.35rem;
        }
        .grid-row-label {
            display: flex;
            align-items: center;
            gap: 0.45rem;
            min-height: 2.65rem;
            color: #e2e8f0;
            font-size: 0.92rem;
            font-weight: 500;
        }
        .grid-row-label .icon {
            width: 1.65rem;
            height: 1.65rem;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            background: #1e293b;
            border: 1px solid #334155;
        }
        .section-chip {
            display: inline-block;
            background: #1d4ed8;
            color: #eff6ff;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            margin-bottom: 0.65rem;
        }
        .result-card {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 1rem 1.15rem;
            margin-bottom: 0.75rem;
        }
        .result-account {
            color: #cbd5e1;
            font-size: 0.95rem;
            margin: 0;
        }
        div[data-testid="stFormSubmitButton"] button {
            background: linear-gradient(90deg, #2563eb, #1d4ed8);
            border: none;
            font-weight: 600;
            letter-spacing: 0.02em;
            padding: 0.65rem 1rem;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            border: none;
            color: #fff;
            filter: brightness(1.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_analyzer_hero() -> None:
    st.markdown(
        """
        <div class="analyzer-hero">
            <h3>Campaign Analyzer</h3>
            <p>Configure account details and campaign spend by type, then run analysis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_chip(label: str) -> None:
    st.markdown(f'<span class="section-chip">{label}</span>', unsafe_allow_html=True)


def render_grid_header() -> None:
    c1, c2, c3, c4 = st.columns([2.4, 1.5, 1.3, 1.3])
    with c1:
        st.markdown('<div class="grid-header">Campaign type</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="grid-header">Spend amount</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="grid-header">Start date</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="grid-header">End date</div>', unsafe_allow_html=True)


def render_row_label(icon: str, label: str) -> None:
    st.markdown(
        f'<div class="grid-row-label"><span class="icon">{icon}</span>{label}</div>',
        unsafe_allow_html=True,
    )
