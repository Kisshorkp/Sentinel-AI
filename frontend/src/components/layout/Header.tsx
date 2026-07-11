import { Clock3, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'

interface HeaderProps {
  title: string
  subtitle?: string
  badge?: string
  onRefresh?: () => void
  refreshing?: boolean
}

export function Header({ title, subtitle, badge = 'Live Operations', onRefresh, refreshing }: HeaderProps) {
  const [time, setTime] = useState(() => new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <div className="mb-1 flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-slate-800">{title}</h1>
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700">
            {badge}
          </span>
        </div>
        {subtitle ? <p className="text-sm text-slate-500">{subtitle}</p> : null}
      </div>

      <div className="flex items-center gap-3">
        {onRefresh ? (
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition hover:bg-slate-50 disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'loader-spin' : ''}`} />
            Refresh
          </button>
        ) : null}
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-2 shadow-sm">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Current Time</p>
          <p className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Clock3 className="h-4 w-4 text-brand-600" />
            {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </p>
        </div>
      </div>
    </header>
  )
}
