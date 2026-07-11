import { Download, FileSpreadsheet, Play, Upload } from 'lucide-react'
import { useRef, useState, type FormEvent } from 'react'
import { toast } from 'sonner'
import {
  defaultCampaignFields,
  defaultMonthDates,
  type AnalyzerRunPayload,
  type AppConfig,
  type CampaignFieldPayload,
} from '../../services/api'
import {
  buildAnalyzerPayloadFromUpload,
  downloadSampleCampaignFile,
  isIsoDate,
  parseCampaignWorkbook,
  type UploadCampaignRow,
} from '../../utils/excelCampaignParser'
import { formatCurrency } from '../../utils/format'
import { DashboardCard } from '../ui/DashboardCard'
import { DataTable } from '../ui/DataTable'

const CAMPAIGN_TYPES = [
  'Search campaigns',
  'Video campaigns',
  'Demand Gen campaigns',
  'Performance Max campaigns',
] as const

type InputMode = 'form' | 'upload'

interface StepBudgetsUploadProps {
  accountCid: string
  config: AppConfig | null
  loading: boolean
  onBack: () => void
  onRun: (payload: AnalyzerRunPayload) => void
}

export function StepBudgetsUpload({ accountCid, config, loading, onBack, onRun }: StepBudgetsUploadProps) {
  const dates = defaultMonthDates()
  const [mode, setMode] = useState<InputMode>('form')
  const [accountStart, setAccountStart] = useState(dates.start)
  const [accountEnd, setAccountEnd] = useState(dates.end)
  const [fields, setFields] = useState<Record<string, CampaignFieldPayload>>(defaultCampaignFields())
  const [uploadRows, setUploadRows] = useState<UploadCampaignRow[]>([])
  const [uploadFileName, setUploadFileName] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const updateField = (label: string, patch: Partial<CampaignFieldPayload>) => {
    setFields((prev) => ({ ...prev, [label]: { ...prev[label], ...patch } }))
  }

  const switchMode = (next: InputMode) => {
    setMode(next)
    if (next === 'form') {
      // Keep form independent — clear upload so analysis uses form only.
      setUploadRows([])
      setUploadFileName('')
      if (fileRef.current) fileRef.current.value = ''
    } else {
      // Keep upload independent — reset form to defaults.
      setFields(defaultCampaignFields())
      setAccountStart(dates.start)
      setAccountEnd(dates.end)
    }
  }

  const handleFile = async (file: File | null) => {
    if (!file) return
    try {
      const buffer = await file.arrayBuffer()
      const rows = parseCampaignWorkbook(buffer)
      if (!rows.length) {
        toast.error('No campaign rows found in the file.')
        return
      }
      setUploadRows(rows)
      setUploadFileName(file.name)
      toast.success(`Loaded ${rows.length} campaigns from Excel`, {
        description: 'Click Run Analyzer to analyze this uploaded data (form is not used).',
      })
    } catch (error) {
      toast.error('Could not parse Excel/CSV', {
        description: error instanceof Error ? error.message : 'Check the sample format.',
      })
    }
  }

  const runFromForm = (event: FormEvent) => {
    event.preventDefault()
    if (!accountCid.trim()) {
      toast.error('Select an Account / Customer ID in step 1.')
      return
    }
    onRun({
      account: accountCid.trim(),
      account_start_date: accountStart,
      account_end_date: accountEnd,
      search_campaigns: fields['Search campaigns'],
      video_campaigns: fields['Video campaigns'],
      demand_gen_campaigns: fields['Demand Gen campaigns'],
      performance_max_campaigns: fields['Performance Max campaigns'],
    })
  }

  const runFromUpload = () => {
    if (!accountCid.trim()) {
      toast.error('Select an Account / Customer ID in step 1.')
      return
    }
    if (!uploadRows.length) {
      toast.error('Upload an Excel/CSV file first.')
      return
    }
    const badDate = uploadRows.find(
      (row) => !isIsoDate(row.start_date) || !isIsoDate(row.end_date),
    )
    if (badDate) {
      toast.error('Invalid dates in Excel upload', {
        description: 'Use DD/MM/YYYY or YYYY-MM-DD (e.g. 11/07/2026 or 2026-07-11).',
      })
      return
    }
    const payload = buildAnalyzerPayloadFromUpload(uploadRows, accountCid)
    onRun(payload)
  }

  return (
    <div className="space-y-6">
      <DashboardCard
        title="Budgets input"
        subtitle={`Account ${accountCid} · choose one path only: Type form OR Upload Excel`}
      >
        <div className="mb-5 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => switchMode('form')}
            className={`rounded-full px-4 py-2 text-xs font-semibold ${
              mode === 'form' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600'
            }`}
          >
            Type form
          </button>
          <button
            type="button"
            onClick={() => switchMode('upload')}
            className={`rounded-full px-4 py-2 text-xs font-semibold ${
              mode === 'upload' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600'
            }`}
          >
            Upload Excel
          </button>
          {mode === 'upload' ? (
            <button
              type="button"
              onClick={downloadSampleCampaignFile}
              className="ml-auto inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              <Download className="h-3.5 w-3.5" />
              Download sample data
            </button>
          ) : null}
        </div>

        {mode === 'upload' ? (
          <div className="space-y-6">
            <div className="rounded-2xl border border-dashed border-brand-300 bg-brand-50/40 px-5 py-8 text-center">
              <FileSpreadsheet className="mx-auto mb-3 h-8 w-8 text-brand-600" />
              <p className="mb-1 text-sm font-semibold text-slate-800">Upload Excel / CSV for analysis</p>
              <p className="mb-4 text-xs text-slate-500">
                Columns: Campaign Type, Budget, Start Date, End Date
              </p>
              <input
                ref={fileRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                className="hidden"
                onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
              />
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
              >
                <Upload className="h-4 w-4" />
                {uploadRows.length ? 'Replace file' : 'Choose file'}
              </button>
              {uploadFileName ? (
                <p className="mt-3 text-xs font-medium text-emerald-700">
                  Ready: {uploadFileName} ({uploadRows.length} rows)
                </p>
              ) : null}
            </div>

            {uploadRows.length > 0 ? (
              <div>
                <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
                  Uploaded Excel data (used for Run Analyzer)
                </p>
                <DataTable
                  columns={[
                    { key: 'type', label: 'Campaign Type' },
                    { key: 'budget', label: 'Budget', align: 'right' },
                    { key: 'start', label: 'Start Date' },
                    { key: 'end', label: 'End Date' },
                  ]}
                  filterPlaceholder="Filter uploaded rows…"
                  rows={uploadRows.map((row) => ({
                    type: row.campaign_type || '—',
                    budget: formatCurrency(row.budget, 'INR'),
                    start: row.start_date,
                    end: row.end_date,
                  }))}
                  sortValues={uploadRows.map((row) => ({
                    type: row.campaign_type || '',
                    budget: row.budget,
                    start: row.start_date,
                    end: row.end_date,
                  }))}
                />
              </div>
            ) : null}

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={onBack}
                className="rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50"
              >
                Back
              </button>
              <button
                type="button"
                onClick={runFromUpload}
                disabled={loading || !config?.google_ads_configured || uploadRows.length === 0}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-brand-600/20 hover:bg-brand-700 disabled:opacity-60"
              >
                <Play className="h-4 w-4" />
                {loading ? 'Running Analyzer…' : 'Run Analyzer on Excel'}
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={runFromForm} className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-700">Account start</span>
                <input
                  type="date"
                  value={accountStart}
                  onChange={(e) => setAccountStart(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
                  required
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-700">Account end</span>
                <input
                  type="date"
                  value={accountEnd}
                  onChange={(e) => setAccountEnd(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
                  required
                />
              </label>
            </div>

            <div>
              <p className="mb-3 text-xs font-bold uppercase tracking-wide text-brand-600">
                Campaign type form
              </p>
              <div className="space-y-3">
                {CAMPAIGN_TYPES.map((label) => (
                  <div key={label} className="grid gap-3 rounded-2xl border border-slate-100 p-4 md:grid-cols-4">
                    <p className="self-center text-sm font-semibold text-slate-700">{label}</p>
                    <label className="block">
                      <span className="mb-1 block text-xs text-slate-500">Budget / limit (₹)</span>
                      <input
                        type="number"
                        min={0}
                        step={1000}
                        value={fields[label].budget}
                        onChange={(e) => updateField(label, { budget: Number(e.target.value) })}
                        className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                      />
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-xs text-slate-500">Start date</span>
                      <input
                        type="date"
                        value={fields[label].start_date}
                        onChange={(e) => updateField(label, { start_date: e.target.value })}
                        className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                      />
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-xs text-slate-500">End date</span>
                      <input
                        type="date"
                        value={fields[label].end_date}
                        onChange={(e) => updateField(label, { end_date: e.target.value })}
                        className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                      />
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={onBack}
                className="rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading || !config?.google_ads_configured}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-brand-600/20 hover:bg-brand-700 disabled:opacity-60"
              >
                <Play className="h-4 w-4" />
                {loading ? 'Running Analyzer…' : 'Run Analyzer'}
              </button>
            </div>
          </form>
        )}
      </DashboardCard>
    </div>
  )
}
