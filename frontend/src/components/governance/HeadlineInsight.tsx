/** Bold ₹ amounts and percentages inside governance headline copy. */
export function HeadlineInsight({ text }: { text: string }) {
  const parts = text.split(/(₹[\d,]+|\d+\.?\d*%)/g)
  return (
    <p className="headline-insight">
      {parts.map((part, index) =>
        /^(₹[\d,]+|\d+\.?\d*%)$/.test(part) ? (
          <strong key={index}>{part}</strong>
        ) : (
          <span key={index}>{part}</span>
        ),
      )}
    </p>
  )
}
