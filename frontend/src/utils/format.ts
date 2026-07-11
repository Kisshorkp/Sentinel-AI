export function formatCurrency(value: number, currency = 'INR') {
  const symbol = currency === 'INR' ? '₹' : currency === 'USD' ? '$' : `${currency} `
  return `${symbol}${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
}

export function formatPercent(value: number) {
  return `${value.toFixed(1)}%`
}

export function severityBadgeClass(severity: string) {
  if (severity === 'critical' || severity === 'over_budget') return 'bg-red-100 text-red-700'
  if (severity === 'warning') return 'bg-amber-100 text-amber-700'
  return 'bg-emerald-100 text-emerald-700'
}

export function severityIcon(severity: string) {
  if (severity === 'critical' || severity === 'over_budget') return '🔴'
  if (severity === 'warning') return '🟡'
  return '🟢'
}
