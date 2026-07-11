import { Bot, RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import {
  ChannelSpendPie,
  CheckLevelPie,
  CheckSeverityPie,
  DailySpendTrendChart,
  HourlySpendBarChart,
  TopCampaignsBar,
} from '../components/governance/DashboardAgentCharts'
import { AlertVolumeChart, MtdPacingChart, Sparkline } from '../components/governance/GovernanceCharts'
import { DashboardLoader } from '../components/governance/DashboardLoader'
import { HeadlineInsight } from '../components/governance/HeadlineInsight'
import { RagBadge } from '../components/governance/RagBadge'
import { api, type DashboardAgentOverviewResponse, type GovernanceOverviewResponse } from '../services/api'
import { formatInr, formatPct } from '../utils/format_inr'
import { getDashboardCache, setDashboardCache, withInflight } from '../utils/pageDataCache'
import '../styles/governance.css'

type PlatformFilter = 'all' | string

function KpiBlock({
  label,
  value,
  sub,
  tone,
}: {
  label: string
  value: ReactNode
  sub?: ReactNode
  tone?: 'critical' | 'warning'
}) {
  const toneStyle =
    tone === 'critical' ? { color: '#B23A32' } : tone === 'warning' ? { color: '#B0791A' } : undefined

  return (
    <div className="min-w-0 flex-1">
      <p className="gov-label mb-2">{label}</p>
      <div className="font-display text-[2rem] font-medium leading-none text-[var(--gov-ink)]" style={toneStyle}>
        {value}
      </div>
      {sub ? <div className="mt-1 text-sm text-[var(--gov-muted)]">{sub}</div> : null}
    </div>
  )
}

function isAgentPayload(data: GovernanceOverviewResponse | DashboardAgentOverviewResponse): data is DashboardAgentOverviewResponse {
  return 'charts' in data && 'agent' in data
}

export function DashboardPage() {
  const cached = getDashboardCache()
  const [loading, setLoading] = useState(!cached)
  const [refreshing, setRefreshing] = useState(false)
  const [data, setData] = useState<GovernanceOverviewResponse | DashboardAgentOverviewResponse | null>(
    () => (cached?.data as GovernanceOverviewResponse | DashboardAgentOverviewResponse | null) ?? null,
  )
  const [usingLiveAgent, setUsingLiveAgent] = useState(() => cached?.usingLiveAgent ?? false)
  const [platformFilter, setPlatformFilter] = useState<PlatformFilter>('all')

  const load = useCallback(async (opts?: { silent?: boolean; force?: boolean }) => {
    const silent = opts?.silent ?? false
    const force = opts?.force ?? false

    if (!force) {
      const hit = getDashboardCache()
      if (hit?.data) {
        setData(hit.data as GovernanceOverviewResponse | DashboardAgentOverviewResponse)
        setUsingLiveAgent(hit.usingLiveAgent)
        setLoading(false)
        setRefreshing(false)
        return
      }
    }

    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      const fetchOnce = async () => {
        try {
          const live = await api.dashboardAgentOverview()
          return { data: live, usingLiveAgent: true as const }
        } catch (liveError) {
          const fallback = await api.governanceOverview()
          return { data: fallback, usingLiveAgent: false as const, liveError }
        }
      }
      const result = force ? await fetchOnce() : await withInflight('dashboard-overview', fetchOnce)

      setData(result.data)
      setUsingLiveAgent(result.usingLiveAgent)
      setDashboardCache({ data: result.data, usingLiveAgent: result.usingLiveAgent })

      if (!result.usingLiveAgent && 'liveError' in result && result.liveError) {
        toast.message('Showing demo governance data', {
          description:
            result.liveError instanceof Error
              ? result.liveError.message
              : 'Live Google Ads dashboard agent unavailable — check credentials / API.',
        })
      }
    } catch (error) {
      toast.error('Failed to load dashboard', {
        description: error instanceof Error ? error.message : 'Is the API server running on port 8000?',
      })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const filteredPlatforms = useMemo(() => {
    if (!data) return []
    if (platformFilter === 'all') return data.platform_rows
    return data.platform_rows.filter((row) => row.platform === platformFilter)
  }, [data, platformFilter])

  if (loading || !data) {
    return <DashboardLoader />
  }

  const { scorecard, alert_summary: alerts } = data
  const agentData = isAgentPayload(data) ? data : null

  return (
    <div className="governance-page -mx-2 rounded-2xl bg-[#F4F6F8] px-2 pb-8 pt-2 lg:-mx-4 lg:px-4">
      <header className="gov-topbar">
        <div className="flex items-start gap-3">
          <div className="gov-logo-glyph" aria-hidden>
            SA
          </div>
          <div>
            <h1 className="font-display text-2xl font-medium text-[var(--gov-ink)]">Spend Governance Dashboard</h1>
            <p className="gov-label mt-1 normal-case tracking-[0.12em]">
              {usingLiveAgent ? 'Live Google Ads · AI agent checks' : 'Spend governance (demo)'}
            </p>
          </div>
        </div>
        <div className="flex items-start gap-4">
          <div className="text-right">
            <p className="text-sm font-semibold text-[var(--gov-ink)]">{data.account_name}</p>
            <p className="mt-0.5 text-xs text-[var(--gov-faint)]">
              {data.context_line} · CID {data.account_cid}
            </p>
            {usingLiveAgent ? (
              <p className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-[var(--gov-steel)]">
                <Bot className="h-3 w-3" /> Dashboard LangGraph agent
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() => load({ silent: true, force: true })}
            disabled={refreshing}
            title="Refresh data (bypass cache)"
            className="rounded-xl border border-[var(--gov-hairline)] bg-white p-2.5 text-[var(--gov-muted)] shadow-sm transition hover:border-[var(--gov-steel)] hover:text-[var(--gov-steel)] disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      <section className="gov-card mb-6 p-6">
        <div className="flex flex-wrap gap-8 lg:flex-nowrap">
          <KpiBlock
            label="MTD spend vs target"
            value={<span className="font-mono-num">{formatInr(scorecard.mtd_spend, true)}</span>}
            sub={
              <span>
                of <span className="font-mono-num">{formatInr(scorecard.mtd_target)}</span> target
              </span>
            }
          />
          <KpiBlock
            label="Critical alerts"
            value={<span className="font-mono-num">{scorecard.critical_alerts}</span>}
            tone="critical"
          />
          <KpiBlock
            label="Warning alerts"
            value={<span className="font-mono-num">{scorecard.warning_alerts}</span>}
            tone="warning"
          />
          <KpiBlock
            label="Total managed spend MTD"
            value={<span className="font-mono-num">{formatInr(scorecard.managed_spend_mtd, true)}</span>}
          />
        </div>

        <div className="gov-hairline my-6" />

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className={`platform-chip ${platformFilter === 'all' ? 'active' : ''}`}
            onClick={() => setPlatformFilter('all')}
          >
            <span className="text-sm font-medium text-[var(--gov-ink)]">All platforms</span>
            <span className="font-mono-num text-sm text-[var(--gov-muted)]">
              {formatPct(scorecard.deviation_pct, true)}
            </span>
          </button>
          {data.platform_rows.map((row) => (
            <button
              key={row.platform}
              type="button"
              className={`platform-chip ${platformFilter === row.platform ? 'active' : ''}`}
              onClick={() => setPlatformFilter(row.platform)}
            >
              <span className="flex items-center gap-2 text-sm font-medium text-[var(--gov-ink)]">
                <span aria-hidden>{row.rag.emoji}</span>
                {row.platform}
              </span>
              <span className="font-mono-num text-sm" style={{ color: row.rag.text_color }}>
                {formatPct(row.pacing_pct, true)}
              </span>
            </button>
          ))}
        </div>
      </section>

      {agentData?.agent.overall_summary ? (
        <section className="gov-card mb-6 p-6">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-display text-lg font-medium text-[var(--gov-ink)]">AI agent summary</h2>
            <span
              className="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide"
              style={{
                background:
                  agentData.agent.overall_severity === 'critical'
                    ? '#FBEDEC'
                    : agentData.agent.overall_severity === 'warning'
                      ? '#FBF3E3'
                      : '#EAF3EE',
                color:
                  agentData.agent.overall_severity === 'critical'
                    ? '#B23A32'
                    : agentData.agent.overall_severity === 'warning'
                      ? '#B0791A'
                      : '#2F7D5B',
              }}
            >
              {agentData.agent.overall_severity}
            </span>
          </div>
          <HeadlineInsight text={agentData.agent.overall_summary} />
          <p className="mt-3 text-xs text-[var(--gov-faint)]">
            Checks: account · daily · hourly · campaign ({agentData.campaign_count ?? 0} campaigns ·{' '}
            {agentData.fetch_record_count ?? 0} daily rows)
          </p>
        </section>
      ) : null}

      <section className="gov-card mb-6 overflow-hidden">
        <div className="border-b border-[var(--gov-hairline-2)] px-6 py-4">
          <h2 className="font-display text-lg font-medium text-[var(--gov-ink)]">Platform-level pacing</h2>
          <p className="mt-1 text-sm text-[var(--gov-muted)]">
            Month-to-date (MTD) spend against expected pace by ad platform
          </p>
        </div>
        <div className="overflow-x-auto px-2 pb-2">
          <table className="gov-table">
            <thead>
              <tr>
                <th>Platform</th>
                <th className="num">MTD spend</th>
                <th className="num">Pacing %</th>
                <th>RAG status</th>
                <th className="num">7-day trend</th>
              </tr>
            </thead>
            <tbody>
              {filteredPlatforms.map((row) => (
                <tr key={row.platform}>
                  <td className="strong">{row.platform}</td>
                  <td className="num font-mono-num">{formatInr(row.mtd_spend)}</td>
                  <td className="num font-mono-num">{formatPct(row.pacing_pct, true)}</td>
                  <td>
                    <RagBadge rag={row.rag} />
                  </td>
                  <td className="num">
                    <div className="inline-flex justify-end">
                      <Sparkline values={row.trend_7d} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="gov-card mb-6 p-6">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="font-display text-lg font-medium text-[var(--gov-ink)]">Account MTD pacing</h2>
            <p className="mt-1 text-sm text-[var(--gov-muted)]">
              Actual cumulative spend vs expected pace through {data.anchor_date}
            </p>
          </div>
          <RagBadge rag={scorecard.rag} pct={scorecard.deviation_pct} />
        </div>
        <HeadlineInsight text={scorecard.headline} />
        <div className="mt-6">
          <MtdPacingChart data={data.pacing_series} deviationPct={scorecard.deviation_pct} />
        </div>
      </section>

      {agentData ? (
        <>
          <section className="mb-6 grid gap-6 lg:grid-cols-2">
            <div className="gov-card p-6">
              <h3 className="font-display mb-1 text-base font-medium text-[var(--gov-ink)]">
                7-day spend by channel
              </h3>
              <p className="mb-4 text-sm text-[var(--gov-muted)]">Share of spend across Google Ads channel types</p>
              <ChannelSpendPie data={agentData.charts.spend_by_channel} />
            </div>
            <div className="gov-card p-6">
              <h3 className="font-display mb-1 text-base font-medium text-[var(--gov-ink)]">Check outcomes</h3>
              <p className="mb-4 text-sm text-[var(--gov-muted)]">Pass / warning / fail across all agent checks</p>
              <CheckSeverityPie data={agentData.charts.check_severity} />
            </div>
          </section>

          <section className="mb-6 grid gap-6 lg:grid-cols-2">
            <div className="gov-card p-6">
              <h3 className="font-display mb-1 text-base font-medium text-[var(--gov-ink)]">
                Daily spend (last 7 days)
              </h3>
              <p className="mb-4 text-sm text-[var(--gov-muted)]">Channel-wise daily cost for the lookback window</p>
              <DailySpendTrendChart data={agentData.charts.daily_spend_series} />
            </div>
            <div className="gov-card p-6">
              <h3 className="font-display mb-1 text-base font-medium text-[var(--gov-ink)]">
                Alerts by check level
              </h3>
              <p className="mb-4 text-sm text-[var(--gov-muted)]">
                Account · daily · hourly · campaign failures & warnings
              </p>
              <CheckLevelPie data={agentData.charts.check_by_level} />
            </div>
          </section>

          <section className="mb-6 grid gap-6 lg:grid-cols-2">
            <div className="gov-card p-6">
              <h3 className="font-display mb-1 text-base font-medium text-[var(--gov-ink)]">
                Hourly spend today
              </h3>
              <p className="mb-4 text-sm text-[var(--gov-muted)]">Intraday cost by hour and channel</p>
              <HourlySpendBarChart data={agentData.charts.hourly_today} />
            </div>
            <div className="gov-card p-6">
              <h3 className="font-display mb-1 text-base font-medium text-[var(--gov-ink)]">
                Top campaigns (7-day)
              </h3>
              <p className="mb-4 text-sm text-[var(--gov-muted)]">Highest recent spend campaigns</p>
              <TopCampaignsBar data={agentData.charts.top_campaigns} />
            </div>
          </section>
        </>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="gov-card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-display text-base font-medium text-[var(--gov-ink)]">Active check alerts</h3>
            <Link
              to="/budget-alerts"
              className="text-xs font-semibold uppercase tracking-wider text-[var(--gov-steel)] hover:underline"
            >
              View alerts →
            </Link>
          </div>
          <div className="flex gap-8">
            <div>
              <p className="gov-label mb-1">Total</p>
              <p className="font-display font-mono-num text-3xl text-[var(--gov-ink)]">{alerts.yesterday.total}</p>
            </div>
            <div>
              <p className="gov-label mb-1">Critical</p>
              <p className="font-mono-num text-2xl font-medium text-[#B23A32]">{alerts.yesterday.critical}</p>
            </div>
            <div>
              <p className="gov-label mb-1">Warning</p>
              <p className="font-mono-num text-2xl font-medium text-[#B0791A]">{alerts.yesterday.warning}</p>
            </div>
          </div>
          <div className="gov-hairline my-4" />
          <p className="gov-label mb-2">By platform</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(alerts.yesterday.platforms).map(([platform, count]) => (
              <span
                key={platform}
                className="rounded-lg border border-[var(--gov-hairline)] px-3 py-1.5 text-xs text-[var(--gov-muted)]"
              >
                {platform}{' '}
                <span className="font-mono-num font-medium text-[var(--gov-ink)]">{count}</span>
              </span>
            ))}
          </div>
        </div>

        <div className="gov-card p-6">
          <h3 className="font-display mb-4 text-base font-medium text-[var(--gov-ink)]">Last 7 days</h3>
          <div className="mb-4 flex gap-8">
            <div>
              <p className="gov-label mb-1">Total</p>
              <p className="font-display font-mono-num text-3xl text-[var(--gov-ink)]">{alerts.last_7_days.total}</p>
            </div>
            <div>
              <p className="gov-label mb-1">Critical</p>
              <p className="font-mono-num text-2xl font-medium text-[#B23A32]">{alerts.last_7_days.critical}</p>
            </div>
            <div>
              <p className="gov-label mb-1">Warning</p>
              <p className="font-mono-num text-2xl font-medium text-[#B0791A]">{alerts.last_7_days.warning}</p>
            </div>
          </div>
          <AlertVolumeChart daily={alerts.last_7_days.daily} />
        </div>
      </section>
    </div>
  )
}
