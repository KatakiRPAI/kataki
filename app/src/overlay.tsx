// Overlays and toasts (OVERLAYS-AND-MENUS.md): state, never routes. An overlay takes focus when it
// opens, gives it back when it closes, and Esc or a click on the dim closes it.
import { useEffect, useRef, useSyncExternalStore, type KeyboardEvent as KeyEvent, type MouseEvent, type ReactNode } from 'react'
import type { IconName } from './ds/kataki'
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

// ---- menus: a ··· button or a right-click opens one at that spot (OVERLAYS-AND-MENUS.md › Menus) ----
export type MenuItem = { label?: string; detail?: string; icon?: IconName; danger?: boolean; disabled?: boolean; divider?: boolean; checked?: boolean; onSelect?: () => void }
type Open = { x: number; y: number; title?: string; items: MenuItem[] }
let menu: Open | null = null
const menuSubs = new Set<() => void>()
const menuEmit = () => menuSubs.forEach((f) => f())
const closeMenu = () => { menu = null; menuEmit() }

/** Open a menu under an element (a ··· button) or at the pointer (right-click, Shift F10). */
export function openMenu(at: Element | { clientX: number; clientY: number }, items: MenuItem[], title?: string) {
  if (at instanceof Element) {
    const r = at.getBoundingClientRect()
    menu = { x: r.right, y: r.bottom + 6, title, items }
  } else menu = { x: at.clientX + 260, y: at.clientY, title, items }
  menuEmit()
}
/** Props for anything with a menu: right-click and Shift F10 open it. */
export const withMenu = (items: () => MenuItem[]) => ({
  onContextMenu: (e: MouseEvent) => { e.preventDefault(); openMenu(e, items()) },
  onKeyDown: (e: KeyEvent) => { if (e.key === 'F10' && e.shiftKey) { e.preventDefault(); openMenu(e.currentTarget, items()) } },
})

export function Menus() {
  const m = useSyncExternalStore((f) => (menuSubs.add(f), () => menuSubs.delete(f)), () => menu)
  const box = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!m) return
    box.current?.querySelector<HTMLElement>('.k-menu__item:not([disabled])')?.focus()
    const away = (e: Event) => !box.current?.contains(e.target as Node) && closeMenu()
    const keys = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeMenu() }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault()
        const all = [...(box.current?.querySelectorAll<HTMLElement>('.k-menu__item:not([disabled])') ?? [])]
        const i = all.indexOf(document.activeElement as HTMLElement)
        all[(i + (e.key === 'ArrowDown' ? 1 : all.length - 1)) % all.length]?.focus()
      }
    }
    addEventListener('pointerdown', away, true)
    addEventListener('keydown', keys, true)
    addEventListener('resize', closeMenu)
    return () => { removeEventListener('pointerdown', away, true); removeEventListener('keydown', keys, true); removeEventListener('resize', closeMenu) }
  }, [m])
  if (!m) return null
  const width = 260
  const x = Math.max(8, Math.min(m.x - width, innerWidth - width - 8))
  const y = Math.min(m.y, innerHeight - 40 * m.items.length - 24)
  return (
    <div ref={box} style={{ position: 'fixed', left: x, top: Math.max(8, y), zIndex: 45 }}>
      <K.Menu title={m.title} width={width} items={m.items.map((it) => ({ ...it, onSelect: it.onSelect && (() => { closeMenu(); it.onSelect!() }) }))} />
    </div>
  )
}
