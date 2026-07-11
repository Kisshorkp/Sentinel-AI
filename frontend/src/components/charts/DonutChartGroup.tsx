import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts'
import type { ResourceUsage } from '../../types'

interface DonutChartGroupProps {
  items: ResourceUsage[]
}

export function DonutChartGroup({ items }: DonutChartGroupProps) {
  return (
    <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
      {items.map((item) => {
        const data = [
          { name: 'used', value: item.value },
          { name: 'rest', value: 100 - item.value },
        ]
        return (
          <div key={item.label} className="flex flex-col items-center rounded-2xl bg-slate-50/80 p-4">
            <div className="relative h-28 w-28">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data}
                    innerRadius={34}
                    outerRadius={48}
                    startAngle={90}
                    endAngle={-270}
                    dataKey="value"
                    stroke="none"
                  >
                    <Cell fill={item.color} />
                    <Cell fill="#e2e8f0" />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-bold text-slate-700">{item.value}%</span>
              </div>
            </div>
            <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{item.label}</p>
          </div>
        )
      })}
    </div>
  )
}
