const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

function formatApiDetail(detail: unknown): string {
  if (detail == null) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          const row = item as { loc?: unknown[]; msg?: string; message?: string }
          const where = Array.isArray(row.loc) ? row.loc.filter((p) => p !== 'body').join('.') : ''
          const msg = row.msg || row.message || JSON.stringify(item)
          return where ? `${where}: ${msg}` : msg
        }
        return String(item)
      })
      .filter(Boolean)
      .join(' | ')
  }
  if (typeof detail === 'object') {
    const row = detail as { message?: string; msg?: string }
    return row.message || row.msg || JSON.stringify(detail)
  }
  return String(detail)
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!response.ok) {
    const raw = await response.text()
    try {
      const parsed = JSON.parse(raw) as { detail?: unknown }
      const message = formatApiDetail(parsed.detail) || raw || `Request failed (${response.status})`
      throw new Error(message)
    } catch (error) {
      if (error instanceof Error && error.message !== raw) throw error
    }
    throw new Error(raw || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export interface AppConfig {
  app_title: string
  app_currency: string
  warning_threshold_pct: number
  critical_threshold_pct: number
  google_ads_configured: boolean
  google_ads_missing: string[]
  openrouter_configured: boolean
  lookback_days: number
  default_customer_id: string
  masked_credentials: Record<string, string>
}

export interface DashboardResponse {
  summary: {
    total_budget: number
    total_spend_mtd: number
    utilization_pct: number
    campaigns_at_risk: number
    campaigns_over_budget: number
    projected_overspend: number
    prevented_loss_estimate: number
    total_conversions: number
    avg_cost_per_conversion: number
  }
  campaigns: Array<Record<string, unknown>>
  alerts: Array<Record<string, unknown>>
  chart_rows: Array<{ campaign: string; spend_mtd: number; monthly_budget: number; utilization_pct: number }>
  currency: string
}

export interface RagPayload {
  status: string
  label: string
  emoji: string
  text_color: string
  bg_tint: string
}

export interface GovernanceOverviewResponse {
  account_name: string
  account_cid: string
  context_line: string
  anchor_date: string
  scorecard: {
    health_score: number
    mtd_spend: number
    mtd_target: number
    deviation_pct: number
    rag: RagPayload
    critical_alerts: number
    warning_alerts: number
    managed_spend_mtd: number
    headline: string
    projected_delta: number
  }
  platform_rows: Array<{
    platform: string
    mtd_spend: number
    mtd_target: number
    expected_pace: number
    campaign_count: number
    pacing_pct: number
    rag: RagPayload
    trend_7d: number[]
  }>
  pacing_series: Array<{
    date: string
    day_label: string
    actual_cumulative: number
    expected_pace: number
    target: number
  }>
  alert_summary: {
    yesterday: {
      total: number
      critical: number
      warning: number
      platforms: Record<string, number>
    }
    last_7_days: {
      total: number
      critical: number
      warning: number
      daily: Array<{
        date: string
        label: string
        critical: number
        warning: number
        total: number
      }>
    }
  }
}

export interface DashboardAgentOverviewResponse extends GovernanceOverviewResponse {
  source: string
  window_start?: string
  window_end?: string
  currency?: string
  openrouter_configured?: boolean
  fetch_record_count?: number
  campaign_count?: number
  agent: {
    overall_severity: string
    overall_summary: string
    errors: Record<string, string>
    check_severity: Record<string, number>
    check_by_level: Record<string, number>
    grouped_alerts: Record<string, Array<Record<string, unknown>>>
    alert_count: number
  }
  charts: {
    spend_by_channel: Record<string, number>
    daily_spend_series: Array<{
      date: string
      day: string
      search: number
      video: number
      demandGen: number
      pmax: number
      total: number
    }>
    hourly_today: Array<Record<string, string | number>>
    top_campaigns: Array<{
      campaign: string
      campaign_type: string
      spend_7d_proxy: number
      t1_cost: number
      budget: number
      today_cost: number
    }>
    check_severity: Record<string, number>
    check_by_level: Record<string, number>
  }
}

export interface SampleDataResponse {
  campaigns: Array<Record<string, unknown>>
  stakeholders: string[]
  stakeholder_totals: Record<string, number>
  top_overspend: Array<{ campaign_name: string; stakeholder: string; amount: number }>
  currency: string
}

export interface AnalyzerRunPayload {
  account: string
  account_start_date: string
  account_end_date: string
  search_campaigns: CampaignFieldPayload
  video_campaigns: CampaignFieldPayload
  demand_gen_campaigns: CampaignFieldPayload
  performance_max_campaigns: CampaignFieldPayload
}

export interface CampaignFieldPayload {
  label: string
  budget: number
  start_date: string
  end_date: string
}

export interface AnalyzerRunResponse {
  session_id: string
  analyzer_result: Record<string, unknown>
  agent_report: Record<string, unknown> | null
  step_status: Record<string, string>
  pipeline_errors: Record<string, string>
  fetch_records_preview: Array<Record<string, unknown>>
  fetch_record_count: number
  hourly_rows_by_label: Record<string, Array<Record<string, unknown>>>
  campaign_rows: Array<Record<string, unknown>>
  campaign_hygiene: Record<string, unknown>
  currency: string
  openrouter_configured: boolean
}

export type PipelineAlertItem = {
  id: string
  pipeline_step: string
  severity: 'critical' | 'warning'
  email_sent: boolean
  campaign_type?: string | null
  campaign_id?: string | null
  campaign_name?: string | null
  rule: string
  threshold: string
  actual: string
  message: string
  title: string
  stakeholder?: string
  utilization_pct?: number
  overspend_amount?: number
}

export type PipelineAlertsResponse = {
  grouped_alerts: {
    account: PipelineAlertItem[]
    daily: PipelineAlertItem[]
    hourly: PipelineAlertItem[]
    campaign: PipelineAlertItem[]
  }
  total_count: number
  session_id: string | null
  has_analyzer_session: boolean
  currency: string
  smtp_configured: boolean
  smtp_error: string | null
  message: string | null
}

export type PipelineAlertsPayload = {
  session_id?: string | null
  agent_report?: Record<string, unknown> | null
}

export const api = {
  health: () => request<{ status: string }>('/api/health'),
  config: () => request<AppConfig>('/api/config'),
  dashboard: () => request<DashboardResponse>('/api/dashboard'),
  governanceOverview: () => request<GovernanceOverviewResponse>('/api/governance/overview'),
  dashboardAgentOverview: () => request<DashboardAgentOverviewResponse>('/api/dashboard-agent/overview'),
  sampleData: (stakeholder = 'All') =>
    request<SampleDataResponse>(`/api/sample-data?stakeholder=${encodeURIComponent(stakeholder)}`),
  budgetAlerts: (warning_threshold_pct: number, critical_threshold_pct: number) =>
    request<{ alerts: Array<Record<string, unknown>>; currency: string }>('/api/budget-alerts', {
      method: 'POST',
      body: JSON.stringify({ warning_threshold_pct, critical_threshold_pct }),
    }),
  pipelineAlerts: (payload: PipelineAlertsPayload = {}) =>
    request<PipelineAlertsResponse>('/api/pipeline-alerts', {
      method: 'POST',
      body: JSON.stringify({
        session_id: payload.session_id ?? null,
        agent_report: payload.agent_report ?? null,
      }),
    }),
  runAnalyzer: (payload: AnalyzerRunPayload) =>
    request<AnalyzerRunResponse>('/api/analyzer/run', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  chat: (session_id: string, message: string) =>
    request<{ reply: string; messages: Array<{ role: string; content: string }> }>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ session_id, message }),
    }),
}

export function defaultMonthDates() {
  const today = new Date()
  const y = today.getFullYear()
  const m = today.getMonth()
  const d = today.getDate()
  const pad = (n: number) => String(n).padStart(2, '0')
  return {
    // Local calendar dates — avoid UTC shift from toISOString()
    start: `${y}-${pad(m + 1)}-01`,
    end: `${y}-${pad(m + 1)}-${pad(d)}`,
  }
}

export function defaultCampaignFields(): Record<string, CampaignFieldPayload> {
  const { start, end } = defaultMonthDates()
  const base = { budget: 0, start_date: start, end_date: end }
  return {
    'Search campaigns': { label: 'Search campaigns', ...base },
    'Video campaigns': { label: 'Video campaigns', ...base },
    'Demand Gen campaigns': { label: 'Demand Gen campaigns', ...base },
    'Performance Max campaigns': { label: 'Performance Max campaigns', ...base },
  }
}
