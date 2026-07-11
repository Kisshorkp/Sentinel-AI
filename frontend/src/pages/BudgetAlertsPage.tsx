import clsx from 'clsx'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { Header } from '../components/layout/Header'
import { BudgetAlertsLoader } from '../components/alerts/BudgetAlertsLoader'
import { DashboardCard } from '../components/ui/DashboardCard'
import { useAnalyzer } from '../context/AnalyzerContext'
import { api, type PipelineAlertItem, type PipelineAlertsResponse } from '../services/api'
import { loadAnalyzerSession } from '../utils/analyzerSessionStorage'
import { formatCurrency, severityBadgeClass } from '../utils/format'
import { getBudgetAlertsCache, setBudgetAlertsCache, withInflight } from '../utils/pageDataCache'

type AlertTab = 'account' | 'daily' | 'hourly' | 'campaign'

const TAB_CONFIG: Array<{ id: AlertTab; label: string; description: string }> = [
  {
    id: 'account',
    label: 'Account-wise',
    description: 'Account-level spend checks from the analyzer pipeline.',
  },
  {
    id: 'daily',
    label: 'Daily-wise',
    description: 'Daily snapshot threshold checks across campaign types.',
  },
  {
    id: 'hourly',
    label: 'Hourly',
    description: 'Hourly spend pacing and spike checks.',
  },
  {
    id: 'campaign',
    label: 'Campaign-wise',
    description: 'Individual campaign hygiene and daily spend checks.',
  },
]

export function BudgetAlertsPage() {
  const { analyzerData } = useAnalyzer()
  const analyzerSession = loadAnalyzerSession()
  const sessionKey = analyzerData?.session_id ?? analyzerSession.session_id ?? null
  const initialCache = getBudgetAlertsCache(sessionKey)

  const [loading, setLoading] = useState(!initialCache)
  const [activeTab, setActiveTab] = useState<AlertTab>('account')
  const [data, setData] = useState<PipelineAlertsResponse | null>(
    () => (initialCache?.data as PipelineAlertsResponse | null) ?? null,
  )

  const loadAlerts = useCallback(
    async (opts?: { force?: boolean }) => {
      const force = opts?.force ?? false
      const cachedSession = loadAnalyzerSession()
      const session_id = analyzerData?.session_id ?? cachedSession.session_id ?? null
      const agent_report = analyzerData?.agent_report ?? cachedSession.agent_report ?? null

      if (!force) {
        const hit = getBudgetAlertsCache(session_id)
        if (hit?.data) {
          setData(hit.data as PipelineAlertsResponse)
          setLoading(false)
          return
        }
      }

      setLoading(true)
      try {
        const fetchOnce = () => api.pipelineAlerts({ session_id, agent_report })
        const response = force
          ? await fetchOnce()
          : await withInflight(`budget-alerts:${session_id ?? 'none'}`, fetchOnce)
        setData(response)
        setBudgetAlertsCache({ data: response, sessionId: session_id })
      } catch (error) {
        toast.error('Failed to load alerts', {
          description: error instanceof Error ? error.message : 'Is the API server running?',
        })
      } finally {
        setLoading(false)
      }
    },
    [analyzerData?.session_id, analyzerData?.agent_report],
  )

  useEffect(() => {
    loadAlerts()
  }, [loadAlerts])

  const grouped = data?.grouped_alerts ?? { account: [], daily: [], hourly: [], campaign: [] }
  const activeAlerts = grouped[activeTab]
  const totalCount = data?.total_count ?? 0
  const hasAnalyzerSession = data?.has_analyzer_session ?? false
  const smtpConfigured = data?.smtp_configured ?? false
  const smtpError = data?.smtp_error ?? null
  const currency = data?.currency ?? 'INR'

  return (
    <div>
      <Header
        title="Budget Alerts"
        subtitle="Pipeline alerts from your latest Run Analyzer session"
        badge="Alert Center"
        onRefresh={() => loadAlerts({ force: true })}
        refreshing={loading}
      />

      {loading ? (
        <BudgetAlertsLoader />
      ) : (
        <DashboardCard title={`Active Alerts (${totalCount})`}>
          {!hasAnalyzerSession ? (
            <div className="mb-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {data?.message ?? 'No analyzer results yet.'} Go to{' '}
              <Link to="/campaign-analysis" className="font-semibold underline">
                Campaign Analysis
              </Link>{' '}
              and click <strong>Run Analyzer</strong> to populate alerts from the pipeline checks.
            </div>
          ) : null}

          {hasAnalyzerSession && smtpError ? (
            <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">
              <strong>Email delivery blocked:</strong> {smtpError}
            </div>
          ) : hasAnalyzerSession && !smtpConfigured ? (
            <div className="mb-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              Email delivery is disabled — add <strong>SMTP_HOST</strong>, <strong>SMTP_USER</strong>, and{' '}
              <strong>SMTP_PASSWORD</strong> to your <code className="text-xs">.env</code> file. Critical
              alerts will show <strong>Not sent</strong> until SMTP is configured.
            </div>
          ) : null}

          <div className="mb-4 flex flex-wrap gap-2 border-b border-slate-200 pb-2">
            {TAB_CONFIG.map((tab) => {
              const count = grouped[tab.id].length
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={clsx(
                    'rounded-t-xl px-4 py-2 text-sm font-semibold transition',
                    activeTab === tab.id
                      ? 'border border-b-white border-slate-200 bg-white text-brand-700'
                      : 'text-slate-500 hover:text-slate-700',
                  )}
                >
                  {tab.label}
                  <span
                    className={clsx(
                      'ml-2 inline-flex min-w-[1.25rem] justify-center rounded-full px-1.5 py-0.5 text-xs',
                      count > 0 ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-500',
                    )}
                  >
                    {count}
                  </span>
                </button>
              )
            })}
          </div>

          <p className="mb-4 text-sm text-slate-500">
            {TAB_CONFIG.find((tab) => tab.id === activeTab)?.description}
          </p>

          {!hasAnalyzerSession ? null : !activeAlerts.length ? (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-800">
              No {TAB_CONFIG.find((tab) => tab.id === activeTab)?.label.toLowerCase()} alerts — all checks
              passed.
            </div>
          ) : (
            <div className="space-y-3">
              {activeAlerts.map((alert) => (
                <AlertCard key={alert.id} alert={alert} currency={currency} smtpConfigured={smtpConfigured} />
              ))}
            </div>
          )}
        </DashboardCard>
      )}
    </div>
  )
}

function AlertCard({
  alert,
  currency,
  smtpConfigured,
}: {
  alert: PipelineAlertItem
  currency: string
  smtpConfigured: boolean
}) {
  const isCritical = alert.severity === 'critical'
  const tone = isCritical
    ? 'border-red-200 bg-red-50 text-red-900'
    : 'border-sky-200 bg-sky-50 text-sky-900'

  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm ${tone}`}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <strong className="text-base">{alert.title}</strong>
          <p className="mt-1">{alert.message}</p>
        </div>
        <span
          className={`inline-flex shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${severityBadgeClass(alert.severity)}`}
        >
          {isCritical ? 'Critical' : 'Warning'}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs opacity-90">
        <span>
          <strong>Email:</strong>{' '}
          {isCritical ? (
            alert.email_sent ? (
              <span className="font-semibold text-emerald-700">Sent</span>
            ) : smtpConfigured ? (
              <span className="font-semibold text-slate-600">Not sent</span>
            ) : (
              <span className="font-semibold text-amber-700">Not sent (SMTP not configured)</span>
            )
          ) : (
            <span className="text-slate-500">Not required (warning)</span>
          )}
        </span>
        <span>
          <strong>Rule:</strong> {alert.rule}
        </span>
        <span>
          <strong>Threshold:</strong> {alert.threshold}
        </span>
        <span>
          <strong>Actual:</strong> {alert.actual}
        </span>
        {alert.campaign_id ? (
          <span>
            <strong>Campaign ID:</strong> {alert.campaign_id}
          </span>
        ) : null}
        {alert.utilization_pct != null ? (
          <span>
            <strong>Utilization:</strong> {alert.utilization_pct.toFixed(1)}%
          </span>
        ) : null}
        {alert.overspend_amount != null && alert.overspend_amount > 0 ? (
          <span>
            <strong>Overspend:</strong> {formatCurrency(alert.overspend_amount, currency)}
          </span>
        ) : null}
        {alert.stakeholder ? (
          <span>
            <strong>Stakeholder:</strong> {alert.stakeholder}
          </span>
        ) : null}
      </div>
    </div>
  )
}
