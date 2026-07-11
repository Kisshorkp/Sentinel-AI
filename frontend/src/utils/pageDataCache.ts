/** Session-scoped cache for Dashboard, Budget Alerts, and Campaign Analysis. */

const DASHBOARD_KEY = 'sg-cache-dashboard-overview'
const BUDGET_ALERTS_KEY = 'sg-cache-budget-alerts'
const CAMPAIGN_ANALYSIS_KEY = 'sg-cache-campaign-analysis'

/** Legacy analyzer session keys used by Budget Alerts. */
const ANALYZER_SESSION_ID_KEY = 'sg-analyzer-session-id'
const ANALYZER_AGENT_REPORT_KEY = 'sg-analyzer-agent-report'

export interface DashboardCacheEntry {
  data: unknown
  usingLiveAgent: boolean
  cachedAt: number
}

export interface BudgetAlertsCacheEntry {
  data: unknown
  sessionId: string | null
  cachedAt: number
}

export interface CampaignAnalysisCacheEntry {
  data: unknown
  selectedCid: string
  chatMessages: Array<{ role: string; content: string }>
  step: 1 | 2 | 3
  cachedAt: number
}

/** In-flight fetch promises — prevent duplicate API hits (e.g. React Strict Mode). */
const inflight = new Map<string, Promise<unknown>>()

function readJson<T>(key: string): T | null {
  try {
    const raw = sessionStorage.getItem(key)
    if (!raw) return null
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

function writeJson(key: string, value: unknown): void {
  try {
    sessionStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Quota / private mode — ignore; pages still work without cache.
  }
}

export function getDashboardCache(): DashboardCacheEntry | null {
  return readJson<DashboardCacheEntry>(DASHBOARD_KEY)
}

export function setDashboardCache(entry: Omit<DashboardCacheEntry, 'cachedAt'>): void {
  writeJson(DASHBOARD_KEY, { ...entry, cachedAt: Date.now() })
}

export function getBudgetAlertsCache(sessionId: string | null): BudgetAlertsCacheEntry | null {
  const entry = readJson<BudgetAlertsCacheEntry>(BUDGET_ALERTS_KEY)
  if (!entry) return null
  if ((entry.sessionId ?? null) !== (sessionId ?? null)) return null
  return entry
}

export function setBudgetAlertsCache(entry: Omit<BudgetAlertsCacheEntry, 'cachedAt'>): void {
  writeJson(BUDGET_ALERTS_KEY, { ...entry, cachedAt: Date.now() })
}

export function getCampaignAnalysisCache(): CampaignAnalysisCacheEntry | null {
  return readJson<CampaignAnalysisCacheEntry>(CAMPAIGN_ANALYSIS_KEY)
}

export function setCampaignAnalysisCache(
  entry: Omit<CampaignAnalysisCacheEntry, 'cachedAt'>,
): void {
  // Full analyzer payloads (~1MB+) can exceed sessionStorage; keep a slim copy.
  const slimData = slimAnalyzerCacheData(entry.data)
  writeJson(CAMPAIGN_ANALYSIS_KEY, { ...entry, data: slimData, cachedAt: Date.now() })
}

function slimAnalyzerCacheData(data: unknown): unknown {
  if (!data || typeof data !== 'object') return data
  const raw = data as Record<string, unknown>
  return {
    ...raw,
    // Keep UI working; drop the heaviest arrays from sessionStorage.
    campaign_rows: Array.isArray(raw.campaign_rows) ? (raw.campaign_rows as unknown[]).slice(0, 50) : [],
    fetch_records_preview: Array.isArray(raw.fetch_records_preview)
      ? (raw.fetch_records_preview as unknown[]).slice(0, 10)
      : [],
    hourly_rows_by_label: {},
  }
}

export function patchCampaignAnalysisCache(
  patch: Partial<Omit<CampaignAnalysisCacheEntry, 'cachedAt'>>,
): void {
  const current = getCampaignAnalysisCache()
  if (!current?.data && !patch.data) return
  writeJson(CAMPAIGN_ANALYSIS_KEY, {
    data: patch.data ?? current?.data ?? null,
    selectedCid: patch.selectedCid ?? current?.selectedCid ?? '',
    chatMessages: patch.chatMessages ?? current?.chatMessages ?? [],
    step: patch.step ?? current?.step ?? 3,
    cachedAt: Date.now(),
  })
}

export function clearCampaignAnalysisCache(): void {
  sessionStorage.removeItem(CAMPAIGN_ANALYSIS_KEY)
  sessionStorage.removeItem(ANALYZER_SESSION_ID_KEY)
  sessionStorage.removeItem(ANALYZER_AGENT_REPORT_KEY)
}

export function clearPageDataCache(): void {
  sessionStorage.removeItem(DASHBOARD_KEY)
  sessionStorage.removeItem(BUDGET_ALERTS_KEY)
  clearCampaignAnalysisCache()
  inflight.clear()
}

export function hasPageDataCache(): boolean {
  return Boolean(
    sessionStorage.getItem(DASHBOARD_KEY) ||
      sessionStorage.getItem(BUDGET_ALERTS_KEY) ||
      sessionStorage.getItem(CAMPAIGN_ANALYSIS_KEY),
  )
}

/** Deduplicate concurrent fetches for the same key. */
export async function withInflight<T>(key: string, factory: () => Promise<T>): Promise<T> {
  const existing = inflight.get(key)
  if (existing) return existing as Promise<T>
  const promise = factory().finally(() => {
    if (inflight.get(key) === promise) inflight.delete(key)
  })
  inflight.set(key, promise)
  return promise
}
