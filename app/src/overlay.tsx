// Overlays and toasts (OVERLAYS-AND-MENUS.md): state, never routes. An overlay takes focus when it
// opens, gives it back when it closes, and Esc or a click on the dim closes it.
import { useEffect, useRef, useSyncExternalStore, type KeyboardEvent as KeyEvent, type MouseEvent, type ReactNode } from 'react'
import type { IconName } from './ds/kataki'
import { createPortal } from 'react-dom'
import { K } from './ds'
import { t } from './strings'

/** Overlays, menus and toasts sit over the whole Sky page, rail included, in its Night/Day theme,
 *  wherever they were opened from; in a story they stay where they are. */
const onPage = (node: ReactNode) => { const host = document.querySelector('.app'); return host ? createPortal(node, host) : node }

/** `at`: a popover standing at an element (above it, left edges aligned), with no dim behind it. */
export function Overlay({ onClose, top, at, children }: { onClose: () => void; top?: boolean; at?: Element | null; children: ReactNode }) {
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
  return onPage(
    <div className="ov" ref={box}>
      <div className="ov__dim" style={at ? { background: 'transparent' } : undefined} onClick={() => close.current()} />
      {at ? <div className="ov__at" style={{ left: at.getBoundingClientRect().left, bottom: innerHeight - at.getBoundingClientRect().top + 8 }}>{children}</div>
        : <div className={`ov__win${top ? ' ov__win--top' : ''}`} onClick={(e) => e.target === e.currentTarget && close.current()}>{children}</div>}
    </div>,
  )
}

// ---- toasts: one at a time, bottom centre; an action (Undo, Show) and a dismiss ----
type Toast = { id: number; text: string; icon?: IconName; action?: string; onAction?: () => void; onDone?: () => void }
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
  return onPage(
    <div className="toasts" onMouseEnter={() => clearTimeout(timer)} onMouseLeave={() => (timer = setTimeout(() => end('done'), 4000))}>
      <K.Toast icon={t.icon} action={t.action} onAction={() => end('action')} onDismiss={() => end('done')}>{t.text}</K.Toast>
    </div>,
  )
}

// ---- menus: a ··· button or a right-click opens one at that spot (OVERLAYS-AND-MENUS.md › Menus) ----
export type MenuItem = { section?: string; label?: string; detail?: string; meta?: string; shortcut?: string[]; who?: string; src?: string; icon?: IconName; danger?: boolean; disabled?: boolean; divider?: boolean; checked?: boolean; onSelect?: () => void }
type Open = { x: number; y: number; left?: boolean; title?: string; items: MenuItem[]; footer?: string; width?: number }
let menu: Open | null = null
const menuSubs = new Set<() => void>()
const menuEmit = () => menuSubs.forEach((f) => f())
const closeMenu = () => { menu = null; menuEmit() }

/** Open a menu under an element (a ··· button) or at the pointer (right-click, Shift F10). */
export function openMenu(at: Element | { clientX: number; clientY: number }, items: MenuItem[], title?: string, more: { footer?: string; width?: number } = {}) {
  if (at instanceof Element) {
    const r = at.getBoundingClientRect()
    // a trigger on the left opens its menu from its own left edge (the persona switch); else from its right
    const left = r.left + r.width / 2 < innerWidth / 2
    menu = { x: left ? r.left : r.right, left, y: r.bottom + 6, title, items, ...more }
  } else menu = { x: at.clientX + 260, y: at.clientY, title, items, ...more }
  menuEmit()
}
/** TextMenu (M1): the desktop app's right-click in text, spelling first. The web build keeps the browser's own. */
window.kataki?.onTextMenu?.((m) => {
  const k = window.kataki!
  const items: MenuItem[] = []
  if (m.word) {
    items.push({ section: t('tm.spelling') }, ...m.suggestions.map((s): MenuItem => ({ label: s, onSelect: () => k.edit?.('replace', s) })),
      { label: t('tm.learn'), icon: 'plus', onSelect: () => k.edit?.('learn', m.word) }, { divider: true })
  }
  if (m.editable) items.push({ label: t('tm.cut'), disabled: !m.selection, onSelect: () => k.edit?.('cut') })
  items.push({ label: t('tm.copy'), disabled: !m.selection, onSelect: () => k.edit?.('copy') })
  if (m.editable) items.push({ label: t('tm.paste'), onSelect: () => k.edit?.('paste') })
  items.push({ label: t('tm.all'), onSelect: () => k.edit?.('selectAll') })
  openMenu({ clientX: m.x, clientY: m.y }, items)
})

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
  const inScene = !!document.querySelector('.scene') // a menu over a story wears the Scene's colours
  const width = m.width ?? (inScene ? 300 : 260)
  const x = Math.max(8, Math.min(m.left ? m.x : m.x - width, innerWidth - width - 8))
  const y = Math.min(m.y, innerHeight - 40 * m.items.length - 24)
  return onPage(
    <div ref={box} style={{ position: 'fixed', left: x, top: Math.max(8, y), zIndex: 45 }}>
      <K.Menu scene={inScene} title={m.title} width={width} footer={m.footer} items={m.items.map((it) => ({ ...it, onSelect: it.onSelect && (() => { closeMenu(); it.onSelect!() }) }))} />
    </div>,
  )
}
