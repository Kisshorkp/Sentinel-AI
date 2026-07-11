const SESSION_ID_KEY = 'sg-analyzer-session-id'
const AGENT_REPORT_KEY = 'sg-analyzer-agent-report'

export function saveAnalyzerSession(
  sessionId: string,
  agentReport: Record<string, unknown> | null,
) {
  try {
    sessionStorage.setItem(SESSION_ID_KEY, sessionId)
    if (agentReport) {
      sessionStorage.setItem(AGENT_REPORT_KEY, JSON.stringify(agentReport))
    } else {
      sessionStorage.removeItem(AGENT_REPORT_KEY)
    }
  } catch {
    // QuotaExceeded or private mode — keep in-memory analyzer results usable.
    try {
      sessionStorage.setItem(SESSION_ID_KEY, sessionId)
      sessionStorage.removeItem(AGENT_REPORT_KEY)
    } catch {
      /* ignore */
    }
  }
}

export function loadAnalyzerSession(): {
  session_id: string | null
  agent_report: Record<string, unknown> | null
} {
  const session_id = sessionStorage.getItem(SESSION_ID_KEY)
  const raw = sessionStorage.getItem(AGENT_REPORT_KEY)
  if (!raw) {
    return { session_id, agent_report: null }
  }
  try {
    return { session_id, agent_report: JSON.parse(raw) as Record<string, unknown> }
  } catch {
    return { session_id, agent_report: null }
  }
}
