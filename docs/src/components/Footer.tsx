import Link from 'next/link'
import { useRouter } from 'next/router'

import { Button } from '@/components/Button'
import { navigation } from '@/components/Navigation'

function PageLink(props: {
  label: string
  page: {
    title: string
    href: string
  }
  previous?: boolean
}) {
  return (
    <>
      <Button
        href={props.page.href}
        aria-label={`${props.label}: ${props.page.title}`}
        variant="secondary"
        arrow={props.previous ? 'left' : 'right'}
      >
        {props.label}
      </Button>
      <Link
        href={props.page.href}
        tabIndex={-1}
        aria-hidden="true"
        className="text-base font-semibold transition text-zinc-900 hover:text-zinc-600 dark:text-white dark:hover:text-zinc-300"
      >
        {props.page.title}
      </Link>
    </>
  )
}

function PageNavigation() {
  let router = useRouter()
  let allPages = navigation.flatMap((group) => group.links)
  let currentPageIndex = allPages.findIndex(
    (page) => page.href === router.pathname
  )

  if (currentPageIndex === -1) {
    return null
  }

  let previousPage = allPages[currentPageIndex - 1]
  let nextPage = allPages[currentPageIndex + 1]

  if (!previousPage && !nextPage) {
    return null
  }

  return (
    <div className="flex">
      {previousPage && (
        <div className="flex flex-col items-start gap-3">
          <PageLink label="Previous" page={previousPage} previous />
        </div>
      )}
      {nextPage && (
        <div className="flex flex-col items-end gap-3 ml-auto">
          <PageLink label="Next" page={nextPage} />
        </div>
      )}
    </div>
  )
}

function WebsiteIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      strokeWidth="2"
      stroke="currentColor"
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5 transition stroke-zinc-600 group-hover:stroke-zinc-800 dark:group-hover:stroke-zinc-400"
      aria-hidden="true"
    >
      <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
      <path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0"></path>
      <path d="M3.6 9h16.8"></path>
      <path d="M3.6 15h16.8"></path>
      <path d="M11.5 3a17 17 0 0 0 0 18"></path>
      <path d="M12.5 3a17 17 0 0 1 0 18"></path>
    </svg>
  )
}

function GitHubIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      stroke-width="1"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-5 h-5 transition fill-zinc-600 group-hover:fill-zinc-800 dark:group-hover:fill-zinc-400"
      aria-hidden="true"
    >
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M5.315 2.1c.791 -.113 1.9 .145 3.333 .966l.272 .161l.16 .1l.397 -.083a13.3 13.3 0 0 1 4.59 -.08l.456 .08l.396 .083l.161 -.1c1.385 -.84 2.487 -1.17 3.322 -1.148l.164 .008l.147 .017l.076 .014l.05 .011l.144 .047a1 1 0 0 1 .53 .514a5.2 5.2 0 0 1 .397 2.91l-.047 .267l-.046 .196l.123 .163c.574 .795 .93 1.728 1.03 2.707l.023 .295l.007 .272c0 3.855 -1.659 5.883 -4.644 6.68l-.245 .061l-.132 .029l.014 .161l.008 .157l.004 .365l-.002 .213l-.003 3.834a1 1 0 0 1 -.883 .993l-.117 .007h-6a1 1 0 0 1 -.993 -.883l-.007 -.117v-.734c-1.818 .26 -3.03 -.424 -4.11 -1.878l-.535 -.766c-.28 -.396 -.455 -.579 -.589 -.644l-.048 -.019a1 1 0 0 1 .564 -1.918c.642 .188 1.074 .568 1.57 1.239l.538 .769c.76 1.079 1.36 1.459 2.609 1.191l.001 -.678l-.018 -.168a5.03 5.03 0 0 1 -.021 -.824l.017 -.185l.019 -.12l-.108 -.024c-2.976 -.71 -4.703 -2.573 -4.875 -6.139l-.01 -.31l-.004 -.292a5.6 5.6 0 0 1 .908 -3.051l.152 -.222l.122 -.163l-.045 -.196a5.2 5.2 0 0 1 .145 -2.642l.1 -.282l.106 -.253a1 1 0 0 1 .529 -.514l.144 -.047l.154 -.03z" />
    </svg>
  )
}

function SocialLink(props: {
  href: string
  variant: 'website' | 'github'
  srLabel: string
}) {
  return (
    <Link href={props.href} className="group">
      <span className="sr-only">{props.srLabel}</span>
      {props.variant === 'website' && <WebsiteIcon />}
      {props.variant === 'github' && <GitHubIcon />}
    </Link>
  )
}

function SmallPrint() {
  return (
    <div className="flex flex-col items-center justify-between gap-5 pt-8 border-t border-zinc-900/5 dark:border-white/5 sm:flex-row">
      <p className="text-xs text-zinc-600 dark:text-zinc-400">
        &copy; TUM Professorship of Environmental Sensing and Modeling{' '}
        {new Date().getFullYear()}. All rights reserved.
      </p>
      <div className="flex gap-4">
        <SocialLink
          href="https://www.ee.cit.tum.de/en/esm"
          variant="website"
          srLabel="Visit our research group's website"
        />
        <SocialLink
          href="https://github.com/tum-esm/automated-retrival-pipeline"
          variant="github"
          srLabel="Follow us on GitHub"
        />
      </div>
    </div>
  )
}

export function Footer() {
  let router = useRouter()

  return (
    <footer className="max-w-2xl pb-16 mx-auto space-y-10 lg:max-w-5xl">
      <PageNavigation />
      <SmallPrint />
    </footer>
  )
}
