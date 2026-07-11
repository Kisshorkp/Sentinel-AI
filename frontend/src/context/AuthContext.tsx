import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import type { User } from '../types'
import { DEMO_EMAIL, DEMO_PASSWORD } from '../data/mockData'
import { clearPageDataCache } from '../utils/pageDataCache'

const STORAGE_KEY = 'sentinel_ai_auth'

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function loadStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

function buildUser(email: string): User {
  const name = email.split('@')[0].replace(/[._]/g, ' ')
  const display = name
    .split(' ')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
  const initials = display
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
  return { email, name: display || 'User', initials }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => loadStoredUser())

  const login = useCallback(async (email: string, password: string) => {
    await new Promise((resolve) => setTimeout(resolve, 1200))

    const normalizedEmail = email.trim().toLowerCase()
    const valid =
      (normalizedEmail === DEMO_EMAIL && password === DEMO_PASSWORD) ||
      (password === DEMO_PASSWORD && normalizedEmail.includes('@'))

    if (!valid) {
      throw new Error('Invalid email or password. Use demo@sentinel.ai / demo123')
    }

    // Always start a signed-in session with fresh API data (no stale cache).
    clearPageDataCache()

    const nextUser = buildUser(normalizedEmail)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser))
    setUser(nextUser)
  }, [])

  const logout = useCallback(() => {
    clearPageDataCache()
    localStorage.removeItem(STORAGE_KEY)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      login,
      logout,
    }),
    [user, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
