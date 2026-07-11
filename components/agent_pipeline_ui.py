"""Agent pipeline — single-row workflow UI (fetch + 4 agents)."""

from __future__ import annotations

import html

import streamlit as st
import streamlit.components.v1 as components

from models.pipeline_steps import (
    AGENT_PIPELINE_STEPS,
    PipelineStepStatus,
    VALID_PIPELINE_STEP_IDS,
    badge_label,
    initial_step_status,
    step_is_clickable,
)

_PIPELINE_CARD_CSS = """
<style>
.pipeline-card-row [data-testid="column"] .stButton > button {
  width: 100%;
  min-height: 96px;
  border-radius: 10px;
  border: 2px solid #404559;
  background: #262730;
  color: #fafafa;
  white-space: pre-line;
  font-size: 11px;
  line-height: 1.35;
  padding: 8px 6px;
  text-align: left;
}
.pipeline-card-row [data-testid="column"] .stButton > button[kind="primary"] {
  border-color: #21c354;
  box-shadow: 0 0 0 2px rgba(33, 195, 84, 0.35);
}
.pipeline-card-row [data-testid="column"] .stButton > button:disabled {
  opacity: 0.88;
  cursor: not-allowed;
  pointer-events: none;
  border-color: #404559 !important;
  box-shadow: none !important;
}
</style>
"""


def build_pipeline_html(step_status: dict[str, str]) -> str:
    parts = []
    for step in AGENT_PIPELINE_STEPS:
        status = step_status.get(step["id"], PipelineStepStatus.PENDING.value)
        parts.append(f"{step['title']}:{badge_label(step['id'], status)}")
    return " | ".join(parts)


def build_n8n_pipeline_document(step_status: dict[str, str]) -> str:
    return build_pipeline_html(step_status)


def render_pipeline_anchor(step_id: str) -> None:
    st.markdown(
        f'<div data-pipeline-anchor="{html.escape(step_id)}" '
        f'style="scroll-margin-top: 88px;"></div>',
        unsafe_allow_html=True,
    )


def select_pipeline_step(step_id: str) -> None:
    st.session_state["pipeline_selected_step"] = step_id


def sync_pipeline_step_selection() -> str | None:
    query_step = st.query_params.get("pipeline_step")
    if query_step in VALID_PIPELINE_STEP_IDS:
        st.session_state["pipeline_selected_step"] = query_step
        return query_step
    selected = st.session_state.get("pipeline_selected_step")
    if selected in VALID_PIPELINE_STEP_IDS:
        return selected
    return None


def _grid_template(step_count: int) -> str:
    if step_count <= 1:
        return "1fr"
    columns: list[str] = []
    for index in range(step_count):
        columns.append("1fr")
        if index < step_count - 1:
            columns.append("18px")
    return " ".join(columns)


def _node_cell(
    step: dict[str, str],
    status: str,
    *,
    selected: bool = False,
    interactive: bool = False,
) -> str:
    title = html.escape(step["title"])
    subtitle = html.escape(step["subtitle"])
    icon = html.escape(step["icon"])
    step_id = html.escape(step["id"])
    badge_text = html.escape(badge_label(step["id"], status))
    badge_cls = _BADGE.get(status, _BADGE[PipelineStepStatus.PENDING.value])[1]
    if step["id"] == "fetch" and status == PipelineStepStatus.COMPLETE.value:
        badge_cls = "badge-done"

    clickable = interactive and step_is_clickable(status)
    state_class = f"node {status}"
    if clickable:
        state_class += " clickable"
    if selected and clickable:
        state_class += " selected"
    if interactive and not clickable:
        state_class += " locked"

    inner = (
        f'<div class="node-top"><span class="icon">{icon}</span>'
        f'<div><div class="title">{title}</div><div class="sub">{subtitle}</div></div></div>'
        f'<div class="badge {badge_cls}">{badge_text}</div>'
    )

    if clickable:
        return (
            f'<a class="{state_class}" href="?pipeline_step={step_id}" '
            f'target="_self" data-step-id="{step_id}">{inner}</a>'
        )
    return f'<div class="{state_class}" data-step-id="{step_id}">{inner}</div>'


def _pipeline_markup(
    step_status: dict[str, str],
    *,
    selected_step: str | None = None,
    interactive: bool = False,
) -> str:
    cells = []
    for i, step in enumerate(AGENT_PIPELINE_STEPS):
        st_val = step_status.get(step["id"], PipelineStepStatus.PENDING.value)
        cells.append(
            _node_cell(
                step,
                st_val,
                selected=selected_step == step["id"],
                interactive=interactive,
            )
        )
        if i < len(AGENT_PIPELINE_STEPS) - 1:
            cells.append('<div class="arrow">→</div>')
    row = "".join(cells)
    grid = _grid_template(len(AGENT_PIPELINE_STEPS))

    return f"""
<style>
.pipeline-wrap .pipeline{{
  display:grid;
  grid-template-columns:{grid};
  align-items:stretch;
  width:100%;
  gap:0;
}}
.pipeline-wrap .node, .pipeline-wrap a.node{{
  background:#262730;
  border:2px solid #404559;
  border-radius:10px;
  padding:8px 6px 6px;
  min-height:92px;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  text-decoration:none;
  color:inherit;
}}
.pipeline-wrap a.node:hover{{filter:brightness(1.08);transform:translateY(-1px)}}
.pipeline-wrap .node.running{{border-color:#ff7a59;box-shadow:0 0 0 2px rgba(255,122,89,.15)}}
.pipeline-wrap .node.complete{{border-color:#21c354}}
.pipeline-wrap .node.error{{border-color:#ff4b4b}}
.pipeline-wrap .node.locked{{cursor:not-allowed;opacity:.88}}
.pipeline-wrap a.node.clickable{{cursor:pointer}}
.pipeline-wrap a.node.selected{{box-shadow:0 0 0 2px rgba(33,195,84,.35)}}
.pipeline-wrap .node-top{{display:flex;align-items:center;gap:6px}}
.pipeline-wrap .icon{{
  font-size:18px;width:30px;height:30px;display:flex;align-items:center;
  justify-content:center;background:#1a1d24;border-radius:8px;border:1px solid #404559;
}}
.pipeline-wrap .title{{color:#fafafa;font-size:11px;font-weight:700;line-height:1.2}}
.pipeline-wrap .sub{{color:#9ca3af;font-size:9px;margin-top:2px}}
.pipeline-wrap .badge{{
  margin-top:5px;font-size:8px;font-weight:700;text-transform:uppercase;
  padding:2px 6px;border-radius:4px;width:fit-content;
}}
.pipeline-wrap .badge-pending{{background:#31333f;color:#b0b4c1}}
.pipeline-wrap .badge-running{{background:#1a3a6e;color:#7eb6ff}}
.pipeline-wrap .badge-done{{background:#0d4429;color:#7dffb3}}
.pipeline-wrap .badge-error{{background:#4a1212;color:#fca5a5}}
.pipeline-wrap .arrow{{
  display:flex;align-items:center;justify-content:center;
  color:#6b7280;font-size:14px;font-weight:700;padding-top:26px;
}}
</style>
<div class="pipeline-wrap"><div class="pipeline">{row}</div></div>
"""


def _pipeline_iframe_document(step_status: dict[str, str]) -> str:
    cells = []
    for i, step in enumerate(AGENT_PIPELINE_STEPS):
        st_val = step_status.get(step["id"], PipelineStepStatus.PENDING.value)
        cells.append(_node_cell(step, st_val, interactive=False))
        if i < len(AGENT_PIPELINE_STEPS) - 1:
            cells.append('<div class="arrow">→</div>')
    row = "".join(cells)
    grid = _grid_template(len(AGENT_PIPELINE_STEPS))
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0e1117;font-family:system-ui,sans-serif;padding:6px 2px}}
.pipeline{{display:grid;grid-template-columns:{grid};align-items:stretch;width:100%;gap:0}}
.node{{background:#262730;border:2px solid #404559;border-radius:10px;padding:8px 6px 6px;min-height:92px;display:flex;flex-direction:column;justify-content:space-between}}
.node.running{{border-color:#ff7a59;box-shadow:0 0 0 2px rgba(255,122,89,.15)}}
.node.complete{{border-color:#21c354}}
.node.error{{border-color:#ff4b4b}}
.node-top{{display:flex;align-items:center;gap:6px}}
.icon{{font-size:18px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;background:#1a1d24;border-radius:8px;border:1px solid #404559}}
.title{{color:#fafafa;font-size:11px;font-weight:700;line-height:1.2}}
.sub{{color:#9ca3af;font-size:9px;margin-top:2px}}
.badge{{margin-top:5px;font-size:8px;font-weight:700;text-transform:uppercase;padding:2px 6px;border-radius:4px;width:fit-content}}
.badge-pending{{background:#31333f;color:#b0b4c1}}
.badge-running{{background:#1a3a6e;color:#7eb6ff}}
.badge-done{{background:#0d4429;color:#7dffb3}}
.badge-error{{background:#4a1212;color:#fca5a5}}
.arrow{{display:flex;align-items:center;justify-content:center;color:#6b7280;font-size:14px;font-weight:700;padding-top:26px}}
</style></head><body><div class="pipeline">{row}</div></body></html>"""


def _step_card_label(step: dict[str, str], status: str) -> str:
    badge = badge_label(step["id"], status).upper()
    return f"{step['icon']}  {step['title']}\n{step['subtitle']}\n{badge}"


def _render_interactive_pipeline(status: dict[str, str], selected_step: str | None) -> None:
    """Compact pipeline cards — the card itself is clickable (no extra buttons)."""
    st.markdown(_PIPELINE_CARD_CSS, unsafe_allow_html=True)
    columns = st.columns([1, 0.04, 1, 0.04, 1, 0.04, 1, 0.04, 1], gap="small")
    for index, step in enumerate(AGENT_PIPELINE_STEPS):
        step_status = status.get(step["id"], PipelineStepStatus.PENDING.value)
        clickable = step_is_clickable(step_status)
        selected = selected_step == step["id"]
        label = _step_card_label(step, step_status)

        with columns[index * 2]:
            if clickable:
                st.button(
                    label,
                    key=f"pipeline_step_{step['id']}",
                    use_container_width=True,
                    type="primary" if selected else "secondary",
                    on_click=select_pipeline_step,
                    args=(step["id"],),
                )
            else:
                st.button(
                    label,
                    key=f"pipeline_step_{step['id']}",
                    use_container_width=True,
                    disabled=True,
                )

        if index < len(AGENT_PIPELINE_STEPS) - 1:
            with columns[index * 2 + 1]:
                st.markdown(
                    "<div style='text-align:center;color:#6b7280;font-size:1rem;padding-top:2.5rem;'>→</div>",
                    unsafe_allow_html=True,
                )


def render_agent_pipeline(
    step_status: dict[str, str] | None = None,
    *,
    placeholder: st.delta_generator.DeltaGenerator | None = None,
    title: str = "AI Agent Pipeline",
    selected_step: str | None = None,
    interactive: bool = True,
) -> None:
    status = step_status or initial_step_status()
    if selected_step is None:
        selected_step = sync_pipeline_step_selection()

    container = placeholder.container() if placeholder is not None else st.container()
    with container:
        if title:
            st.markdown(f"##### {title}")
        if interactive:
            st.markdown('<div class="pipeline-card-row">', unsafe_allow_html=True)
            _render_interactive_pipeline(status, selected_step)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            components.html(_pipeline_iframe_document(status), height=128, scrolling=False)
