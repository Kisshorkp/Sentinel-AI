/** Indian Rupee formatting — dashboard Overview only. */

export function formatInr(value: number, compact = false): string {
  const n = Number.isFinite(value) ? value : 0
  if (compact) {
    if (Math.abs(n) >= 1_00_00_000) return `₹${(n / 1_00_00_000).toFixed(2)}Cr`
    if (Math.abs(n) >= 1_00_000) return `₹${(n / 1_00_000).toFixed(2)}L`
    if (Math.abs(n) >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`
  }
  return `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

export function formatInrDecimal(value: number): string {
  return `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

export function formatPct(value: number, signed = false): string {
  const prefix = signed && value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(1)}%`
}
