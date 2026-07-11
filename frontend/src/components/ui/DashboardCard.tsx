import type { ReactNode } from 'react'

interface DashboardCardProps {
  title: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  className?: string
  headerClassName?: string
}

export function DashboardCard({
  title,
  subtitle,
  action,
  children,
  className = '',
  headerClassName = '',
}: DashboardCardProps) {
  return (
    <section className={`overflow-hidden rounded-3xl border border-slate-200/80 bg-white shadow-sm ${className}`}>
      <div className={`flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-4 ${headerClassName}`}>
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wide text-slate-700">{title}</h3>
          {subtitle ? <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p> : null}
        </div>
        {action}
      </div>
      <div className="p-6">{children}</div>
    </section>
  )
}
