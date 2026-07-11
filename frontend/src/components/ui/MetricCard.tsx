import clsx from 'clsx'
import type { ReactNode } from 'react'

interface MetricCardProps {
  label: string
  value: string
  tone?: 'default' | 'blue' | 'green' | 'orange' | 'red' | 'purple'
  icon?: ReactNode
}

const toneClasses = {
  default: 'text-slate-800',
  blue: 'text-brand-600',
  green: 'text-emerald-600',
  orange: 'text-amber-600',
  red: 'text-red-600',
  purple: 'text-violet-600',
}

export function MetricCard({ label, value, tone = 'default', icon }: MetricCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white px-5 py-4 shadow-sm">
      <div className="mb-1 flex items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
        {icon}
      </div>
      <p className={clsx('text-2xl font-bold tracking-tight', toneClasses[tone])}>{value}</p>
    </div>
  )
}
