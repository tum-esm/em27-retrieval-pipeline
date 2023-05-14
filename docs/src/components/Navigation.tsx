import React from 'react'
import Link from 'next/link'
import clsx from 'clsx'
import { Tag } from '@/components/Tag'
import { useRouter } from 'next/router'

function NavLink(props: {
  children: React.ReactNode
  href: string
  active: boolean
  tag?: string
  isAnchorLink?: boolean
}) {
  return (
    <Link
      href={props.href}
      aria-current={props.active ? 'page' : undefined}
      className={clsx(
        'flex justify-between gap-2 py-1 pr-3 text-sm transition',
        props.isAnchorLink ? 'pl-7' : 'pl-4',
        props.active
          ? 'text-zinc-900 dark:text-white'
          : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white'
      )}
    >
      <span className="truncate">{props.children}</span>
      {props.tag && <Tag variant="small" color="zinc" label={props.tag} />}
    </Link>
  )
}

function NavigationGroup(props: {
  group: {
    title: string
    links: { href: string; title: string }[]
  }
  className: string
}) {
  let router = useRouter()

  return (
    <li className={clsx('relative mt-6', props.className)}>
      <h2 className="text-xs font-semibold text-zinc-900 dark:text-white">
        {props.group.title}
      </h2>
      <div className="relative pl-2 mt-3">
        <div className="absolute inset-y-0 w-px left-2 bg-zinc-900/10 dark:bg-white/5" />
        <ul role="list" className="border-l border-transparent">
          {props.group.links.map((link) => (
            <NavLink
              key={link.href}
              href={link.href}
              active={link.href === router.pathname}
            >
              {link.title}
            </NavLink>
          ))}
        </ul>
      </div>
    </li>
  )
}

export const navigation: {
  title: string
  links: { href: string; title: string }[]
}[] = [
  {
    title: 'Guides',
    links: [
      { title: 'Introduction', href: '/' },
      { title: 'Quickstart', href: '/quickstart' },
      { title: 'SDKs', href: '/sdks' },
      { title: 'Authentication', href: '/authentication' },
      { title: 'Pagination', href: '/pagination' },
      { title: 'Errors', href: '/errors' },
      { title: 'Webhooks', href: '/webhooks' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { title: 'Contacts', href: '/contacts' },
      { title: 'Conversations', href: '/conversations' },
      { title: 'Messages', href: '/messages' },
      { title: 'Groups', href: '/groups' },
      { title: 'Attachments', href: '/attachments' },
    ],
  },
]

export function Navigation(props: { className?: string }) {
  return (
    <nav className={props.className || ''}>
      <ul role="list">
        {navigation.map((group, groupIndex) => (
          <NavigationGroup
            key={group.title}
            group={group}
            className={groupIndex === 0 ? 'md:mt-0' : ''}
          />
        ))}
      </ul>
    </nav>
  )
}
