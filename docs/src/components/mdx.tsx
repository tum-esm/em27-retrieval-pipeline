import Link from 'next/link'
import clsx from 'clsx'

import { Heading } from '@/components/Heading'

export const a = Link
export { Button } from '@/components/Button'
export { Code as code, Pre as pre } from '@/components/Code'

export const h2 = function H2(props: any) {
  return <Heading level={2} {...props} />
}

function InfoIcon(props: any) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" {...props}>
      <circle cx="8" cy="8" r="8" strokeWidth="0" />
      <path
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
        d="M6.75 7.75h1.5v3.5"
      />
      <circle cx="8" cy="4" r=".5" fill="none" />
    </svg>
  )
}

export function Note(props: { children: React.ReactNode }) {
  return (
    <div className="my-6 flex gap-2.5 rounded-2xl border border-emerald-500/20 bg-emerald-50/50 p-4 leading-6 text-emerald-900 dark:border-emerald-500/30 dark:bg-emerald-500/5 dark:text-emerald-200 dark:[--tw-prose-links-hover:theme(colors.emerald.300)] dark:[--tw-prose-links:theme(colors.white)]">
      <InfoIcon className="flex-none w-4 h-4 mt-1 fill-emerald-500 stroke-white dark:fill-emerald-200/20 dark:stroke-emerald-200" />
      <div className="[&>:first-child]:mt-0 [&>:last-child]:mb-0">
        {props.children}
      </div>
    </div>
  )
}

export function Row(props: { children: React.ReactNode }) {
  return (
    <div className="grid items-start grid-cols-1 gap-x-16 gap-y-10 xl:max-w-none xl:grid-cols-2">
      {props.children}
    </div>
  )
}

export function Col(props: { children: React.ReactNode; sticky?: boolean }) {
  return (
    <div
      className={clsx(
        '[&>:first-child]:mt-0 [&>:last-child]:mb-0',
        props.sticky && 'xl:sticky xl:top-24'
      )}
    >
      {props.children}
    </div>
  )
}

export function Properties(props: { children: React.ReactNode }) {
  return (
    <div className="my-6">
      <ul
        role="list"
        className="m-0 max-w-[calc(theme(maxWidth.lg)-theme(spacing.8))] list-none divide-y divide-zinc-900/5 p-0 dark:divide-white/5"
      >
        {props.children}
      </ul>
    </div>
  )
}

export function Property(props: {
  name: string
  type: string
  children: React.ReactNode
}) {
  return (
    <li className="px-0 py-4 m-0 first:pt-0 last:pb-0">
      <dl className="flex flex-wrap items-center m-0 gap-x-3 gap-y-2">
        <dt className="sr-only">Name</dt>
        <dd>
          <code>{props.name}</code>
        </dd>
        <dt className="sr-only">Type</dt>
        <dd className="font-mono text-xs text-zinc-400 dark:text-zinc-500">
          {props.type}
        </dd>
        <dt className="sr-only">Description</dt>
        <dd className="w-full flex-none [&>:first-child]:mt-0 [&>:last-child]:mb-0">
          {props.children}
        </dd>
      </dl>
    </li>
  )
}
