import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatInr } from '../../utils/format_inr'

const CHANNEL_COLORS = ['#2c6e9b', '#2F7D5B', '#B0791A', '#6B5B95']
const SEVERITY_COLORS: Record<string, string> = {
  pass: '#2F7D5B',
  warning: '#B0791A',
  fail: '#B23A32',
}
const LEVEL_COLORS = ['#1f3a5f', '#2c6e9b', '#5e6b7a', '#B0791A']

function pieEntries(data: Record<string, number>) {
  return Object.entries(data)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }))
}

export function ChannelSpendPie({ data }: { data: Record<string, number> }) {
  const chartData = pieEntries(data)
  if (!chartData.length) {
    return <p className="py-12 text-center text-sm text-[var(--gov-faint)]">No channel spend in window</p>
  }
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={2}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={CHANNEL_COLORS[i % CHANNEL_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(v) => formatInr(Number(v ?? 0))} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function CheckSeverityPie({ data }: { data: Record<string, number> }) {
  const chartData = pieEntries(data).map((d) => ({
    ...d,
    name: d.name === 'fail' ? 'Fail' : d.name === 'warning' ? 'Warning' : 'Pass',
    key: d.name,
  }))
  if (!chartData.length) {
    return <p className="py-12 text-center text-sm text-[var(--gov-faint)]">No checks yet</p>
  }
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={2}>
            {chartData.map((d) => (
              <Cell key={d.key} fill={SEVERITY_COLORS[d.key] ?? '#8a97a6'} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function CheckLevelPie({ data }: { data: Record<string, number> }) {
  const chartData = pieEntries(data)
  if (!chartData.length) {
    return <p className="py-12 text-center text-sm text-[var(--gov-faint)]">No level alerts</p>
  }
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={2}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={LEVEL_COLORS[i % LEVEL_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function DailySpendTrendChart({
  data,
}: {
  data: Array<{
    day: string
    search: number
    video: number
    demandGen: number
    pmax: number
    total: number
  }>
}) {
  if (!data.length) {
    return <p className="py-12 text-center text-sm text-[var(--gov-faint)]">No daily spend series</p>
  }
  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e6ebf0" />
          <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="#8a97a6" />
          <YAxis
            tick={{ fontSize: 11 }}
            stroke="#8a97a6"
            tickFormatter={(v) => `₹${(Number(v) / 1000).toFixed(0)}k`}
          />
          <Tooltip formatter={(v) => formatInr(Number(v ?? 0))} />
          <Legend />
          <Line type="monotone" dataKey="search" name="Search" stroke="#2c6e9b" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="video" name="Video" stroke="#2F7D5B" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="demandGen" name="Demand Gen" stroke="#B0791A" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="pmax" name="PMax" stroke="#6B5B95" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function HourlySpendBarChart({ data }: { data: Array<Record<string, string | number>> }) {
  if (!data.length) {
    return <p className="py-12 text-center text-sm text-[var(--gov-faint)]">No hourly spend today</p>
  }
  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e6ebf0" />
          <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="#8a97a6" interval={2} />
          <YAxis
            tick={{ fontSize: 11 }}
            stroke="#8a97a6"
            tickFormatter={(v) => `₹${(Number(v) / 1000).toFixed(0)}k`}
          />
          <Tooltip formatter={(v) => formatInr(Number(v ?? 0))} />
          <Legend />
          <Bar dataKey="Search" stackId="a" fill="#2c6e9b" />
          <Bar dataKey="Video" stackId="a" fill="#2F7D5B" />
          <Bar dataKey="Demand Gen" stackId="a" fill="#B0791A" />
          <Bar dataKey="PMax" stackId="a" fill="#6B5B95" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function TopCampaignsBar({
  data,
}: {
  data: Array<{ campaign: string; spend_7d_proxy: number; campaign_type: string }>
}) {
  if (!data.length) {
    return <p className="py-12 text-center text-sm text-[var(--gov-faint)]">No campaign rows</p>
  }
  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e6ebf0" />
          <XAxis
            type="number"
            tick={{ fontSize: 11 }}
            stroke="#8a97a6"
            tickFormatter={(v) => `₹${(Number(v) / 1000).toFixed(0)}k`}
          />
          <YAxis type="category" dataKey="campaign" width={120} tick={{ fontSize: 10 }} stroke="#8a97a6" />
          <Tooltip formatter={(v) => formatInr(Number(v ?? 0))} />
          <Bar dataKey="spend_7d_proxy" name="~7-day spend" fill="#2c6e9b" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
