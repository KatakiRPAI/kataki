import { useEffect, useId, useRef, useState, type ReactNode } from 'react'

// Thin wrappers over the design system's classes (design/components.css). Anything the design
// doesn't cover lives in app.css under ka- classes.

export function Icon({ name, size }: { name: string; size?: number }) {
  return (
    <svg className="k-icon" aria-hidden="true" style={size ? { width: size, height: size } : undefined}>
      <use href={`#i-${name}`} />
    </svg>
  )
}

export type CandyColor = 'blue' | 'pink' | 'purple' | 'green' | 'orange' | 'gold'

export function Candy({ icon, color = 'blue', size }: { icon: string; color?: CandyColor; size?: number }) {
  return (
    <span className={`k-candy k-candy--${color}`} style={size ? { width: size, height: size } : undefined}>
      <Icon name={icon} />
    </span>
  )
}

export function Chip({ pressed, onClick, icon, children }: { pressed?: boolean; onClick?: () => void; icon?: string; children: ReactNode }) {
  return (
    <button type="button" className="k-chip" aria-pressed={pressed} onClick={onClick}>
      {icon && <Icon name={icon} />}
      {children}
    </button>
  )
}

/** A segmented control: one choice among a few. */
export function Seg<T extends string>({ label, options, value, onChange }: {
  label: string
  options: [T, ReactNode][]
  value: T
  onChange: (v: T) => void
}) {
  return (
    <div className="k-seg" role="group" aria-label={label}>
      {options.map(([v, text]) => (
        <button key={v} type="button" aria-pressed={v === value} onClick={() => onChange(v)}>
          {text}
        </button>
      ))}
    </div>
  )
}

/** A Sky glass card: an optional title with a right-aligned action, then the content. */
export function Glass({ title, action, className = '', children }: { title?: ReactNode; action?: ReactNode; className?: string; children: ReactNode }) {
  return (
    <section className={`k-card ${className}`}>
      {(title || action) && (
        <div className="ka-card-head">
          {title && <h3>{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </section>
  )
}

/** A native modal dialog: Esc closes it and focus goes back where it was. */
export function Dialog({ open, onClose, title, className = '', children }: {
  open: boolean
  onClose: () => void
  title: string
  className?: string
  children: ReactNode
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const d = ref.current!
    if (open && !d.open) {
      d.showModal()
      // showModal focuses the close button; a form should start in its first field
      d.querySelector<HTMLElement>('input:not([type=hidden]), textarea, select')?.focus()
    }
    if (!open && d.open) d.close()
  }, [open])
  return (
    <dialog ref={ref} className={`ka-dialog ${className}`} aria-label={title} onClose={onClose}>
      <div className="ka-dialog__head">
        <h2>{title}</h2>
        <button type="button" className="k-btn k-btn--ghost k-btn--sm" aria-label="Close" onClick={onClose}>
          <Icon name="x" />
        </button>
      </div>
      {open && children}
    </dialog>
  )
}

/** A popover menu under its button. Clicking outside or pressing Esc closes it. */
export function Menu({ label, icon = 'dots', text, className = 'k-btn k-btn--ghost k-btn--sm', disabled, children }: {
  label: string
  icon?: string
  text?: ReactNode // shown beside the icon; the label still names the button
  className?: string
  disabled?: boolean
  children: ReactNode
}) {
  const id = useId()
  return (
    <>
      {/* the visible text is the name when there is one, so it is not hidden behind the label */}
      <button type="button" className={className} popoverTarget={id} aria-label={text ? undefined : label} disabled={disabled}>
        <Icon name={icon} />
        {text}
      </button>
      <div id={id} popover="auto" className="ka-menu" onClick={(e) => (e.target as Element).closest('button') && e.currentTarget.hidePopover()}>
        {children}
      </div>
    </>
  )
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="k-field">
      <span>{label}</span>
      {children}
    </label>
  )
}

export type TierName = 'sharp' | 'hazy' | 'forgotten'

export function Tier({ tier, backstage }: { tier: TierName; backstage?: boolean }) {
  return <span className={backstage ? `k-bs-tier k-bs-tier--${tier}` : `k-tier k-tier--${tier}`}>{tier}</span>
}

/** A placeholder for a load that is taking a moment: nothing for the first 300 ms, so a quick
 *  answer never flashes a skeleton. */
export function Waiting({ rows = 3, className = '' }: { rows?: number; className?: string }) {
  const [show, setShow] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setShow(true), 300)
    return () => clearTimeout(t)
  }, [])
  if (!show) return null
  return (
    <div className={`ka-waiting ${className}`} aria-hidden="true">
      {Array.from({ length: rows }, (_, i) => <span key={i} className="ka-waiting__row" />)}
    </div>
  )
}

/** Something is not answering: what happened, and the one thing worth trying. */
export function Trouble({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="k-card ka-trouble" role="alert">
      <h3 className="ka-row ka-row--gap">
        <Icon name="alert" size={18} />
        {title}
      </h3>
      <p className="ka-muted ka-m0">{children}</p>
      {action}
    </section>
  )
}

export function ErrorLine({ error }: { error: string }) {
  return error ? <p className="ka-error" role="alert">{error}</p> : null
}

/** Story text: paragraphs, *actions* and **emphasis**. Rendered as elements, never as HTML.
 *  `tail` goes at the end of the last paragraph (the caret while a reply is written). */
export function Prose({ text, tail }: { text: string; tail?: ReactNode }) {
  const paras = text.split(/\n{2,}/)
  return (
    <>
      {paras.map((para, i) => (
        <p key={i} className="ka-prose">
          {para.split(/(\*\*[^*]+\*\*|\*[^*\n]+\*)/).map((part, j): ReactNode => {
            if (part.startsWith('**') && part.endsWith('**') && part.length > 4) return <strong key={j}>{part.slice(2, -2)}</strong>
            if (part.startsWith('*') && part.endsWith('*') && part.length > 2) return <em key={j}>{part.slice(1, -1)}</em>
            return part
          })}
          {i === paras.length - 1 && tail}
        </p>
      ))}
    </>
  )
}

/** A Sky page header: the title on the left, search and actions on the right. */
export function SkyHeader({ title, children }: { title: ReactNode; children?: ReactNode }) {
  return (
    <header className="ka-sky-header">
      <h1 className="k-display">{title}</h1>
      <div className="ka-sky-header__actions">{children}</div>
    </header>
  )
}
