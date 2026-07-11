import {
  Area,
  Bar,
  BarChart,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatInr } from '../../utils/format_inr'
import { getRagStatus } from '../../utils/rag_status'

interface PacingPoint {
  day_label: string
  actual_cumulative: number
  expected_pace: number
  target: number
}

export function MtdPacingChart({ data, deviationPct }: { data: PacingPoint[]; deviationPct: number }) {
  const rag = getRagStatus(deviationPct)
  const strokeActual = rag.status === 'over_spend' ? '#B23A32' : rag.status === 'under_spend' ? '#2F7D5B' : '#2C6E9B'

  return (
    <div className="h-[320px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 12, right: 20, left: 4, bottom: 4 }}>
          <XAxis
            dataKey="day_label"
            tick={{ fill: '#8A97A6', fontSize: 11, fontFamily: 'IBM Plex Mono' }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: '#8A97A6', fontSize: 11, fontFamily: 'IBM Plex Mono' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => formatInr(v, true)}
            width={52}
          />
          <Tooltip
            formatter={(value: number, name: string) => [
              formatInr(value),
              name === 'actual_cumulative' ? 'Actual MTD' : name === 'expected_pace' ? 'Expected pace' : name,
            ]}
            contentStyle={{
              borderRadius: 12,
              border: '1px solid #E6EBF0',
              boxShadow: '0 8px 24px rgba(22,32,43,.05)',
              fontFamily: 'IBM Plex Mono',
              fontSize: 12,
            }}
          />
          <ReferenceLine
            y={data[0]?.target}
            stroke="#8A97A6"
            strokeDasharray="4 4"
            strokeWidth={1}
            label={{
              value: 'Target',
              position: 'insideTopRight',
              fill: '#8A97A6',
              fontSize: 10,
              fontFamily: 'IBM Plex Mono',
            }}
          />
          <Area
            type="monotone"
            dataKey="actual_cumulative"
            stroke={strokeActual}
            fill={rag.bgTint}
            fillOpacity={0.65}
            strokeWidth={2.5}
            name="actual_cumulative"
          />
          <Line
            type="monotone"
            dataKey="expected_pace"
            stroke="#5E6B7A"
            strokeDasharray="6 4"
            strokeWidth={2}
            dot={false}
            name="expected_pace"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export function Sparkline({ values }: { values: number[] }) {
  const data = values.map((v, i) => ({ i, v }))
  return (
    <div className="h-8 w-24">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <Line type="monotone" dataKey="v" stroke="#2C6E9B" strokeWidth={1.5} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export function AlertVolumeChart({
  daily,
}: {
  daily: Array<{ label: string; critical: number; warning: number }>
}) {
  return (
    <div className="h-36 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={daily} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#8A97A6' }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ fontSize: 11, fontFamily: 'IBM Plex Mono' }} />
          <Bar dataKey="critical" stackId="a" fill="#FBEDEC" stroke="#B23A32" strokeWidth={1} />
          <Bar dataKey="warning" stackId="a" fill="#FBF3E3" stroke="#B0791A" strokeWidth={1} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
