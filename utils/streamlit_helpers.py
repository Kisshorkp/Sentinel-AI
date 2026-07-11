"""Streamlit session and layout helpers."""

from __future__ import annotations

import streamlit as st

from config.settings import AppSettings, get_settings


def init_app() -> AppSettings:
    settings = get_settings()
    st.set_page_config(
        page_title=settings.app_title,
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    return settings


def init_page() -> AppSettings:
    """Initialize a sub-page without calling set_page_config."""
    return get_settings()
