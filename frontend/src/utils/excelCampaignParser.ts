/** Parse campaign Excel/CSV upload into analyzer form fields. */

import * as XLSX from 'xlsx'
import { defaultMonthDates, type CampaignFieldPayload, type AnalyzerRunPayload } from '../services/api'

export type UploadCampaignRow = {
  cid: string
  campaign_name: string
  campaign_id: string
  campaign_type: string
  budget: number
  start_date: string
  end_date: string
  label: string
  action: string
}

const TYPE_MAP: Record<string, string> = {
  search: 'Search campaigns',
  video: 'Video campaigns',
  'demand gen': 'Demand Gen campaigns',
  demand_gen: 'Demand Gen campaigns',
  demandgen: 'Demand Gen campaigns',
  display: 'Demand Gen campaigns',
  'performance max': 'Performance Max campaigns',
  pmax: 'Performance Max campaigns',
  'perf max': 'Performance Max campaigns',
}

function normalizeHeader(value: unknown): string {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .replace(/[_/]+/g, ' ')
    .replace(/\s+/g, ' ')
}

function toIsoDate(year: number, month: number, day: number): string | null {
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) return null
  if (month < 1 || month > 12 || day < 1 || day > 31) return null
  // Reject impossible calendar dates (e.g. 31 Feb)
  const dt = new Date(year, month - 1, day)
  if (dt.getFullYear() !== year || dt.getMonth() !== month - 1 || dt.getDate() !== day) return null
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function parseSlashDate(text: string): string | null {
  const slash = text.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/)
  if (!slash) return null
  const a = Number(slash[1])
  const b = Number(slash[2])
  const year = Number(slash[3])

  // Prefer DD/MM/YYYY (INR). Disambiguate when one side is > 12.
  if (a > 12 && b >= 1 && b <= 12) {
    return toIsoDate(year, b, a) // D/M/YYYY
  }
  if (b > 12 && a >= 1 && a <= 12) {
    return toIsoDate(year, a, b) // M/D/YYYY
  }
  // Ambiguous (both <= 12): day-first for this product (INR)
  return toIsoDate(year, b, a)
}

function excelDateToIso(value: unknown): string {
  const fallback = defaultMonthDates().start
  if (value == null || value === '') return fallback

  // Native Date from xlsx cellDates:true
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return toIsoDate(value.getFullYear(), value.getMonth() + 1, value.getDate()) ?? fallback
  }

  // Excel serial number
  if (typeof value === 'number' && Number.isFinite(value)) {
    const parsed = XLSX.SSF.parse_date_code(value)
    if (parsed) return toIsoDate(parsed.y, parsed.m, parsed.d) ?? fallback
  }

  const text = String(value).trim()

  // Already ISO (validate month/day — reject e.g. 2026-15-07)
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const [y, m, d] = text.slice(0, 10).split('-').map(Number)
    return toIsoDate(y, m, d) ?? fallback
  }

  const fromSlash = parseSlashDate(text)
  if (fromSlash) return fromSlash

  // Avoid locale-dependent Date("15/07/2026") parsing
  return fallback
}

function isIsoDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const [y, m, d] = value.split('-').map(Number)
  return toIsoDate(y, m, d) !== null
}

export { isIsoDate, excelDateToIso }

function pick(row: Record<string, unknown>, aliases: string[]): unknown {
  const entries = Object.entries(row)
  for (const alias of aliases) {
    const found = entries.find(([key]) => normalizeHeader(key) === alias)
    if (found) return found[1]
  }
  return undefined
}

function mapCampaignType(raw: string): string | null {
  const key = normalizeHeader(raw)
  return TYPE_MAP[key] ?? null
}

export function parseCampaignWorkbook(file: ArrayBuffer): UploadCampaignRow[] {
  const workbook = XLSX.read(file, { type: 'array', cellDates: true })
  const sheet = workbook.Sheets[workbook.SheetNames[0]]
  const json = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, { defval: '' })

  return json
    .map((row) => {
      const campaignTypeRaw = String(pick(row, ['campaign type', 'type', 'channel']) ?? '')
      return {
        cid: String(pick(row, ['cid', 'customer id', 'account', 'customer']) ?? '').trim(),
        campaign_name: String(pick(row, ['campaign name', 'campaign', 'name']) ?? '').trim(),
        campaign_id: String(pick(row, ['campaign id', 'id']) ?? '').trim(),
        campaign_type: campaignTypeRaw,
        budget: Number(pick(row, ['budget', 'budget / limit', 'monthly budget']) ?? 0) || 0,
        start_date: excelDateToIso(pick(row, ['start date', 'start', 'start_date'])),
        end_date: excelDateToIso(pick(row, ['end date', 'end', 'end_date'])),
        label: String(pick(row, ['label']) ?? '').trim(),
        action: String(pick(row, ['action']) ?? '').trim(),
      } satisfies UploadCampaignRow
    })
    .filter((row) => row.campaign_type || row.campaign_id || row.budget > 0 || row.cid)
}

export function aggregateUploadToCampaignFields(
  rows: UploadCampaignRow[],
): {
  fields: Record<string, CampaignFieldPayload>
  mappedCount: number
  totalBudget: number
  account_start: string
  account_end: string
} {
  const dates = defaultMonthDates()
  const buckets: Record<
    string,
    { budget: number; start_date: string; end_date: string; label: string }
  > = {
    'Search campaigns': { budget: 0, start_date: dates.start, end_date: dates.end, label: 'Search campaigns' },
    'Video campaigns': { budget: 0, start_date: dates.start, end_date: dates.end, label: 'Video campaigns' },
    'Demand Gen campaigns': {
      budget: 0,
      start_date: dates.start,
      end_date: dates.end,
      label: 'Demand Gen campaigns',
    },
    'Performance Max campaigns': {
      budget: 0,
      start_date: dates.start,
      end_date: dates.end,
      label: 'Performance Max campaigns',
    },
  }

  const seenStart: Record<string, boolean> = {}
  const seenEnd: Record<string, boolean> = {}
  let mappedCount = 0
  let totalBudget = 0
  let globalStart = ''
  let globalEnd = ''

  for (const row of rows) {
    totalBudget += row.budget
    const start = isIsoDate(row.start_date) ? row.start_date : excelDateToIso(row.start_date)
    const end = isIsoDate(row.end_date) ? row.end_date : excelDateToIso(row.end_date)
    if (!globalStart || start < globalStart) globalStart = start
    if (!globalEnd || end > globalEnd) globalEnd = end

    const type = mapCampaignType(row.campaign_type)
    if (!type || !buckets[type]) continue
    mappedCount += 1
    buckets[type].budget += row.budget

    if (!seenStart[type] || start < buckets[type].start_date) {
      buckets[type].start_date = start
      seenStart[type] = true
    }
    if (!seenEnd[type] || end > buckets[type].end_date) {
      buckets[type].end_date = end
      seenEnd[type] = true
    }
  }

  // No Campaign Type in file — put full budget on Search; shared dates on all types.
  if (mappedCount === 0) {
    for (const bucket of Object.values(buckets)) {
      if (globalStart) bucket.start_date = globalStart
      if (globalEnd) bucket.end_date = globalEnd
      bucket.budget = 0
    }
    buckets['Search campaigns'].budget = Math.round(totalBudget * 100) / 100
  }

  return {
    fields: Object.fromEntries(
      Object.entries(buckets).map(([label, value]) => [
        label,
        {
          label,
          budget: Math.round(value.budget * 100) / 100,
          start_date: value.start_date,
          end_date: value.end_date,
        } satisfies CampaignFieldPayload,
      ]),
    ),
    mappedCount,
    totalBudget: Math.round(totalBudget * 100) / 100,
    account_start: globalStart || dates.start,
    account_end: globalEnd || dates.end,
  }
}

export function buildAnalyzerPayloadFromUpload(
  rows: UploadCampaignRow[],
  accountCid: string,
): AnalyzerRunPayload {
  const { fields, account_start, account_end } = aggregateUploadToCampaignFields(rows)
  const cid = accountCid.trim() || rows.find((r) => r.cid)?.cid || ''
  return {
    account: cid,
    account_start_date: account_start,
    account_end_date: account_end,
    search_campaigns: fields['Search campaigns'],
    video_campaigns: fields['Video campaigns'],
    demand_gen_campaigns: fields['Demand Gen campaigns'],
    performance_max_campaigns: fields['Performance Max campaigns'],
  }
}

export function downloadSampleCampaignFile() {
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}sample-campaign-upload.csv`
  link.download = 'sample-campaign-upload.csv'
  document.body.appendChild(link)
  link.click()
  link.remove()
}
