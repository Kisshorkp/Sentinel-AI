import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import type { AnalyzerRunResponse, AppConfig } from '../services/api'
import { saveAnalyzerSession } from '../utils/analyzerSessionStorage'
import {
  clearCampaignAnalysisCache,
  getCampaignAnalysisCache,
  setCampaignAnalysisCache,
} from '../utils/pageDataCache'
import { useAuth } from './AuthContext'

interface AnalyzerContextValue {
  config: AppConfig | null
  setConfig: (config: AppConfig | null) => void
  analyzerData: AnalyzerRunResponse | null
  setAnalyzerData: (data: AnalyzerRunResponse | null) => void
  chatMessages: Array<{ role: string; content: string }>
  setChatMessages: (messages: Array<{ role: string; content: string }>) => void
  clearAnalyzer: () => void
}

const AnalyzerContext = createContext<AnalyzerContextValue | null>(null)

function loadInitialAnalyzer(): {
  data: AnalyzerRunResponse | null
  chatMessages: Array<{ role: string; content: string }>
} {
  const cached = getCampaignAnalysisCache()
  if (!cached?.data) {
    return { data: null, chatMessages: [] }
  }
  return {
    data: cached.data as AnalyzerRunResponse,
    chatMessages: cached.chatMessages ?? [],
  }
}

export function AnalyzerProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const wasAuthenticated = useRef(isAuthenticated)
  const initial = loadInitialAnalyzer()
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [analyzerData, setAnalyzerDataState] = useState<AnalyzerRunResponse | null>(
    isAuthenticated ? initial.data : null,
  )
  const [chatMessages, setChatMessagesState] = useState<Array<{ role: string; content: string }>>(
    isAuthenticated ? initial.chatMessages : [],
  )

  // Drop in-memory analyzer state on login/logout so post-sign-in always starts fresh.
  useEffect(() => {
    const loggedIn = !wasAuthenticated.current && isAuthenticated
    const loggedOut = wasAuthenticated.current && !isAuthenticated
    if (loggedIn || loggedOut) {
      setAnalyzerDataState(null)
      setChatMessagesState([])
    }
    wasAuthenticated.current = isAuthenticated
  }, [isAuthenticated])

  const setAnalyzerData = (data: AnalyzerRunResponse | null) => {
    setAnalyzerDataState(data)
    if (!data) {
      clearCampaignAnalysisCache()
      setChatMessagesState([])
      return
    }
    const prev = getCampaignAnalysisCache()
    setCampaignAnalysisCache({
      data,
      selectedCid: prev?.selectedCid ?? '',
      chatMessages: prev?.chatMessages ?? [],
      step: 3,
    })
    saveAnalyzerSession(data.session_id, data.agent_report)
  }

  const setChatMessages = (messages: Array<{ role: string; content: string }>) => {
    setChatMessagesState(messages)
    const prev = getCampaignAnalysisCache()
    const data = analyzerData ?? (prev?.data as AnalyzerRunResponse | null)
    if (!data) return
    setCampaignAnalysisCache({
      data,
      selectedCid: prev?.selectedCid ?? '',
      chatMessages: messages,
      step: prev?.step ?? 3,
    })
  }

  const value = useMemo(
    () => ({
      config,
      setConfig,
      analyzerData,
      setAnalyzerData,
      chatMessages,
      setChatMessages,
      clearAnalyzer: () => {
        setAnalyzerDataState(null)
        setChatMessagesState([])
        clearCampaignAnalysisCache()
      },
    }),
    [config, analyzerData, chatMessages],
  )

  return <AnalyzerContext.Provider value={value}>{children}</AnalyzerContext.Provider>
}

export function useAnalyzer() {
  const ctx = useContext(AnalyzerContext)
  if (!ctx) throw new Error('useAnalyzer must be used within AnalyzerProvider')
  return ctx
}
