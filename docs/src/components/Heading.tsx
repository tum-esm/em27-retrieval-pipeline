import { useRef } from 'react'
import Link from 'next/link'
import { useInView } from 'framer-motion'
import { Tag } from '@/components/Tag'
import { remToPx } from '@/lib/remToPx'

function AnchorIcon(props: { className?: string }) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      strokeLinecap="round"
      aria-hidden="true"
      className={props.className || ''}
    >
      <path d="m6.5 11.5-.964-.964a3.535 3.535 0 1 1 5-5l.964.964m2 2 .964.964a3.536 3.536 0 0 1-5 5L8.5 13.5m0-5 3 3" />
    </svg>
  )
}

function Eyebrow(props: { tag: string; label: string }) {
  if (!props.tag && !props.label) {
    return null
  }

  return (
    <div className="flex items-center gap-x-3">
      {props.tag && <Tag label={props.tag} variant="small" color="emerald" />}
      {props.tag && props.label && (
        <span className="h-0.5 w-0.5 rounded-full bg-zinc-300 dark:bg-zinc-600" />
      )}
      {props.label && (
        <span className="font-mono text-xs text-zinc-400">{props.label}</span>
      )}
    </div>
  )
}

function Anchor(props: {
  id: string
  inView: boolean
  children: React.ReactNode
}) {
  return (
    <Link
      href={`#${props.id}`}
      className="group text-inherit no-underline hover:text-inherit"
    >
      {props.inView && (
        <div className="absolute ml-[calc(-1*var(--width))] mt-1 hidden w-[var(--width)] opacity-0 transition [--width:calc(2.625rem+0.5px+50%-min(50%,calc(theme(maxWidth.lg)+theme(spacing.8))))] group-hover:opacity-100 group-focus:opacity-100 md:block lg:z-50 2xl:[--width:theme(spacing.10)]">
          <div className="group/anchor block h-5 w-5 rounded-lg bg-zinc-50 ring-1 ring-inset ring-zinc-300 transition hover:ring-zinc-500 dark:bg-zinc-800 dark:ring-zinc-700 dark:hover:bg-zinc-700 dark:hover:ring-zinc-600">
            <AnchorIcon className="h-5 w-5 stroke-zinc-500 transition dark:stroke-zinc-400 dark:group-hover/anchor:stroke-white" />
          </div>
        </div>
      )}
      {props.children}
    </Link>
  )
}

export function Heading(props: {
  level: 1 | 2 | 3 | 4 | 5
  children: React.ReactNode
  id: string
  tag: string
  label: string
  anchor: boolean
}) {
  const Component: keyof JSX.IntrinsicElements = `h${props.level}`

  let ref = useRef(null)

  let inView = useInView(ref, {
    margin: `${remToPx(-3.5)}px 0px 0px 0px`,
    amount: 'all',
  })

  return (
    <>
      <Eyebrow tag={props.tag} label={props.label} />
      <Component
        ref={ref}
        id={props.anchor ? props.id : undefined}
        className={
          props.tag || props.label ? 'mt-2 scroll-mt-32' : 'scroll-mt-24'
        }
      >
        {props.anchor ? (
          <Anchor id={props.id} inView={inView}>
            {props.children}
          </Anchor>
        ) : (
          props.children
        )}
      </Component>
    </>
  )
}
