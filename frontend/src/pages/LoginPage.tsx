import clsx from 'clsx'
import { Eye, EyeOff, LineChart, Plug } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { SidebarBrandCompact } from '../components/layout/Sidebar'
import { PageLoader } from '../components/ui/Loader'
import { useAuth } from '../context/AuthContext'
import { DEMO_EMAIL, DEMO_PASSWORD } from '../data/mockData'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState(DEMO_EMAIL)
  const [password, setPassword] = useState(DEMO_PASSWORD)
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    try {
      await login(email, password)
      toast.success('Welcome back!', {
        description: 'Signed in to Sentinel AI.',
      })
      navigate('/dashboard')
    } catch (error) {
      toast.error('Sign in failed', {
        description: error instanceof Error ? error.message : 'Please try again.',
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <PageLoader label="Signing you in..." />
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,#dbeafe,transparent_35%),linear-gradient(180deg,#f8fbff_0%,#eef4fb_100%)]">
      <div className="mx-auto flex min-h-screen max-w-6xl items-center px-6 py-10">
        <div className="grid w-full gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="rounded-[2rem] border border-white/70 bg-white/80 p-10 shadow-[0_20px_60px_rgba(15,39,68,0.08)] backdrop-blur">
            <SidebarBrandCompact />
            <h2 className="mt-10 text-4xl font-bold leading-tight text-slate-800">
              Unlock Insights from your <span className="text-brand-600">Ad Spend Data</span>
            </h2>
            <p className="mt-4 max-w-xl text-slate-500">
              Track Google Ads spend against permissible limits, detect overspend early, and quantify NR loss
              prevention for stakeholders.
            </p>

            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-100 bg-slate-50/80 p-5">
                <Plug className="mb-3 h-5 w-5 text-brand-600" />
                <p className="font-semibold text-slate-800">Unified Spend Access</p>
                <p className="mt-1 text-sm text-slate-500">Live dashboards & automated AI reporting.</p>
              </div>
              <div className="rounded-2xl border border-slate-100 bg-slate-50/80 p-5">
                <LineChart className="mb-3 h-5 w-5 text-brand-600" />
                <p className="font-semibold text-slate-800">360° Campaign View</p>
                <p className="mt-1 text-sm text-slate-500">Account, daily, hourly & campaign checks.</p>
              </div>
            </div>

            <div className="mt-10 flex h-28 items-end gap-2">
              {[42, 68, 54, 88, 62, 95, 74].map((height, index) => (
                <div
                  key={index}
                  className="flex-1 rounded-t-xl bg-gradient-to-t from-brand-600 to-brand-500/40"
                  style={{ height: `${height}%` }}
                />
              ))}
            </div>
          </section>

          <section className="rounded-[2rem] border border-white/70 bg-white p-10 shadow-[0_20px_60px_rgba(15,39,68,0.08)]">
            <h2 className="text-3xl font-bold text-slate-800">Welcome Back</h2>
            <p className="mt-2 text-sm text-slate-500">Sign in to your Sentinel AI portal</p>

            <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email" className="mb-2 block text-sm font-medium text-slate-700">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none ring-brand-500 transition focus:border-brand-500 focus:ring-2"
                  required
                />
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label htmlFor="password" className="text-sm font-medium text-slate-700">
                    Password
                  </label>
                  <button type="button" className="text-sm font-medium text-brand-600 hover:text-brand-700">
                    Forgot Password?
                  </button>
                </div>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-4 py-3 pr-12 text-sm outline-none ring-brand-500 transition focus:border-brand-500 focus:ring-2"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className={clsx(
                  'w-full rounded-xl bg-brand-600 py-3.5 text-sm font-semibold text-white shadow-lg shadow-brand-600/20 transition hover:bg-brand-700',
                  loading && 'opacity-70',
                )}
              >
                Sign In
              </button>
            </form>

            <p className="mt-6 text-center text-xs text-slate-400">
              Demo credentials: <span className="font-medium text-slate-500">{DEMO_EMAIL}</span> /{' '}
              <span className="font-medium text-slate-500">{DEMO_PASSWORD}</span>
            </p>
            <p className="mt-4 text-center text-xs text-slate-400">
              By continuing, you agree to our Terms of Service and Privacy Policy.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
