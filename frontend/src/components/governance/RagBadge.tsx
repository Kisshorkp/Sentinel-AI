interface RagPayload {
  status: string
  label: string
  emoji: string
  text_color: string
  bg_tint: string
}

export function RagBadge({ rag, pct }: { rag: RagPayload; pct?: number }) {
  return (
    <span
      className="rag-badge"
      style={{ color: rag.text_color, backgroundColor: rag.bg_tint }}
    >
      <span aria-hidden>{rag.emoji}</span>
      <span>{rag.label}</span>
      {pct !== undefined ? (
        <span className="font-mono-num" style={{ color: rag.text_color }}>
          {pct > 0 ? '+' : ''}
          {pct.toFixed(1)}%
        </span>
      ) : null}
    </span>
  )
}
