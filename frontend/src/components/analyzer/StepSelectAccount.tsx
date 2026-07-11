import clsx from 'clsx'
import { ArrowRight, RefreshCw, Shield } from 'lucide-react'
import { useMemo, useState } from 'react'
import { DashboardCard } from '../ui/DashboardCard'
import { DataTable } from '../ui/DataTable'

export type DummyAnalyzer = {
  id: string
  name: string
  cid: string
  platform: string
  last_run: string
  status: 'Healthy' | 'Warning' | 'Critical'
  campaigns: number
}

const DUMMY_ANALYZERS: DummyAnalyzer[] = [
  {
    id: 'a1',
    name: 'LS Brand Search Monitor',
    cid: '465-793-6931',
    platform: 'Google Ads',
    last_run: '2026-07-10 18:20',
    status: 'Warning',
    campaigns: 214,
  },
  {
    id: 'a2',
    name: 'Video Awareness Guardian',
    cid: '465-793-6931',
    platform: 'Google Ads',
    last_run: '2026-07-09 11:05',
    status: 'Healthy',
    campaigns: 48,
  },
  {
    id: 'a3',
    name: 'Demand Gen Pace Check',
    cid: '512-884-2201',
    platform: 'Google Ads',
    last_run: '2026-07-08 16:40',
    status: 'Critical',
    campaigns: 36,
  },
  {
    id: 'a4',
    name: 'PMax Overspend Watch',
    cid: '512-884-2201',
    platform: 'Google Ads',
    last_run: '2026-07-07 09:12',
    status: 'Warning',
    campaigns: 22,
  },
  {
    id: 'a5',
    name: 'Retail Search Portfolio',
    cid: '778-201-4430',
    platform: 'Google Ads',
    last_run: '2026-07-06 14:55',
    status: 'Healthy',
    campaigns: 91,
  },
]

interface StepSelectAccountProps {
  defaultCustomerId?: string
  selectedCid: string
  onSelectCid: (cid: string) => void
  onNext: () => void
}

export function StepSelectAccount({
  defaultCustomerId,
  selectedCid,
  onSelectCid,
  onNext,
}: StepSelectAccountProps) {
  const [shaking, setShaking] = useState(false)
  const [seed, setSeed] = useState(0)

  const accountOptions = useMemo(() => {
    const fromDummy = [...new Set(DUMMY_ANALYZERS.map((item) => item.cid))]
    if (defaultCustomerId && !fromDummy.includes(defaultCustomerId)) {
      fromDummy.unshift(defaultCustomerId)
    }
    return fromDummy
  }, [defaultCustomerId])

  const rows = useMemo(() => {
    const rotated = [...DUMMY_ANALYZERS]
    if (seed > 0) {
      const offset = seed % rotated.length
      return [...rotated.slice(offset), ...rotated.slice(0, offset)]
    }
    return rotated
  }, [seed])

  const filtered = selectedCid ? rows.filter((row) => row.cid === selectedCid) : rows

  const performShake = () => {
    setShaking(true)
    setSeed((s) => s + 1)
    window.setTimeout(() => setShaking(false), 700)
  }

  return (
    <div className="space-y-6">
      <DashboardCard
        title="Campaign analyzers"
        subtitle="Dummy list of analyzers configured for other campaigns / accounts"
        action={
          <button
            type="button"
            onClick={performShake}
            className={clsx(
              'inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50',
              shaking && 'animate-[shake_0.55s_ease-in-out]',
            )}
          >
            <RefreshCw className={clsx('h-3.5 w-3.5', shaking && 'animate-spin')} />
            Perform Shake
          </button>
        }
      >
        <div className="mb-5 grid gap-4 md:grid-cols-[1fr_auto] md:items-end">
          <label className="block max-w-md">
            <span className="mb-1 block text-sm font-medium text-slate-700">Account / Customer ID</span>
            <select
              value={selectedCid}
              onChange={(e) => onSelectCid(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
            >
              <option value="">Select account…</option>
              {accountOptions.map((cid) => (
                <option key={cid} value={cid}>
                  {cid}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            disabled={!selectedCid}
            onClick={onNext}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
          >
            Next
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        <div
          className={clsx(
            'transition',
            shaking && 'origin-center animate-[shake_0.55s_ease-in-out]',
          )}
        >
          <DataTable
            columns={[
              { key: 'name', label: 'Analyzer' },
              { key: 'cid', label: 'CID' },
              { key: 'platform', label: 'Platform' },
              { key: 'campaigns', label: 'Campaigns', align: 'right' },
              { key: 'last_run', label: 'Last run' },
              { key: 'status', label: 'Status' },
            ]}
            filterPlaceholder="Filter analyzers…"
            rows={filtered.map((row) => ({
              name: (
                <span className="inline-flex items-center gap-2 font-medium text-slate-800">
                  <Shield className="h-3.5 w-3.5 text-brand-600" />
                  {row.name}
                </span>
              ),
              cid: row.cid,
              platform: row.platform,
              campaigns: String(row.campaigns),
              last_run: row.last_run,
              status: (
                <span
                  className={clsx(
                    'rounded-full px-2.5 py-1 text-xs font-semibold',
                    row.status === 'Healthy' && 'bg-emerald-100 text-emerald-700',
                    row.status === 'Warning' && 'bg-amber-100 text-amber-700',
                    row.status === 'Critical' && 'bg-red-100 text-red-700',
                  )}
                >
                  {row.status}
                </span>
              ),
            }))}
            sortValues={filtered.map((row) => ({
              name: row.name,
              cid: row.cid,
              platform: row.platform,
              campaigns: row.campaigns,
              last_run: row.last_run,
              status: row.status,
            }))}
            emptyMessage="No dummy analyzers for this account."
          />
        </div>
      </DashboardCard>

      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          20% { transform: translateX(-6px); }
          40% { transform: translateX(6px); }
          60% { transform: translateX(-4px); }
          80% { transform: translateX(4px); }
        }
      `}</style>
    </div>
  )
}
