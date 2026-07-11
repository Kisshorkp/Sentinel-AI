import clsx from 'clsx'

interface MetricRowProps {
  items: Array<{ label: string; value: string }>
  columns?: 3 | 4 | 5
}

export function MetricRow({ items, columns = 4 }: MetricRowProps) {
  const gridClass =
    columns === 5 ? 'lg:grid-cols-5' : columns === 3 ? 'lg:grid-cols-3' : 'lg:grid-cols-4'

  return (
    <div className={clsx('grid gap-4 sm:grid-cols-2', gridClass)}>
      {items.map((item) => (
        <div key={item.label} className="rounded-2xl border border-slate-200/80 bg-white px-5 py-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{item.label}</p>
          <p className="mt-1 text-2xl font-bold text-slate-800">{item.value}</p>
        </div>
      ))}
    </div>
  )
}
