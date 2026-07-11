import { useEffect, useState } from 'react'
import { AlertTriangle } from 'lucide-react'

const STEPS = [
  'Loading analyzer session',
  'Collecting account-wise alerts',
  'Collecting daily & hourly alerts',
  'Collecting campaign-wise alerts',
  'Checking email delivery status',
]

const TABS = ['Account-wise', 'Daily-wise', 'Hourly', 'Campaign-wise']

function Bone({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-gradient-to-r from-slate-100 via-slate-50 to-slate-100 bg-[length:200%_100%] ${className}`}
      style={{ animationDuration: '1.4s' }}
      aria-hidden
    />
  )
}

function AlertCardSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex-1 space-y-2">
          <Bone className="h-4 w-2/3" />
          <Bone className="h-3 w-1/3" />
        </div>
        <Bone className="h-6 w-20 rounded-full" />
      </div>
      <div className="space-y-2">
        <Bone className="h-3 w-full" />
        <Bone className="h-3 w-5/6" />
        <Bone className="h-3 w-2/5" />
      </div>
      <div className="mt-4 flex gap-2">
        <Bone className="h-6 w-24 rounded-full" />
        <Bone className="h-6 w-28 rounded-full" />
      </div>
    </div>
  )
}

export function BudgetAlertsLoader() {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const id = window.setInterval(() => {
      setStep((prev) => (prev + 1) % STEPS.length)
    }, 1800)
    return () => window.clearInterval(id)
  }, [])

  return (
    <div className="space-y-5">
      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        <div className="flex flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="relative flex h-12 w-12 shrink-0 items-center justify-center">
              <span className="absolute inset-0 animate-spin rounded-2xl border-2 border-slate-100 border-t-brand-600" />
              <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#0c2340] text-white">
                <AlertTriangle className="h-4 w-4" />
              </span>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800">Preparing alert center</h2>
              <p className="mt-1 text-sm text-slate-500">{STEPS[step]}…</p>
            </div>
          </div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
            Pipeline · Account · Daily · Hourly · Campaign
          </p>
        </div>

        <div className="border-t border-slate-100 px-5 py-4">
          <div className="flex flex-wrap gap-2">
            {STEPS.map((label, index) => {
              const active = index === step
              const done = index < step
              return (
                <span
                  key={label}
                  className={`rounded-full px-3 py-1.5 text-[11px] font-semibold transition ${
                    active
                      ? 'bg-brand-50 text-brand-700 ring-1 ring-brand-200'
                      : done
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-slate-50 text-slate-400'
                  }`}
                >
                  {done ? '✓ ' : active ? '● ' : ''}
                  {label.replace('Collecting ', '').replace('Checking ', '').replace('Loading ', '')}
                </span>
              )
            })}
          </div>
          <div className="mt-4 h-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[#0c2340] to-brand-600 transition-all duration-500"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <Bone className="h-5 w-40" />
          <Bone className="h-4 w-16" />
        </div>

        <div className="mb-5 flex flex-wrap gap-2 border-b border-slate-100 pb-3">
          {TABS.map((tab, i) => (
            <Bone
              key={tab}
              className={`h-9 w-28 rounded-t-xl ${i === 0 ? 'opacity-100' : 'opacity-60'}`}
            />
          ))}
        </div>

        <div className="mb-4 space-y-2">
          <Bone className="h-3 w-72" />
          <Bone className="h-3 w-48" />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <AlertCardSkeleton />
          <AlertCardSkeleton />
          <AlertCardSkeleton />
          <AlertCardSkeleton />
        </div>
      </div>

      <p className="text-center text-xs text-slate-400">
        Pulling critical and warning checks from your latest analyzer run.
      </p>
    </div>
  )
}
