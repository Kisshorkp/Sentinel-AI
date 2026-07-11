import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

interface SpendVsBudgetChartProps {
  rows: Array<{ campaign: string; spend_mtd: number; monthly_budget: number }>
  currency: string
}

export function SpendVsBudgetChart({ rows }: SpendVsBudgetChartProps) {
  return (
    <div className="h-96 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="campaign" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" height={70} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="spend_mtd" name="Spend (MTD)" fill="#2563eb" radius={[4, 4, 0, 0]} />
          <Bar dataKey="monthly_budget" name="Monthly Budget" fill="#64748b" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

interface UtilizationGaugeProps {
  utilization: number
  warningPct: number
  criticalPct: number
}

export function UtilizationGauge({ utilization, warningPct, criticalPct }: UtilizationGaugeProps) {
  let color = '#22c55e'
  if (utilization >= criticalPct) color = '#ef4444'
  else if (utilization >= warningPct) color = '#f59e0b'

  const data = [{ name: 'used', value: Math.min(utilization, 120) }, { name: 'rest', value: Math.max(120 - utilization, 0) }]

  return (
    <div className="flex flex-col items-center">
      <div className="relative h-56 w-56">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} innerRadius={70} outerRadius={95} startAngle={180} endAngle={0} dataKey="value" stroke="none">
              <Cell fill={color} />
              <Cell fill="#e2e8f0" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center pt-8">
          <p className="text-3xl font-bold text-slate-800">{utilization.toFixed(1)}%</p>
          <p className="text-xs text-slate-500">Portfolio Utilization</p>
        </div>
      </div>
    </div>
  )
}

interface StakeholderPieProps {
  data: Record<string, number>
}

const COLORS = ['#0284c7', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4']

export function StakeholderPieChart({ data }: StakeholderPieProps) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }))
  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2}>
            {chartData.map((_, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
