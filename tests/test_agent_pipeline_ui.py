"""Tests for agent pipeline UI."""

from __future__ import annotations

from components.agent_pipeline_ui import (
    PipelineStepStatus,
    badge_label,
    build_n8n_pipeline_document,
    build_pipeline_html,
    initial_step_status,
    step_is_clickable,
)


def test_pipeline_summary_includes_fetch_and_agents():
    summary = build_pipeline_html(initial_step_status())
    assert "Google Ads" in summary
    assert "Account-wise" in summary
    assert "Daily-wise" in summary
    assert "Hourly" in summary
    assert "Campaign-wise" in summary


def test_fetch_complete_shows_fetched_label():
    status = initial_step_status()
    status["fetch"] = PipelineStepStatus.COMPLETE.value
    summary = build_pipeline_html(status)
    assert "Fetched" in summary


def test_badge_label_fetch_complete():
    assert badge_label("fetch", PipelineStepStatus.COMPLETE.value) == "Fetched"


def test_step_clickable_only_when_complete_or_error():
    assert not step_is_clickable(PipelineStepStatus.PENDING.value)
    assert not step_is_clickable(PipelineStepStatus.RUNNING.value)
    assert step_is_clickable(PipelineStepStatus.COMPLETE.value)
    assert step_is_clickable(PipelineStepStatus.ERROR.value)


def test_n8n_document_running_state():
    status = initial_step_status()
    status["hourly"] = "running"
    doc = build_n8n_pipeline_document(status)
    assert "Running" in doc
