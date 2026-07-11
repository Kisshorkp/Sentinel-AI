import clsx from 'clsx'

export interface PipelineStep {
  id: string
  title: string
  subtitle: string
  icon: string
}

export const PIPELINE_STEPS: PipelineStep[] = [
  { id: 'fetch', title: 'Google Ads', subtitle: 'Data fetched', icon: '📡' },
  { id: 'account', title: 'Account-wise', subtitle: 'MTD & budget', icon: '📊' },
  { id: 'daily', title: 'Daily-wise', subtitle: 'Daily snapshot', icon: '📅' },
  { id: 'hourly', title: 'Hourly', subtitle: 'Hour breakdown', icon: '⏱️' },
  { id: 'campaign', title: 'Campaign-wise', subtitle: 'Per campaign', icon: '🎯' },
]

function badgeLabel(stepId: string, status: string) {
  if (stepId === 'fetch' && status === 'complete') return 'Fetched'
  const map: Record<string, string> = {
    pending: 'Pending',
    running: 'Running',
    complete: 'Done',
    error: 'Error',
    skipped: 'Skipped',
  }
  return map[status] ?? 'Pending'
}

const statusClass: Record<string, string> = {
  pending: 'border-slate-200 bg-slate-50 text-slate-500',
  running: 'border-sky-300 bg-sky-50 text-sky-700 loader-pulse',
  complete: 'border-emerald-300 bg-emerald-50 text-emerald-700',
  error: 'border-red-300 bg-red-50 text-red-700',
  skipped: 'border-slate-200 bg-slate-50 text-slate-400',
}

interface PipelineStepsProps {
  stepStatus: Record<string, string>
  compact?: boolean
}

export function PipelineSteps({ stepStatus, compact }: PipelineStepsProps) {
  return (
    <div className={clsx('grid gap-2', compact ? 'grid-cols-5' : 'grid-cols-1 sm:grid-cols-5')}>
      {PIPELINE_STEPS.map((step, index) => {
        const status = stepStatus[step.id] ?? 'pending'
        return (
          <div key={step.id} className="relative flex items-stretch gap-2">
            <div
              className={clsx(
                'flex flex-1 flex-col justify-between rounded-2xl border px-3 py-3',
                statusClass[status] ?? statusClass.pending,
              )}
            >
              <div className="flex items-start gap-2">
                <span className="text-lg">{step.icon}</span>
                <div>
                  <p className="text-xs font-bold">{step.title}</p>
                  <p className="text-[10px] opacity-70">{step.subtitle}</p>
                </div>
              </div>
              <span className="mt-2 w-fit rounded-md bg-white/70 px-2 py-0.5 text-[10px] font-bold uppercase">
                {badgeLabel(step.id, status)}
              </span>
            </div>
            {index < PIPELINE_STEPS.length - 1 ? (
              <span className="hidden self-center text-slate-300 sm:inline">→</span>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
