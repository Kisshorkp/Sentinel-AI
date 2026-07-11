import clsx from 'clsx'
import { Loader2 } from 'lucide-react'

interface LoaderProps {
  label?: string
  fullScreen?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = {
  sm: 'h-5 w-5',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
}

export function Loader({ label = 'Loading...', fullScreen = false, size = 'md' }: LoaderProps) {
  const content = (
    <div className="flex flex-col items-center gap-3">
      <Loader2 className={clsx('loader-spin text-brand-600', sizeMap[size])} />
      {label ? <p className="text-sm font-medium text-slate-500">{label}</p> : null}
    </div>
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm">
        {content}
      </div>
    )
  }

  return <div className="flex items-center justify-center py-16">{content}</div>
}

export function PageLoader({ label }: { label?: string }) {
  return <Loader label={label} fullScreen />
}
