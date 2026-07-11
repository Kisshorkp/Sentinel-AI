import clsx from 'clsx'
import type { Components } from 'react-markdown'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const markdownComponents: Components = {
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-full border-collapse text-left text-xs">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">{children}</thead>,
  th: ({ children }) => <th className="border-b border-slate-200 px-3 py-2 font-semibold">{children}</th>,
  td: ({ children }) => <td className="border-b border-slate-100 px-3 py-2 text-slate-700">{children}</td>,
  tr: ({ children }) => <tr className="odd:bg-white even:bg-slate-50/60">{children}</tr>,
  p: ({ children }) => <p className="mb-2 last:mb-0 leading-6">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-5">{children}</ol>,
  li: ({ children }) => <li className="leading-6">{children}</li>,
  h1: ({ children }) => <h1 className="mb-2 text-base font-semibold text-slate-900">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2 text-sm font-semibold text-slate-900">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-2 text-sm font-semibold text-slate-800">{children}</h3>,
  code: ({ children, className }) => {
    const isBlock = Boolean(className)
    if (isBlock) {
      return (
        <code className="block overflow-x-auto rounded-lg bg-slate-900 px-3 py-2 text-[11px] text-slate-100">
          {children}
        </code>
      )
    }
    return <code className="rounded bg-slate-100 px-1 py-0.5 text-[11px] text-slate-800">{children}</code>
  },
  pre: ({ children }) => <pre className="my-2 overflow-x-auto">{children}</pre>,
  a: ({ href, children }) => (
    <a href={href} className="font-medium text-brand-700 underline" target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
}

interface ChatMarkdownProps {
  content: string
  tone?: 'user' | 'assistant'
}

export function ChatMarkdown({ content, tone = 'assistant' }: ChatMarkdownProps) {
  return (
    <div
      className={clsx(
        'chat-markdown break-words',
        tone === 'user' && '[&_*]:text-inherit [&_strong]:text-white [&_a]:text-white',
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
  )
}
