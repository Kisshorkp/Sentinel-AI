import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SpendTrendPoint } from '../../types'

interface SpendTrendChartProps {
  data: SpendTrendPoint[]
}

export function SpendTrendChart({ data }: SpendTrendChartProps) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="day" tick={{ fontSize: 12 }} stroke="#94a3b8" />
          <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
          <Tooltip formatter={(value) => [`₹${Number(value ?? 0).toLocaleString()}`, '']} />
          <Legend />
          <Line type="monotone" dataKey="search" name="Search" stroke="#0284c7" strokeWidth={2.5} dot={false} />
          <Line type="monotone" dataKey="video" name="Video" stroke="#10b981" strokeWidth={2.5} dot={false} />
          <Line type="monotone" dataKey="demandGen" name="Demand Gen" stroke="#f59e0b" strokeWidth={2.5} dot={false} />
          <Line type="monotone" dataKey="pmax" name="PMax" stroke="#8b5cf6" strokeWidth={2.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
