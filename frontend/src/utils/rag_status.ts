/** RAG status from MTD pace deviation % (green=underspend, amber=on-track, red=overspend). */

export type RagStatus = 'under_spend' | 'on_track' | 'over_spend'

export interface RagStyle {
  status: RagStatus
  label: string
  emoji: string
  textColor: string
  bgTint: string
}

export function getRagStatus(deviationPct: number): RagStyle {
  if (deviationPct < -5) {
    return {
      status: 'under_spend',
      label: 'Under Spend',
      emoji: '🟢',
      textColor: '#2F7D5B',
      bgTint: '#EAF3EE',
    }
  }
  if (deviationPct > 5) {
    return {
      status: 'over_spend',
      label: 'Over Spend',
      emoji: '🔴',
      textColor: '#B23A32',
      bgTint: '#FBEDEC',
    }
  }
  return {
    status: 'on_track',
    label: 'On Track',
    emoji: '🟡',
    textColor: '#B0791A',
    bgTint: '#FBF3E3',
  }
}
