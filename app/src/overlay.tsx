// Overlays and toasts (OVERLAYS-AND-MENUS.md): state, never routes. An overlay takes focus when it
// opens, gives it back when it closes, and Esc or a click on the dim closes it.
import { useEffect, useRef, useSyncExternalStore, type ReactNode } from 'react'
import { K } from './ds'

export function Overlay({ onClose, top, children }: { onClose: () => void; top?: boolean; children: ReactNode }) {
  const box = useRef<HTMLDivElement>(null)
  const close = useRef(onClose)
  close.current = onClose
  useEffect(() => {
    const was = document.activeElement as HTMLElement | null
    const first = box.current?.querySelector<HTMLElement>('input:not([disabled]), textarea, select, button:not([aria-label="Close"])')
    first?.focus()
    const on = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      e.preventDefault()
      e.stopPropagation()
      close.current()
    }
    addEventListener('keydown', on, true)
    return () => {
      removeEventListener('keydown', on, true)
      was?.focus?.()
    }
  }, [])
  return (
    <div className="ov" ref={box}>
      <div className="ov__dim" onClick={() => close.current()} />
      <div className={`ov__win${top ? ' ov__win--top' : ''}`} onClick={(e) => e.target === e.currentTarget && close.current()}>{children}</div>
    </div>
  )
}

// ---- toasts: one at a time, bottom centre; an action (Undo, Show) and a dismiss ----
type Toast = { id: number; text: string; action?: string; onAction?: () => void; onDone?: () => void }
let current: Toast | null = null
let timer: ReturnType<typeof setTimeout> | undefined
const subs = new Set<() => void>()
const emit = () => subs.forEach((f) => f())

function end(run: 'action' | 'done') {
  const t = current
  if (!t) return
  clearTimeout(timer)
  current = null
  emit()
  if (run === 'action') t.onAction?.()
  else t.onDone?.()
}

/** Show a toast. `onDone` runs when it goes without its action (timeout, dismiss, or a newer one). */
export function toast(text: string, more: Omit<Toast, 'id' | 'text'> = {}, ms = 10_000) {
  end('done')
  current = { id: Date.now(), text, ...more }
  emit()
  timer = setTimeout(() => end('done'), ms)
}

export function Toasts() {
  const t = useSyncExternalStore((f) => (subs.add(f), () => subs.delete(f)), () => current)
  if (!t) return null
  return (
    <div className="toasts" onMouseEnter={() => clearTimeout(timer)} onMouseLeave={() => (timer = setTimeout(() => end('done'), 4000))}>
      <K.Toast action={t.action} onAction={() => end('action')} onDismiss={() => end('done')}>{t.text}</K.Toast>
    </div>
  )
}
