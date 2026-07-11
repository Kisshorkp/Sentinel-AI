import { Loader2, MessageSquare, Workflow } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { AnalyzerStepper } from '../components/analyzer/AnalyzerStepper'
import { ChatPanel } from '../components/analyzer/ChatPanel'
import { PipelineSteps } from '../components/analyzer/PipelineSteps'
import { PipelineTabs } from '../components/analyzer/PipelineTabs'
import { StepBudgetsUpload } from '../components/analyzer/StepBudgetsUpload'
import { StepSelectAccount } from '../components/analyzer/StepSelectAccount'
import { Header } from '../components/layout/Header'
import { DashboardCard } from '../components/ui/DashboardCard'
import { useAnalyzer } from '../context/AnalyzerContext'
import { api, type AnalyzerRunPayload } from '../services/api'
import { saveAnalyzerSession } from '../utils/analyzerSessionStorage'
import {
  getCampaignAnalysisCache,
  patchCampaignAnalysisCache,
} from '../utils/pageDataCache'

type Step = 1 | 2 | 3
type Step3Tab = 'pipeline' | 'chat'

export function CampaignAnalysisPage() {
  const { config, setConfig, analyzerData, setAnalyzerData, setChatMessages } = useAnalyzer()
  const cached = getCampaignAnalysisCache()
  const [step, setStep] = useState<Step>(() => {
    if (analyzerData) return (cached?.step as Step) || 3
    return 1
  })
  const [selectedCid, setSelectedCid] = useState(() => cached?.selectedCid || '')
  const [step3Tab, setStep3Tab] = useState<Step3Tab>('pipeline')
  const [running, setRunning] = useState(false)
  const [liveStepStatus, setLiveStepStatus] = useState<Record<string, string> | null>(null)
  const [runError, setRunError] = useState<string | null>(null)

  useEffect(() => {
    api
      .config()
      .then((cfg) => {
        setConfig(cfg)
        if (!selectedCid && cfg.default_customer_id) {
          setSelectedCid(cfg.default_customer_id)
        }
      })
      .catch(() => toast.error('Could not load app config. Start the API server.'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setConfig])

  // Persist CID + step so returning to Campaign Analysis restores progress.
  useEffect(() => {
    if (!analyzerData) return
    patchCampaignAnalysisCache({ selectedCid, step })
  }, [analyzerData, selectedCid, step])

  const handleRunAnalyzer = async (payload: AnalyzerRunPayload) => {
    if (!config?.google_ads_configured) {
      toast.error('Configure Google Ads credentials in `.env` first.')
      return
    }

    setRunning(true)
    setStep(3)
    setStep3Tab('pipeline')
    setRunError(null)
    setLiveStepStatus({
      fetch: 'running',
      account: 'pending',
      daily: 'pending',
      hourly: 'pending',
      campaign: 'pending',
    })

    const steps = ['fetch', 'account', 'daily', 'hourly', 'campaign']
    const progressTimer = window.setInterval(() => {
      setLiveStepStatus((prev) => {
        if (!prev) return prev
        const runningIndex = steps.findIndex((s) => prev[s] === 'running')
        if (runningIndex === -1) return prev
        const next = { ...prev, [steps[runningIndex]]: 'complete' }
        if (runningIndex + 1 < steps.length) next[steps[runningIndex + 1]] = 'running'
        return next
      })
    }, 900)

    try {
      const response = await api.runAnalyzer(payload)
      setAnalyzerData(response)
      saveAnalyzerSession(response.session_id, response.agent_report)
      setChatMessages([])
      patchCampaignAnalysisCache({
        data: response,
        selectedCid: payload.account || selectedCid,
        chatMessages: [],
        step: 3,
      })
      setLiveStepStatus(response.step_status)

      if (response.pipeline_errors?.fetch) {
        toast.error('Google Ads fetch failed', {
          description: 'See the pipeline below for details.',
        })
      } else if (Object.keys(response.pipeline_errors ?? {}).length > 0) {
        toast.warning('Analyzer finished with pipeline warnings', {
          description: 'Some agent steps reported errors — check the pipeline tabs.',
        })
      } else {
        toast.success('Analyzer complete', {
          description: 'Results cached — revisit anytime until you Clear Cache.',
        })
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Please try again.'
      setRunError(message)
      toast.error('Analyzer failed', {
        description: message,
      })
      setLiveStepStatus((prev) => ({ ...(prev ?? {}), fetch: 'error' }))
    } finally {
      window.clearInterval(progressTimer)
      setRunning(false)
    }
  }

  return (
    <div>
      <Header
        title="Campaign Analysis"
        subtitle={
          analyzerData
            ? 'Cached analyzer results loaded — Clear Cache in the sidebar to force a fresh run'
            : 'Step through account → budgets/upload → AI agents & chat'
        }
        badge={analyzerData ? 'Cached Results' : 'Live Analyzer'}
      />

      <AnalyzerStepper
        currentStep={step}
        onStepClick={(next) => {
          if (next === 3 && !analyzerData && !running) {
            toast.message('Run Analyzer in step 2 first.')
            return
          }
          setStep(next)
        }}
      />

      {step === 1 ? (
        <StepSelectAccount
          defaultCustomerId={config?.default_customer_id}
          selectedCid={selectedCid}
          onSelectCid={setSelectedCid}
          onNext={() => {
            if (!selectedCid) {
              toast.error('Select an Account / Customer ID')
              return
            }
            setStep(2)
          }}
        />
      ) : null}

      {step === 2 ? (
        <StepBudgetsUpload
          accountCid={selectedCid}
          config={config}
          loading={running}
          onBack={() => setStep(1)}
          onRun={handleRunAnalyzer}
        />
      ) : null}

      {step === 3 ? (
        <div className="space-y-6">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setStep3Tab('pipeline')}
              className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-semibold ${
                step3Tab === 'pipeline' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600'
              }`}
            >
              <Workflow className="h-3.5 w-3.5" />
              AI Agent Pipeline
            </button>
            <button
              type="button"
              onClick={() => setStep3Tab('chat')}
              disabled={running || !analyzerData}
              className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-semibold disabled:opacity-50 ${
                step3Tab === 'chat' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600'
              }`}
            >
              <MessageSquare className="h-3.5 w-3.5" />
              AI Chat
            </button>
            <button
              type="button"
              onClick={() => setStep(2)}
              className="ml-auto rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            >
              Back to budgets
            </button>
          </div>

          {step3Tab === 'pipeline' ? (
            <DashboardCard title="AI Agent Pipeline">
              {running ? (
                <div className="mb-4 flex items-center gap-2 text-sm text-slate-500">
                  <Loader2 className="h-4 w-4 animate-spin text-brand-600" />
                  Fetching Google Ads data and running AI agents…
                </div>
              ) : null}
              {(running && liveStepStatus) || analyzerData || liveStepStatus ? (
                <PipelineSteps
                  stepStatus={
                    running && liveStepStatus
                      ? liveStepStatus
                      : analyzerData?.step_status ?? liveStepStatus!
                  }
                />
              ) : (
                <p className="text-sm text-slate-500">No analyzer run yet.</p>
              )}
              {!running && runError ? (
                <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
                  <strong>Run failed:</strong> {runError}
                  <p className="mt-2 text-rose-800/80">
                    Go back to Budgets &amp; upload and click Run Analyzer again. Make sure the API is
                    running (UI proxies to port 8010).
                  </p>
                </div>
              ) : null}
              {!running && analyzerData && Object.keys(analyzerData.pipeline_errors ?? {}).length > 0 ? (
                <div className="mt-4 space-y-2">
                  {Object.entries(analyzerData.pipeline_errors).map(([pipelineStep, message]) => (
                    <div
                      key={pipelineStep}
                      className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
                    >
                      <strong className="capitalize">{pipelineStep.replace('_', ' ')}:</strong>{' '}
                      {message}
                    </div>
                  ))}
                </div>
              ) : null}
              {!running && analyzerData ? (
                <div className="mt-6">
                  <PipelineTabs data={analyzerData} />
                </div>
              ) : null}
            </DashboardCard>
          ) : (
            <ChatPanel config={config} />
          )}
        </div>
      ) : null}
    </div>
  )
}
