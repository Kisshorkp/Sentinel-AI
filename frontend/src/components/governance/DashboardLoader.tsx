import { useEffect, useState } from 'react'

const STEPS = [
  'Connecting to Google Ads',
  'Fetching last 7 days of spend',
  'Running account & daily checks',
  'Running hourly & campaign checks',
  'Building charts & AI summary',
]

function Bone({ className = '' }: { className?: string }) {
  return <div className={`gov-skeleton-bone ${className}`} aria-hidden />
}

export function DashboardLoader() {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const id = window.setInterval(() => {
      setStep((prev) => (prev + 1) % STEPS.length)
    }, 2200)
    return () => window.clearInterval(id)
  }, [])

  return (
    <div className="governance-page -mx-2 rounded-2xl bg-[#F4F6F8] px-2 pb-8 pt-2 lg:-mx-4 lg:px-4">
      {/* Status banner */}
      <div className="gov-card mb-6 overflow-hidden">
        <div className="flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="gov-loader-mark" aria-hidden>
              <span className="gov-loader-ring" />
              <span className="gov-loader-core">SA</span>
            </div>
            <div>
              <h1 className="font-display text-xl font-medium text-[var(--gov-ink)]">
                Preparing spend governance
              </h1>
              <p className="mt-1 text-sm text-[var(--gov-muted)]">{STEPS[step]}…</p>
            </div>
          </div>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--gov-faint)]">
            Live Google Ads · AI checks
          </p>
        </div>

        <div className="border-t border-[var(--gov-hairline-2)] px-6 py-4">
          <div className="flex flex-wrap gap-2">
            {STEPS.map((label, index) => {
              const active = index === step
              const done = index < step
              return (
                <span
                  key={label}
                  className={`rounded-full px-3 py-1.5 text-[11px] font-semibold transition ${
                    active
                      ? 'bg-[rgba(44,110,155,0.12)] text-[var(--gov-steel)] ring-1 ring-[rgba(44,110,155,0.28)]'
                      : done
                        ? 'bg-[#EAF3EE] text-[#2F7D5B]'
                        : 'bg-[#F4F6F8] text-[var(--gov-faint)]'
                  }`}
                >
                  {done ? '✓ ' : active ? '● ' : ''}
                  {label.replace('Running ', '').replace('Building ', '')}
                </span>
              )
            })}
          </div>
          <div className="gov-loader-track mt-4">
            <div
              className="gov-loader-fill"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Scorecard skeleton */}
      <section className="gov-card mb-6 p-6">
        <div className="flex flex-wrap gap-8 lg:flex-nowrap">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="min-w-0 flex-1 space-y-3">
              <Bone className="h-3 w-24" />
              <Bone className="h-8 w-28" />
              <Bone className="h-3 w-20" />
            </div>
          ))}
        </div>
        <div className="gov-hairline my-6" />
        <div className="flex flex-wrap gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Bone key={i} className="h-11 w-40 rounded-xl" />
          ))}
        </div>
      </section>

      {/* Table skeleton */}
      <section className="gov-card mb-6 overflow-hidden">
        <div className="border-b border-[var(--gov-hairline-2)] px-6 py-4 space-y-2">
          <Bone className="h-5 w-48" />
          <Bone className="h-3 w-72" />
        </div>
        <div className="space-y-3 px-6 py-5">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Bone className="h-4 w-28" />
              <Bone className="h-4 flex-1" />
              <Bone className="h-4 w-20" />
              <Bone className="h-4 w-16" />
              <Bone className="h-6 w-24 rounded-full" />
            </div>
          ))}
        </div>
      </section>

      {/* Charts skeleton */}
      <section className="mb-6 grid gap-6 lg:grid-cols-2">
        <div className="gov-card p-6 space-y-4">
          <Bone className="h-5 w-40" />
          <Bone className="h-3 w-56" />
          <Bone className="mx-auto h-44 w-44 rounded-full" />
        </div>
        <div className="gov-card p-6 space-y-4">
          <Bone className="h-5 w-36" />
          <Bone className="h-3 w-48" />
          <div className="flex h-44 items-end gap-3 pt-4">
            {[42, 68, 55, 80, 48, 72, 60].map((h, i) => (
              <div
                key={i}
                className="gov-skeleton-bone flex-1 rounded-t-md"
                style={{ height: `${h}%` }}
                aria-hidden
              />
            ))}
          </div>
        </div>
      </section>

      <p className="text-center text-xs text-[var(--gov-faint)]">
        This usually takes under 2 minutes on first live fetch.
      </p>
    </div>
  )
}
