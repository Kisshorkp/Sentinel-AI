import clsx from 'clsx'
import { useMemo, useState } from 'react'
import type { AnalyzerRunResponse } from '../../services/api'
import { formatCurrency, formatPercent, severityIcon } from '../../utils/format'
import { getRagStatus } from '../../utils/rag_status'
import { DashboardCard } from '../ui/DashboardCard'
import { DataTable } from '../ui/DataTable'
import { MetricRow } from '../ui/MetricRow'
import { PIPELINE_STEPS } from './PipelineSteps'

interface PipelineTabsProps {
  data: AnalyzerRunResponse
}

type FieldRow = {
  label: string
  budget: number
  cost: number
  mtd_target: number
  mtd_achieve: number
  budget_utilization_pct?: number
  t1_date?: string
  t1_cost: number
  t2_date?: string
  t2_cost: number
  today_cost: number
  t1_7day_avg_cost: number
}

type AgentCheck = {
  rule?: string
  threshold?: string
  actual?: string
  status?: string
  message?: string
}

type CampaignAgentReport = {
  campaign_type?: string
  campaign_id?: string | null
  campaign_name?: string | null
  severity?: string
  summary?: string
  checks?: AgentCheck[]
}

type AgentReport = {
  analyzer_table?: Array<{ campaign_type?: string; severity?: string; summary?: string }>
  daily_snapshot?: Array<{ campaign_type?: string; severity?: string; summary?: string }>
  hourly_snapshot?: Array<{ campaign_type?: string; severity?: string; summary?: string }>
  campaign_daily_by_type?: CampaignAgentReport[]
  campaign_daily_snapshot?: CampaignAgentReport[]
}

function getFields(data: AnalyzerRunResponse): FieldRow[] {
  const result = data.analyzer_result as { fields?: FieldRow[] }
  return result.fields ?? []
}

function normalizeHourlyRows(rows: Array<Record<string, unknown>>) {
  return [...rows]
    .sort((a, b) => Number(a.Hour ?? 0) - Number(b.Hour ?? 0))
    .map((row) => {
      const keys = Object.keys(row)
      if (keys.length >= 3 && keys[0] === 'Hour') {
        return { ...row, [keys[1]]: row[keys[1]], [keys[2]]: row[keys[2]] }
      }
      return row
    })
}

function SummaryTabs({ reports }: { reports: Array<{ campaign_type?: string; severity?: string; summary?: string }> }) {
  const [active, setActive] = useState(0)
  if (!reports.length) {
    return <p className="text-sm text-slate-500">AI summaries will appear here after OpenRouter is configured.</p>
  }
  const report = reports[active]
  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {reports.map((item, index) => (
          <button
            key={item.campaign_type ?? index}
            type="button"
            onClick={() => setActive(index)}
            className={clsx(
              'rounded-full px-3 py-1.5 text-xs font-semibold transition',
              active === index ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200',
            )}
          >
            {severityIcon(item.severity ?? 'healthy')} {(item.campaign_type ?? 'Type').replace(' campaigns', '')}
          </button>
        ))}
      </div>
      {report?.summary ? (
        <div className="rounded-2xl border border-slate-100 bg-slate-50/80 p-4 text-sm leading-7 text-slate-700">
          {report.summary}
        </div>
      ) : (
        <p className="text-sm text-slate-500">No AI summary available for this campaign type yet.</p>
      )}
    </div>
  )
}

function FetchTab({ data }: PipelineTabsProps) {
  const error = data.pipeline_errors.fetch
  const result = data.analyzer_result as { fetch_start_date?: string; fetch_end_date?: string }

  if (error) {
    return <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-700">{error}</div>
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">
        Google Ads API daily campaign metrics (up to 10 rows).
        {result.fetch_start_date ? ` Fetch window: ${result.fetch_start_date} → ${result.fetch_end_date}.` : ''}
      </p>
      <DataTable
        columns={[
          { key: 'type', label: 'Campaign type' },
          { key: 'date', label: 'Date' },
          { key: 'cost', label: 'Cost', align: 'right' },
        ]}
        rows={data.fetch_records_preview.map((row) => ({
          type: String(row['Campaign type'] ?? ''),
          date: String(row.Date ?? ''),
          cost: formatCurrency(Number(row.Cost ?? 0), data.currency),
        }))}
        emptyMessage="No fetch records available."
      />
      {data.fetch_record_count > 10 ? (
        <p className="text-xs text-slate-400">Showing 10 of {data.fetch_record_count} records.</p>
      ) : null}
    </div>
  )
}

function MtdPaceStatusBadge({ deviationPct }: { deviationPct: number | null }) {
  if (deviationPct == null) {
    return <span className="text-xs text-slate-400">—</span>
  }
  const rag = getRagStatus(deviationPct)
  const sign = deviationPct > 0 ? '+' : ''
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
      style={{ color: rag.textColor, backgroundColor: rag.bgTint }}
      title={
        deviationPct < -5
          ? 'Actual MTD < Expected MTD − 5%'
          : deviationPct > 5
            ? 'Actual MTD > Expected MTD + 5%'
            : 'Actual MTD within ±5% of Expected MTD'
      }
    >
      <span aria-hidden>{rag.emoji}</span>
      <span>{rag.label}</span>
      <span className="font-mono tabular-nums opacity-90">
        {sign}
        {deviationPct.toFixed(1)}%
      </span>
    </span>
  )
}

function AccountTab({ data }: PipelineTabsProps) {
  const fields = getFields(data)
  const agentReport = (data.agent_report ?? {}) as AgentReport
  const currency = data.currency

  const tableRows = fields.map((field) => {
    const deviationPct =
      field.mtd_target > 0
        ? ((field.mtd_achieve - field.mtd_target) / field.mtd_target) * 100
        : null
    return {
      display: {
        type: field.label.replace(' campaigns', ''),
        budget: formatCurrency(field.budget, currency),
        spend: formatCurrency(field.cost, currency),
        mtdTarget: formatCurrency(field.mtd_target, currency),
        mtdAchieve: formatCurrency(field.mtd_achieve, currency),
        budgetUsed: field.budget > 0 ? formatPercent((field.cost / field.budget) * 100) : '—',
        mtdVsTarget: deviationPct != null ? `${deviationPct.toFixed(1)}%` : '—',
        status: <MtdPaceStatusBadge deviationPct={deviationPct} />,
      },
      sort: {
        type: field.label.replace(' campaigns', ''),
        budget: field.budget,
        spend: field.cost,
        mtdTarget: field.mtd_target,
        mtdAchieve: field.mtd_achieve,
        budgetUsed: field.budget > 0 ? (field.cost / field.budget) * 100 : -1,
        mtdVsTarget: deviationPct ?? 0,
        status: deviationPct ?? 0,
      },
    }
  })

  return (
    <div className="space-y-6">
      <MetricRow
        items={[
          { label: 'Total budget', value: formatCurrency(fields.reduce((s, f) => s + f.budget, 0), currency) },
          { label: 'Total spend', value: formatCurrency(fields.reduce((s, f) => s + f.cost, 0), currency) },
          { label: 'Total MTD target', value: formatCurrency(fields.reduce((s, f) => s + f.mtd_target, 0), currency) },
          { label: 'Total MTD achieve', value: formatCurrency(fields.reduce((s, f) => s + f.mtd_achieve, 0), currency) },
        ]}
      />

      <p className="text-xs text-slate-500">
        Status uses MTD pace vs expected: 🟢 Under Spend (actual &lt; expected − 5%) · 🟡 On Track (within ±5%) ·
        🔴 Over Spend (actual &gt; expected + 5%)
      </p>

      <DataTable
        columns={[
          { key: 'type', label: 'Campaign type' },
          { key: 'budget', label: 'Budget', align: 'right' },
          { key: 'spend', label: 'Spend', align: 'right' },
          { key: 'mtdTarget', label: 'MTD target', align: 'right' },
          { key: 'mtdAchieve', label: 'MTD achieve', align: 'right' },
          { key: 'budgetUsed', label: 'Budget used', align: 'right' },
          { key: 'mtdVsTarget', label: 'MTD vs target', align: 'right' },
          { key: 'status', label: 'Status' },
        ]}
        rows={tableRows.map((r) => r.display)}
        sortValues={tableRows.map((r) => r.sort)}
        filterPlaceholder="Filter campaign types…"
      />
      <DashboardCard title="AI Summary by Campaign Type">
        <SummaryTabs reports={agentReport.analyzer_table ?? []} />
      </DashboardCard>
    </div>
  )
}

function DailyTab({ data }: PipelineTabsProps) {
  const fields = getFields(data)
  const agentReport = (data.agent_report ?? {}) as AgentReport
  const t1 = fields[0]?.t1_date ?? 'T-1'
  const t2 = fields[0]?.t2_date ?? 'T-2'

  return (
    <div className="space-y-6">
      <MetricRow
        items={[
          { label: `Total ${t1}`, value: formatCurrency(fields.reduce((s, f) => s + f.t1_cost, 0), data.currency) },
          { label: `Total ${t2}`, value: formatCurrency(fields.reduce((s, f) => s + f.t2_cost, 0), data.currency) },
          { label: "Total today's cost", value: formatCurrency(fields.reduce((s, f) => s + f.today_cost, 0), data.currency) },
          {
            label: 'Total T-1 7-day avg',
            value: formatCurrency(fields.reduce((s, f) => s + f.t1_7day_avg_cost, 0), data.currency),
          },
        ]}
      />
      <DataTable
        columns={[
          { key: 'type', label: 'Campaign type' },
          { key: 't1', label: String(t1), align: 'right' },
          { key: 't2', label: String(t2), align: 'right' },
          { key: 'today', label: "Today's cost", align: 'right' },
          { key: 'avg', label: 'T-1 7-day avg', align: 'right' },
        ]}
        rows={fields.map((field) => ({
          type: field.label.replace(' campaigns', ''),
          t1: formatCurrency(field.t1_cost, data.currency),
          t2: formatCurrency(field.t2_cost, data.currency),
          today: formatCurrency(field.today_cost, data.currency),
          avg: formatCurrency(field.t1_7day_avg_cost, data.currency),
        }))}
      />
      <DashboardCard title="AI Summary by Campaign Type">
        <SummaryTabs reports={agentReport.daily_snapshot ?? []} />
      </DashboardCard>
    </div>
  )
}

function HourlyTab({ data }: PipelineTabsProps) {
  const hourlyByLabel = data.hourly_rows_by_label
  const labels = Object.keys(hourlyByLabel)
  const agentReport = (data.agent_report ?? {}) as AgentReport
  const [selected, setSelected] = useState(labels[0] ?? '')

  const overview = useMemo(() => {
    const hour = new Date().getHours()
    return labels.map((label) => {
      const rows = hourlyByLabel[label] ?? []
      const row = rows.find((item) => Number(item.Hour) === hour)
      const today = Number(row?.["Today's cost"] ?? 0)
      const avg = Number(row?.['T-1 7-day avg cost'] ?? 0)
      const pct = avg > 0 ? ((today - avg) / avg) * 100 : null
      return { label, today, avg, pct, hour }
    })
  }, [hourlyByLabel, labels])

  const totalToday = overview.reduce((s, row) => s + row.today, 0)
  const totalAvg = overview.reduce((s, row) => s + row.avg, 0)
  const totalPct = totalAvg > 0 ? ((totalToday - totalAvg) / totalAvg) * 100 : null
  const displayHour = overview[0]?.hour ?? new Date().getHours()
  const selectedRows = normalizeHourlyRows(hourlyByLabel[selected] ?? [])
  const selectedReport = (agentReport.hourly_snapshot ?? []).find((r) => r.campaign_type === selected)

  if (!labels.length) {
    return <p className="text-sm text-slate-500">Hourly data is not loaded yet.</p>
  }

  const costColumns = selectedRows[0]
    ? Object.keys(selectedRows[0]).filter((key) => key !== 'Hour')
    : []

  return (
    <div className="space-y-6">
      <MetricRow
        items={[
          { label: 'Current hour (0–23)', value: String(displayHour) },
          { label: 'Total current-hour spend', value: formatCurrency(totalToday, data.currency) },
          { label: 'Total same-hour 7-day avg', value: formatCurrency(totalAvg, data.currency) },
          { label: 'Vs 7-day avg', value: totalPct != null ? `${totalPct.toFixed(1)}%` : '—' },
        ]}
      />
      <DataTable
        columns={[
          { key: 'type', label: 'Campaign type' },
          { key: 'hour', label: 'Current hour' },
          { key: 'today', label: "Today's cost", align: 'right' },
          { key: 'avg', label: 'T-1 7-day avg', align: 'right' },
          { key: 'pct', label: 'Vs 7-day avg', align: 'right' },
        ]}
        rows={overview.map((row) => ({
          type: row.label.replace(' campaigns', ''),
          hour: String(row.hour),
          today: formatCurrency(row.today, data.currency),
          avg: formatCurrency(row.avg, data.currency),
          pct: row.pct != null ? `${row.pct.toFixed(1)}%` : '—',
        }))}
      />

      <DashboardCard title="Hourly Breakdown by Campaign Type">
        <div className="mb-4 flex flex-wrap gap-2">
          {labels.map((label) => (
            <button
              key={label}
              type="button"
              onClick={() => setSelected(label)}
              className={clsx(
                'rounded-full px-3 py-1.5 text-xs font-semibold transition',
                selected === label ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600',
              )}
            >
              {label.replace(' campaigns', '')}
            </button>
          ))}
        </div>
        <p className="mb-3 text-xs text-slate-500">Hour 0 = 12:00 AM–12:59 AM · Hour 23 = 11:00 PM–11:59 PM</p>
        <DataTable
          key={selected}
          columns={[
            { key: 'hour', label: 'Hour' },
            ...costColumns.map((col) => ({ key: col, label: col, align: 'right' as const })),
          ]}
          filterPlaceholder="Filter hourly rows…"
          rows={selectedRows.map((row) => {
            const mapped: Record<string, string> = { hour: String(row.Hour ?? '') }
            costColumns.forEach((col) => {
              mapped[col] = formatCurrency(Number(row[col] ?? 0), data.currency)
            })
            return mapped
          })}
          sortValues={selectedRows.map((row) => {
            const mapped: Record<string, number> = { hour: Number(row.Hour ?? 0) }
            costColumns.forEach((col) => {
              mapped[col] = Number(row[col] ?? 0)
            })
            return mapped
          })}
        />
        {selectedReport?.summary ? (
          <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50/80 p-4 text-sm leading-7 text-slate-700">
            <p className="mb-2 font-semibold">AI summary</p>
            {selectedReport.summary}
          </div>
        ) : null}
      </DashboardCard>
    </div>
  )
}

function formatCampaignDate(value: unknown): string {
  if (!value) return '—'
  const text = String(value).slice(0, 10)
  // Google Ads open-ended campaigns use a far-future date.
  if (text >= '2037-12-01') return 'Open-ended'
  return text
}

function CampaignAlertCell({
  severity,
  checks,
}: {
  severity?: string
  checks: AgentCheck[]
}) {
  if (!checks.length) {
    return <span className="text-xs font-medium text-emerald-600">OK</span>
  }

  const failCount = checks.filter((c) => c.status === 'fail').length
  const warnCount = checks.filter((c) => c.status === 'warning').length
  const tone =
    severity === 'critical' || failCount > 0
      ? 'bg-red-50 text-red-700 border-red-100'
      : 'bg-amber-50 text-amber-800 border-amber-100'

  return (
    <div className="min-w-[220px] space-y-1.5">
      <span className={clsx('inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold', tone)}>
        {severityIcon(severity ?? (failCount ? 'critical' : 'warning'))}{' '}
        {failCount ? `${failCount} fail` : ''}
        {failCount && warnCount ? ' · ' : ''}
        {warnCount ? `${warnCount} warn` : ''}
      </span>
      <ul className="space-y-1 text-[11px] leading-snug text-slate-600">
        {checks.slice(0, 4).map((check, idx) => (
          <li key={`${check.rule}-${idx}`}>
            <span className="font-semibold text-slate-800">{check.rule}</span>
            {check.message ? ` — ${check.message}` : check.actual ? ` — ${check.actual}` : ''}
          </li>
        ))}
        {checks.length > 4 ? (
          <li className="text-slate-400">+{checks.length - 4} more</li>
        ) : null}
      </ul>
    </div>
  )
}

function CampaignTab({ data }: PipelineTabsProps) {
  const rows = data.campaign_rows as Array<Record<string, unknown>>
  const agentReport = (data.agent_report ?? {}) as AgentReport
  const labels = [...new Set(rows.map((row) => String(row.campaign_type ?? '')))]
  const [selected, setSelected] = useState(labels[0] ?? '')
  const [issuesOnly, setIssuesOnly] = useState(false)
  const t1 = String(rows[0]?.t1_date ?? 'T-1')
  const t2 = String(rows[0]?.t2_date ?? 'T-2')

  const checksByCampaignId = useMemo(() => {
    const map = new Map<string, CampaignAgentReport>()
    for (const report of agentReport.campaign_daily_snapshot ?? []) {
      if (report.campaign_id) map.set(String(report.campaign_id), report)
    }
    return map
  }, [agentReport.campaign_daily_snapshot])

  const typeRows = rows.filter((row) => String(row.campaign_type) === selected)
  const selectedReport = (agentReport.campaign_daily_by_type ?? []).find((r) => r.campaign_type === selected)
  const typeLevelAlerts = (selectedReport?.checks ?? []).filter((c) => c.status && c.status !== 'pass')

  const enriched = useMemo(() => {
    return typeRows.map((row) => {
      const id = String(row.campaign_id ?? '')
      const report = checksByCampaignId.get(id)
      const failing = (report?.checks ?? []).filter((c) => c.status && c.status !== 'pass')
      return { row, report, failing }
    })
  }, [typeRows, checksByCampaignId])

  const visible = issuesOnly ? enriched.filter((item) => item.failing.length > 0) : enriched
  const criticalCount = enriched.filter((item) => item.report?.severity === 'critical').length
  const warningCount = enriched.filter((item) => item.report?.severity === 'warning').length

  if (!rows.length) {
    return <p className="text-sm text-slate-500">No campaign-level records available.</p>
  }

  return (
    <div className="space-y-6">
      <MetricRow
        items={[
          { label: 'Total campaigns', value: String(rows.length) },
          { label: 'Campaign types', value: String(labels.length) },
          {
            label: "Total today's cost",
            value: formatCurrency(rows.reduce((s, row) => s + Number(row.today_cost ?? 0), 0), data.currency),
          },
          {
            label: 'Total T-1 cost',
            value: formatCurrency(rows.reduce((s, row) => s + Number(row.t1_cost ?? 0), 0), data.currency),
          },
        ]}
      />

      <DashboardCard title="Campaign Data by Type">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {labels.map((label) => (
            <button
              key={label}
              type="button"
              onClick={() => setSelected(label)}
              className={clsx(
                'rounded-full px-3 py-1.5 text-xs font-semibold transition',
                selected === label ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600',
              )}
            >
              {label.replace(' campaigns', '')}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setIssuesOnly((v) => !v)}
            className={clsx(
              'ml-auto rounded-full px-3 py-1.5 text-xs font-semibold transition',
              issuesOnly ? 'bg-amber-500 text-white' : 'border border-slate-200 bg-white text-slate-600',
            )}
          >
            {issuesOnly ? 'Showing alerts only' : 'Show alerts only'}
          </button>
        </div>

        <div className="mb-4 flex flex-wrap gap-3 text-xs">
          <span className="rounded-lg bg-red-50 px-3 py-1.5 font-semibold text-red-700">
            Critical: {criticalCount}
          </span>
          <span className="rounded-lg bg-amber-50 px-3 py-1.5 font-semibold text-amber-700">
            Warning: {warningCount}
          </span>
          <span className="rounded-lg bg-slate-100 px-3 py-1.5 font-semibold text-slate-600">
            Shown: {visible.length} / {typeRows.length}
          </span>
        </div>

        {typeLevelAlerts.length > 0 ? (
          <div className="mb-4 space-y-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Type-level alerts</p>
            {typeLevelAlerts.map((check, idx) => (
              <p key={`${check.rule}-${idx}`} className="text-sm text-amber-900">
                <span className="font-semibold">{check.rule}</span>
                {check.message ? ` — ${check.message}` : ''}
                {check.actual ? ` (${check.actual})` : ''}
              </p>
            ))}
          </div>
        ) : null}

        <DataTable
          key={`${selected}-${issuesOnly ? 'alerts' : 'all'}`}
          columns={[
            { key: 'name', label: 'Campaign' },
            { key: 'id', label: 'Campaign ID' },
            { key: 'start', label: 'Start Date' },
            { key: 'end', label: 'End Date' },
            { key: 'budget', label: 'Budget', align: 'right' },
            { key: 'status', label: 'Status' },
            { key: 't1', label: t1, align: 'right' },
            { key: 't2', label: t2, align: 'right' },
            { key: 'today', label: "Today's cost", align: 'right' },
            { key: 'avg', label: 'T-1 7-day avg', align: 'right' },
            { key: 'alerts', label: 'Alerts' },
          ]}
          filterPlaceholder="Filter campaigns by name, ID, status…"
          rows={visible.map(({ row, report, failing }) => {
            const period = String(row.budget_period ?? '')
            const budgetLabel = period
              ? `${formatCurrency(Number(row.budget_amount ?? 0), data.currency)} (${period})`
              : formatCurrency(Number(row.budget_amount ?? 0), data.currency)
            return {
              name: String(row.campaign_name ?? ''),
              id: String(row.campaign_id ?? ''),
              start: formatCampaignDate(row.start_date),
              end: formatCampaignDate(row.end_date),
              budget: budgetLabel,
              status: (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                  {String(row.primary_status || '—')}
                </span>
              ),
              t1: formatCurrency(Number(row.t1_cost ?? 0), data.currency),
              t2: formatCurrency(Number(row.t2_cost ?? 0), data.currency),
              today: formatCurrency(Number(row.today_cost ?? 0), data.currency),
              avg: formatCurrency(Number(row.t1_7day_avg_cost ?? 0), data.currency),
              alerts: <CampaignAlertCell severity={report?.severity} checks={failing} />,
            }
          })}
          sortValues={visible.map(({ row, report, failing }) => {
            const failCount = failing.filter((c) => c.status === 'fail').length
            const warnCount = failing.filter((c) => c.status === 'warning').length
            const severityRank =
              report?.severity === 'critical' || failCount > 0 ? 2 : warnCount > 0 ? 1 : 0
            return {
              name: String(row.campaign_name ?? ''),
              id: String(row.campaign_id ?? ''),
              start: formatCampaignDate(row.start_date),
              end: formatCampaignDate(row.end_date),
              budget: Number(row.budget_amount ?? 0),
              status: String(row.primary_status || ''),
              t1: Number(row.t1_cost ?? 0),
              t2: Number(row.t2_cost ?? 0),
              today: Number(row.today_cost ?? 0),
              avg: Number(row.t1_7day_avg_cost ?? 0),
              alerts: severityRank * 1000 + failCount * 10 + warnCount,
            }
          })}
          emptyMessage={issuesOnly ? 'No campaign alerts for this type.' : 'No campaigns available for this type.'}
        />
        {selectedReport?.summary ? (
          <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50/80 p-4 text-sm leading-7 text-slate-700">
            <p className="mb-2 font-semibold">AI summary (all campaigns in this type)</p>
            {selectedReport.summary}
          </div>
        ) : null}
      </DashboardCard>
    </div>
  )
}

export function PipelineTabs({ data }: PipelineTabsProps) {
  const [activeStep, setActiveStep] = useState('fetch')

  const renderStep = () => {
    if (data.pipeline_errors[activeStep]) {
      return (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          {data.pipeline_errors[activeStep]}
        </div>
      )
    }
    switch (activeStep) {
      case 'fetch':
        return <FetchTab data={data} />
      case 'account':
        return <AccountTab data={data} />
      case 'daily':
        return <DailyTab data={data} />
      case 'hourly':
        return <HourlyTab data={data} />
      case 'campaign':
        return <CampaignTab data={data} />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {PIPELINE_STEPS.map((step) => {
          const status = data.step_status[step.id] ?? 'pending'
          return (
            <button
              key={step.id}
              type="button"
              disabled={status === 'pending' || status === 'running'}
              onClick={() => setActiveStep(step.id)}
              className={clsx(
                'rounded-full px-4 py-2 text-xs font-semibold transition',
                activeStep === step.id ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200',
                (status === 'pending' || status === 'running') && 'cursor-not-allowed opacity-50',
                status === 'error' && 'border border-red-200 bg-red-50 text-red-700',
              )}
            >
              {step.icon} {step.title}
            </button>
          )
        })}
      </div>
      {renderStep()}
    </div>
  )
}
