import { Send, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { toast } from 'sonner'
import { useAnalyzer } from '../../context/AnalyzerContext'
import { api, type AppConfig } from '../../services/api'
import { DashboardCard } from '../ui/DashboardCard'
import { PageLoader } from '../ui/Loader'
import { ChatMarkdown } from './ChatMarkdown'

interface ChatPanelProps {
  config: AppConfig | null
}

export function ChatPanel({ config }: ChatPanelProps) {
  const { analyzerData, chatMessages, setChatMessages } = useAnalyzer()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [chatMessages, loading])

  if (!config?.openrouter_configured) {
    return (
      <DashboardCard title="AI Chat Assistant">
        <p className="text-sm text-amber-700">Add `OPENROUTER_API_KEY` to `.env` to enable the chatbot.</p>
      </DashboardCard>
    )
  }

  if (!analyzerData) {
    return (
      <DashboardCard title="AI Chat Assistant">
        <p className="text-sm text-slate-500">Run Analyzer first so the chatbot can use your Google Ads data.</p>
      </DashboardCard>
    )
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!input.trim() || loading) return
    const message = input.trim()
    setInput('')
    setChatMessages([...chatMessages, { role: 'user', content: message }])
    setLoading(true)
    try {
      const response = await api.chat(analyzerData.session_id, message)
      setChatMessages(response.messages)
    } catch (error) {
      toast.error('Chat failed', {
        description: error instanceof Error ? error.message : 'Please try again.',
      })
      setChatMessages(chatMessages)
    } finally {
      setLoading(false)
    }
  }

  if (loading && chatMessages.length === 0) {
    return <PageLoader label="Thinking..." />
  }

  return (
    <DashboardCard
      title="AI Chat Assistant"
      subtitle="Ask questions or request calculations on your spend data"
      action={
        <button
          type="button"
          onClick={() => setChatMessages([])}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Clear chat
        </button>
      }
    >
      <p className="mb-4 text-xs text-slate-500">
        Examples: total cost, MTD variance for Search, T-1 vs 7-day avg %, budget utilization.
      </p>

      <div
        ref={scrollRef}
        className="mb-4 max-h-[480px] space-y-3 overflow-y-auto rounded-2xl border border-slate-100 bg-slate-50/50 p-4"
      >
        {!chatMessages.length ? (
          <p className="text-sm text-slate-400">No messages yet. Ask a question about your analyzer results.</p>
        ) : (
          chatMessages.map((message, index) => {
            const isUser = message.role === 'user'
            return (
              <div
                key={index}
                className={`rounded-2xl px-4 py-3 text-sm ${
                  isUser ? 'ml-8 bg-brand-600 text-white' : 'mr-2 bg-white text-slate-700 shadow-sm sm:mr-8'
                }`}
              >
                {isUser ? (
                  <p className="whitespace-pre-wrap leading-6">{message.content}</p>
                ) : (
                  <ChatMarkdown content={message.content} tone="assistant" />
                )}
              </div>
            )
          })
        )}
        {loading ? <p className="text-sm text-slate-400">Thinking...</p> : null}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask questions or request calculations on your spend data..."
          className="flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
        />
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          <Send className="h-4 w-4" />
          Send
        </button>
      </form>
    </DashboardCard>
  )
}
