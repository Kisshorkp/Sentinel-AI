import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import {
  useEffect,
  useMemo,
  useState,
  type ReactElement,
  type ReactNode,
} from 'react'

export interface DataTableColumn {
  key: string
  label: string
  align?: 'left' | 'right'
  /** When false, header is not clickable. Default true when enableSort. */
  sortable?: boolean
}

export type SortPrimitive = string | number | boolean | null | undefined

interface DataTableProps {
  columns: DataTableColumn[]
  rows: Array<Record<string, ReactNode>>
  /**
   * Optional raw values (same keys as columns) used for sort/filter.
   * Prefer this for currency / ReactNode cells.
   */
  sortValues?: Array<Record<string, SortPrimitive>>
  emptyMessage?: string
  enableFilter?: boolean
  enableSort?: boolean
  enablePagination?: boolean
  defaultPageSize?: number
  pageSizeOptions?: number[]
  filterPlaceholder?: string
}

type SortDir = 'asc' | 'desc'

function cellToText(value: ReactNode): string {
  if (value == null || typeof value === 'boolean') return ''
  if (typeof value === 'string' || typeof value === 'number') return String(value)
  if (Array.isArray(value)) return value.map(cellToText).join(' ')
  if (typeof value === 'object' && 'props' in (value as object)) {
    const el = value as ReactElement<{ children?: ReactNode }>
    return cellToText(el.props?.children)
  }
  return ''
}

/** Parse display strings like ₹1,23,456.50 or 12.5% into numbers when possible. */
function coerceSortable(value: SortPrimitive | ReactNode): { num: number | null; text: string } {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return { num: value, text: String(value) }
  }
  if (typeof value === 'boolean') {
    return { num: value ? 1 : 0, text: String(value) }
  }
  const text =
    typeof value === 'string' || typeof value === 'number'
      ? String(value)
      : cellToText(value as ReactNode)
  const cleaned = text
    .replace(/[₹$,%\s]/g, '')
    .replace(/,/g, '')
    .trim()
  if (cleaned === '' || cleaned === '—' || cleaned.toLowerCase() === 'n/a') {
    return { num: null, text }
  }
  // Dates YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}/.test(text.trim())) {
    const t = Date.parse(text.trim().slice(0, 10))
    if (!Number.isNaN(t)) return { num: t, text }
  }
  const n = Number(cleaned)
  if (Number.isFinite(n) && /[\d.]/.test(cleaned)) {
    return { num: n, text }
  }
  return { num: null, text }
}

function compareValues(
  a: SortPrimitive | ReactNode,
  b: SortPrimitive | ReactNode,
  dir: SortDir,
): number {
  const left = coerceSortable(a)
  const right = coerceSortable(b)
  let result = 0
  if (left.num != null && right.num != null) {
    result = left.num - right.num
  } else if (left.num != null) {
    result = -1
  } else if (right.num != null) {
    result = 1
  } else {
    result = left.text.localeCompare(right.text, undefined, { numeric: true, sensitivity: 'base' })
  }
  return dir === 'asc' ? result : -result
}

const DEFAULT_PAGE_SIZES = [10, 25, 50, 100]

export function DataTable({
  columns,
  rows,
  sortValues,
  emptyMessage = 'No data available.',
  enableFilter = true,
  enableSort = true,
  enablePagination = true,
  defaultPageSize = 10,
  pageSizeOptions = DEFAULT_PAGE_SIZES,
  filterPlaceholder = 'Filter table…',
}: DataTableProps) {
  const [filter, setFilter] = useState('')
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(defaultPageSize)

  const indexed = useMemo(
    () =>
      rows.map((row, index) => ({
        row,
        sort: sortValues?.[index],
        index,
      })),
    [rows, sortValues],
  )

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase()
    if (!q) return indexed
    return indexed.filter(({ row, sort }) => {
      return columns.some((col) => {
        const fromSort = sort?.[col.key]
        if (fromSort != null && String(fromSort).toLowerCase().includes(q)) return true
        return cellToText(row[col.key]).toLowerCase().includes(q)
      })
    })
  }, [indexed, filter, columns])

  const sorted = useMemo(() => {
    if (!enableSort || !sortKey) return filtered
    const col = columns.find((c) => c.key === sortKey)
    if (!col || col.sortable === false) return filtered
    return [...filtered].sort((a, b) => {
      const av = a.sort?.[sortKey] ?? a.row[sortKey]
      const bv = b.sort?.[sortKey] ?? b.row[sortKey]
      return compareValues(av, bv, sortDir)
    })
  }, [filtered, enableSort, sortKey, sortDir, columns])

  const total = sorted.length
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const safePage = Math.min(page, totalPages)

  const pageRows = useMemo(() => {
    if (!enablePagination) return sorted
    const start = (safePage - 1) * pageSize
    return sorted.slice(start, start + pageSize)
  }, [sorted, enablePagination, safePage, pageSize])

  useEffect(() => {
    setPage(1)
  }, [filter, pageSize, sortKey, sortDir, rows])

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  const toggleSort = (key: string, sortable?: boolean) => {
    if (!enableSort || sortable === false) return
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const rangeStart = total === 0 ? 0 : (safePage - 1) * pageSize + 1
  const rangeEnd = Math.min(safePage * pageSize, total)

  if (!rows.length) {
    return <p className="rounded-2xl bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">{emptyMessage}</p>
  }

  return (
    <div className="space-y-3">
      {(enableFilter || enablePagination) && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          {enableFilter ? (
            <label className="relative min-w-[200px] flex-1 max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="search"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder={filterPlaceholder}
                className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-slate-700 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
              />
            </label>
          ) : (
            <span />
          )}

          {enablePagination ? (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>Rows</span>
              <select
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
                className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm font-medium text-slate-700 shadow-sm outline-none focus:border-brand-500"
              >
                {pageSizeOptions.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
        </div>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-100">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              {columns.map((col) => {
                const canSort = enableSort && col.sortable !== false
                const active = sortKey === col.key
                return (
                  <th
                    key={col.key}
                    className={`px-4 py-3 ${col.align === 'right' ? 'text-right' : ''} ${
                      canSort ? 'cursor-pointer select-none hover:text-slate-600' : ''
                    }`}
                    onClick={() => toggleSort(col.key, col.sortable)}
                    aria-sort={
                      !canSort || !active ? 'none' : sortDir === 'asc' ? 'ascending' : 'descending'
                    }
                  >
                    <span
                      className={`inline-flex items-center gap-1.5 ${
                        col.align === 'right' ? 'flex-row-reverse' : ''
                      }`}
                    >
                      {col.label}
                      {canSort ? (
                        active ? (
                          sortDir === 'asc' ? (
                            <ArrowUp className="h-3.5 w-3.5 text-brand-600" />
                          ) : (
                            <ArrowDown className="h-3.5 w-3.5 text-brand-600" />
                          )
                        ) : (
                          <ArrowUpDown className="h-3.5 w-3.5 opacity-40" />
                        )
                      ) : null}
                    </span>
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {pageRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-sm text-slate-500">
                  {filter.trim() ? 'No rows match this filter.' : emptyMessage}
                </td>
              </tr>
            ) : (
              pageRows.map(({ row, index }) => (
                <tr key={index} className="border-t border-slate-100">
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`px-4 py-3 text-slate-700 ${col.align === 'right' ? 'text-right' : ''}`}
                    >
                      {row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {enablePagination ? (
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-500">
          <p>
            Showing <span className="font-semibold text-slate-700">{rangeStart}</span>–
            <span className="font-semibold text-slate-700">{rangeEnd}</span> of{' '}
            <span className="font-semibold text-slate-700">{total}</span>
            {filter.trim() && total !== rows.length ? (
              <span className="text-slate-400"> (filtered from {rows.length})</span>
            ) : null}
          </p>
          <div className="flex items-center gap-1">
            <button
              type="button"
              disabled={safePage <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-600 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Prev
            </button>
            <span className="px-2 text-xs font-medium text-slate-600">
              Page {safePage} / {totalPages}
            </span>
            <button
              type="button"
              disabled={safePage >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-600 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
