"""In-memory analyzer session store for API chat context."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalyzerSession:
    analyzer_result: Any
    agent_report: Any | None
    hourly_rows_by_label: dict[str, list[dict[str, object]]]
    campaign_rows: list[Any]
    fetch_records: list[dict[str, object]]
    chat_messages: list[dict[str, str]] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, AnalyzerSession] = {}
        self._latest_session_id: str | None = None

    def create(self, session: AnalyzerSession) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = session
        self._latest_session_id = session_id
        return session_id

    def get(self, session_id: str) -> AnalyzerSession | None:
        return self._sessions.get(session_id)

    def get_latest_id(self) -> str | None:
        return self._latest_session_id

    def get_latest(self) -> AnalyzerSession | None:
        if self._latest_session_id is None:
            return None
        return self._sessions.get(self._latest_session_id)

    def append_chat(self, session_id: str, role: str, content: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        session.chat_messages.append({"role": role, "content": content})


session_store = SessionStore()
