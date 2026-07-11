"""Pipeline step definitions shared by Streamlit UI and API."""

from __future__ import annotations

from enum import Enum


class PipelineStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"
    SKIPPED = "skipped"


AGENT_PIPELINE_STEPS = [
    {"id": "fetch", "title": "Google Ads", "subtitle": "Data fetched", "icon": "📡"},
    {"id": "account", "title": "Account-wise", "subtitle": "MTD & budget", "icon": "📊"},
    {"id": "daily", "title": "Daily-wise", "subtitle": "Daily snapshot", "icon": "📅"},
    {"id": "hourly", "title": "Hourly", "subtitle": "Hour breakdown", "icon": "⏱️"},
    {"id": "campaign", "title": "Campaign-wise", "subtitle": "Per campaign", "icon": "🎯"},
]

VALID_PIPELINE_STEP_IDS = {step["id"] for step in AGENT_PIPELINE_STEPS}

_BADGE = {
    PipelineStepStatus.PENDING.value: ("Pending", "badge-pending"),
    PipelineStepStatus.RUNNING.value: ("Running", "badge-running"),
    PipelineStepStatus.COMPLETE.value: ("Done", "badge-done"),
    PipelineStepStatus.ERROR.value: ("Error", "badge-error"),
    PipelineStepStatus.SKIPPED.value: ("Skipped", "badge-pending"),
}

_FETCH_DONE_LABEL = "Fetched"


def initial_step_status() -> dict[str, str]:
    return {step["id"]: PipelineStepStatus.PENDING.value for step in AGENT_PIPELINE_STEPS}


def badge_label(step_id: str, status: str) -> str:
    if step_id == "fetch" and status == PipelineStepStatus.COMPLETE.value:
        return _FETCH_DONE_LABEL
    return _BADGE.get(status, _BADGE[PipelineStepStatus.PENDING.value])[0]


def step_is_clickable(status: str) -> bool:
    return status in (PipelineStepStatus.COMPLETE.value, PipelineStepStatus.ERROR.value)
