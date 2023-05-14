import { Children, useEffect, useState } from 'react'
import clsx from 'clsx'

import { Tag } from '@/components/Tag'

function ClipboardIcon(props: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" {...props}>
      <path
        strokeWidth="0"
        d="M5.5 13.5v-5a2 2 0 0 1 2-2l.447-.894A2 2 0 0 1 9.737 4.5h.527a2 2 0 0 1 1.789 1.106l.447.894a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-5a2 2 0 0 1-2-2Z"
      />
      <path
        fill="none"
        strokeLinejoin="round"
        d="M12.5 6.5a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-5a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2m5 0-.447-.894a2 2 0 0 0-1.79-1.106h-.527a2 2 0 0 0-1.789 1.106L7.5 6.5m5 0-1 1h-3l-1-1"
      />
    </svg>
  )
}

function CopyButton(props: { code: string }) {
  let [copyCount, setCopyCount] = useState(0)
  let copied = copyCount > 0

  useEffect(() => {
    if (copyCount > 0) {
      let timeout = setTimeout(() => setCopyCount(0), 1000)
      return () => {
        clearTimeout(timeout)
      }
    }
  }, [copyCount])

  return (
    <button
      type="button"
      className={clsx(
        'group/button absolute right-4 top-3.5 overflow-hidden rounded-full py-1 pl-2 pr-3 text-2xs font-medium opacity-0 backdrop-blur transition focus:opacity-100 group-hover:opacity-100',
        copied
          ? 'bg-emerald-400/10 ring-1 ring-inset ring-emerald-400/20'
          : 'bg-white/5 hover:bg-white/7.5 dark:bg-white/2.5 dark:hover:bg-white/5'
      )}
      onClick={() => {
        window.navigator.clipboard.writeText(props.code).then(() => {
          setCopyCount((count) => count + 1)
        })
      }}
    >
      <span
        aria-hidden={copied}
        className={clsx(
          'pointer-events-none flex items-center gap-0.5 text-zinc-400 transition duration-300',
          copied && '-translate-y-1.5 opacity-0'
        )}
      >
        <ClipboardIcon className="w-5 h-5 transition-colors fill-zinc-500/20 stroke-zinc-500 group-hover/button:stroke-zinc-400" />
        Copy
      </span>
      <span
        aria-hidden={!copied}
        className={clsx(
          'pointer-events-none absolute inset-0 flex items-center justify-center text-emerald-400 transition duration-300',
          !copied && 'translate-y-1.5 opacity-0'
        )}
      >
        Copied!
      </span>
    </button>
  )
}

function CodePanelHeader(props: { tag?: string; label?: string }) {
  if (!props.tag && !props.label) {
    return null
  }

  return (
    <div className="flex h-9 items-center gap-2 border-y border-b-white/7.5 border-t-transparent bg-white/2.5 bg-zinc-900 px-4 dark:border-b-white/5 dark:bg-white/1">
      {props.tag && (
        <div className="flex dark">
          <Tag variant="small" label={props.tag} color="emerald" />
        </div>
      )}
      {props.tag && props.label && (
        <span className="h-0.5 w-0.5 rounded-full bg-zinc-500" />
      )}
      {props.label && (
        <span className="font-mono text-xs text-zinc-400">{props.label}</span>
      )}
    </div>
  )
}

function CodePanel(props: {
  tag: string
  label: string
  code: string
  children: React.ReactNode
}) {
  let child: any = Children.only(props.children)

  return (
    <div className="group dark:bg-white/2.5">
      <CodePanelHeader
        tag={child.props.tag ?? props.tag}
        label={child.props.label ?? props.label}
      />
      <div className="relative">
        <pre className="p-4 overflow-x-auto text-xs text-white">
          {props.children}
        </pre>
        <CopyButton code={child.props.code ?? props.code} />
      </div>
    </div>
  )
}

export function Code(props: { children: string }) {
  return <code dangerouslySetInnerHTML={{ __html: props.children }} />
}

export function Pre(props: { children: React.ReactNode }) {
  return props.children
}
