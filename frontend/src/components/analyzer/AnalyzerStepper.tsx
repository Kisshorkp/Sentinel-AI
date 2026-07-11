import clsx from 'clsx'
import { Check } from 'lucide-react'

const STEPS = [
  { id: 1, title: 'Select account', hint: 'Choose CID & review analyzers' },
  { id: 2, title: 'Budgets & upload', hint: 'Form or Excel upload' },
  { id: 3, title: 'AI analysis', hint: 'Pipeline & chat' },
] as const

interface AnalyzerStepperProps {
  currentStep: 1 | 2 | 3
  onStepClick?: (step: 1 | 2 | 3) => void
}

export function AnalyzerStepper({ currentStep, onStepClick }: AnalyzerStepperProps) {
  return (
    <ol className="mb-6 grid gap-3 md:grid-cols-3">
      {STEPS.map((step) => {
        const active = currentStep === step.id
        const done = currentStep > step.id
        return (
          <li key={step.id}>
            <button
              type="button"
              disabled={!onStepClick || step.id > currentStep}
              onClick={() => onStepClick?.(step.id)}
              className={clsx(
                'flex w-full items-center gap-3 rounded-2xl border px-4 py-3 text-left transition',
                active && 'border-brand-300 bg-brand-50 shadow-sm',
                done && 'border-emerald-200 bg-emerald-50/70',
                !active && !done && 'border-slate-200 bg-white opacity-80',
                step.id <= currentStep && onStepClick ? 'cursor-pointer' : 'cursor-default',
              )}
            >
              <span
                className={clsx(
                  'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold',
                  active && 'bg-brand-600 text-white',
                  done && 'bg-emerald-600 text-white',
                  !active && !done && 'bg-slate-100 text-slate-500',
                )}
              >
                {done ? <Check className="h-4 w-4" /> : step.id}
              </span>
              <span>
                <span className="block text-sm font-semibold text-slate-800">{step.title}</span>
                <span className="block text-xs text-slate-500">{step.hint}</span>
              </span>
            </button>
          </li>
        )
      })}
    </ol>
  )
}
