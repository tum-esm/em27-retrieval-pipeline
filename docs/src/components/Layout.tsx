import Link from 'next/link'
import { motion } from 'framer-motion'
import { Footer } from '@/components/Footer'
import { Logo } from '@/components/Logo'
import { Navigation } from '@/components/Navigation'
import { Prose } from '@/components/Prose'

export function Layout(props: { children: React.ReactNode }) {
  return (
    <div className="lg:ml-72 xl:ml-80">
      <motion.header
        layoutScroll
        className="contents lg:pointer-events-none lg:fixed lg:inset-0 lg:z-40 lg:flex"
      >
        <div className="contents lg:pointer-events-auto lg:block lg:w-72 lg:overflow-y-auto lg:border-r lg:border-zinc-900/10 lg:px-6 lg:pb-8 lg:pt-4 lg:dark:border-white/10 xl:w-80">
          <div className="hidden lg:flex">
            <Link href="/" aria-label="Home">
              <Logo className="h-6" />
            </Link>
          </div>
          <Navigation className="hidden lg:mt-10 lg:block" />
        </div>
      </motion.header>
      <div className="relative px-4 pt-0 sm:px-6 lg:px-8">
        <main className="py-16">
          <Prose variant="article">{props.children}</Prose>
        </main>
        <Footer />
      </div>
    </div>
  )
}
