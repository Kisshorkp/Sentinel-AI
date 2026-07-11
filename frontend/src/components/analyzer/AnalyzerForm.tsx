import { Play } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import {
  defaultCampaignFields,
  defaultMonthDates,
  type AnalyzerRunPayload,
  type AppConfig,
  type CampaignFieldPayload,
} from '../../services/api'
import { DashboardCard } from '../ui/DashboardCard'

const CAMPAIGN_TYPES = [
  'Search campaigns',
  'Video campaigns',
  'Demand Gen campaigns',
  'Performance Max campaigns',
] as const

interface AnalyzerFormProps {
  config: AppConfig | null
  loading: boolean
  onSubmit: (payload: AnalyzerRunPayload) => void
}

export function AnalyzerForm({ config, loading, onSubmit }: AnalyzerFormProps) {
  const dates = defaultMonthDates()
  const [account, setAccount] = useState('')
  const [accountStart, setAccountStart] = useState(dates.start)
  const [accountEnd, setAccountEnd] = useState(dates.end)
  const [fields, setFields] = useState<Record<string, CampaignFieldPayload>>(defaultCampaignFields())

  useEffect(() => {
    if (config?.default_customer_id) {
      setAccount(config.default_customer_id)
    }
  }, [config?.default_customer_id])

  const updateField = (label: string, patch: Partial<CampaignFieldPayload>) => {
    setFields((prev) => ({ ...prev, [label]: { ...prev[label], ...patch } }))
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!account.trim()) return

    onSubmit({
      account: account.trim(),
      account_start_date: accountStart,
      account_end_date: accountEnd,
      search_campaigns: fields['Search campaigns'],
      video_campaigns: fields['Video campaigns'],
      demand_gen_campaigns: fields['Demand Gen campaigns'],
      performance_max_campaigns: fields['Performance Max campaigns'],
    })
  }

  return (
    <DashboardCard
      title="Campaign Analyzer Form"
      subtitle="Enter account and campaign budgets/dates, then run the live Google Ads pipeline"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <p className="mb-3 text-xs font-bold uppercase tracking-wide text-brand-600">Account setup</p>
          <div className="grid gap-4 md:grid-cols-3">
            <label className="block md:col-span-1">
              <span className="mb-1 block text-sm font-medium text-slate-700">Account / Customer ID</span>
              <input
                value={account}
                onChange={(e) => setAccount(e.target.value)}
                placeholder="e.g. 465-793-6931"
                className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
                required
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Account start</span>
              <input
                type="date"
                value={accountStart}
                onChange={(e) => setAccountStart(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
                required
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Account end</span>
              <input
                type="date"
                value={accountEnd}
                onChange={(e) => setAccountEnd(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
                required
              />
            </label>
          </div>
        </div>

        <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
          <strong>How it works:</strong> Enter values for each campaign type → click Run Analyzer → app uses the latest
          end date and fetches Google Ads data for the last {config?.lookback_days ?? 90} days.
        </div>

        <div>
          <p className="mb-3 text-xs font-bold uppercase tracking-wide text-brand-600">Campaign budgets & dates</p>
          <div className="space-y-3">
            {CAMPAIGN_TYPES.map((label) => (
              <div key={label} className="grid gap-3 rounded-2xl border border-slate-100 p-4 md:grid-cols-4">
                <p className="self-center text-sm font-semibold text-slate-700">{label}</p>
                <label className="block">
                  <span className="mb-1 block text-xs text-slate-500">Budget / limit</span>
                  <input
                    type="number"
                    min={0}
                    step={1000}
                    value={fields[label].budget}
                    onChange={(e) => updateField(label, { budget: Number(e.target.value) })}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </label>
                <label className="block">
                  <span className="mb-1 block text-xs text-slate-500">Start date</span>
                  <input
                    type="date"
                    value={fields[label].start_date}
                    onChange={(e) => updateField(label, { start_date: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </label>
                <label className="block">
                  <span className="mb-1 block text-xs text-slate-500">End date</span>
                  <input
                    type="date"
                    value={fields[label].end_date}
                    onChange={(e) => updateField(label, { end_date: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </label>
              </div>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !config?.google_ads_configured}
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 py-3.5 text-sm font-semibold text-white shadow-lg shadow-brand-600/20 transition hover:bg-brand-700 disabled:opacity-60 md:w-auto md:px-8"
        >
          <Play className="h-4 w-4" />
          {loading ? 'Running Analyzer...' : 'Run Analyzer'}
        </button>
      </form>
    </DashboardCard>
  )
}
