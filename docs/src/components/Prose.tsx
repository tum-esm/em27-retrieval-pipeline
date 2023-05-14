import clsx from 'clsx'

export function Prose(props: {
  children: React.ReactNode
  variant?: 'article'
  className?: string
}) {
  let className = clsx(props.className, 'prose dark:prose-invert')
  if (props.variant === 'article') {
    return <article className={className}>{props.children}</article>
  } else {
    return <div className={className}>{props.children}</div>
  }
}
