import clsx from 'clsx'
import {
  AlertTriangle,
  BarChart3,
  Eraser,
  LayoutDashboard,
  LogOut,
  Sparkles,
  Shield,
} from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuth } from '../../context/AuthContext'
import { clearPageDataCache, hasPageDataCache } from '../../utils/pageDataCache'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/campaign-analysis', label: 'Campaign Analysis', icon: Sparkles },
  { to: '/budget-alerts', label: 'Budget Alerts', icon: AlertTriangle },
]

export const SIDEBAR_WIDTH = '17.5rem'

export function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleClearCache = () => {
    if (!hasPageDataCache()) {
      toast.message('Cache is already empty')
      return
    }
    clearPageDataCache()
    toast.success('Cache cleared', {
      description: 'Dashboard, Budget Alerts, and Campaign Analysis will reload fresh next time.',
    })
    // Remount current route so pages drop stale in-memory state and refetch.
    navigate(0)
  }

  return (
    <aside
      className="fixed inset-y-0 left-0 z-40 flex w-[280px] flex-col border-r border-white/10 bg-[#0c2340] shadow-xl"
      style={{ background: 'linear-gradient(180deg, #0c2340 0%, #0f2d4f 48%, #0a1f38 100%)' }}
    >
      {/* Brand */}
      <div className="shrink-0 border-b border-white/10 px-5 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sky-500/20 ring-1 ring-sky-400/30">
            <Shield className="h-5 w-5 text-sky-300" strokeWidth={2.2} />
          </div>
          <div className="min-w-0">
            <p className="truncate text-base font-bold leading-tight text-white">Sentinel AI</p>
            <p className="truncate text-[11px] font-medium text-sky-200/75">Ad Spend Intelligence</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.14em] text-sky-300/50">Main Menu</p>
        <ul className="space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-all duration-150',
                    isActive
                      ? 'bg-sky-500/20 text-white shadow-[inset_0_0_0_1px_rgba(56,189,248,0.35)]'
                      : 'text-sky-100/85 hover:bg-white/8 hover:text-white',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={clsx(
                        'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
                        isActive ? 'bg-sky-500/30 text-sky-100' : 'bg-white/5 text-sky-200/80',
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="truncate">{label}</span>
                    {isActive ? (
                      <span className="ml-auto h-1.5 w-1.5 shrink-0 rounded-full bg-sky-300" aria-hidden />
                    ) : null}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="shrink-0 space-y-2 border-t border-white/10 bg-[#081a30]/60 px-3 py-4 backdrop-blur-sm">
        <button
          type="button"
          onClick={handleClearCache}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium text-sky-100/80 transition hover:bg-white/8 hover:text-white"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5">
            <Eraser className="h-4 w-4" />
          </span>
          Clear Cache
        </button>

        <div className="rounded-xl bg-white/10 p-3 ring-1 ring-white/10">
          <div className="flex items-center gap-3">
            <div className="relative shrink-0">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-sky-600 text-sm font-bold text-white shadow-md">
                {user?.initials ?? 'AU'}
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[#0c2340] bg-emerald-400" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-white">{user?.name ?? 'Admin User'}</p>
              <p className="truncate text-[11px] text-sky-200/70">{user?.email ?? 'demo@sentinel.ai'}</p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              title="Sign out"
              className="shrink-0 rounded-lg p-2 text-sky-200/80 transition hover:bg-white/10 hover:text-white"
              aria-label="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  )
}

export function SidebarBrandCompact() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/15 ring-1 ring-brand-500/30">
        <BarChart3 className="h-6 w-6 text-brand-600" />
      </div>
      <div>
        <p className="text-xl font-bold text-slate-800">Sentinel AI</p>
        <p className="text-sm text-slate-500">Ad Spend Intelligence</p>
      </div>
    </div>
  )
}
