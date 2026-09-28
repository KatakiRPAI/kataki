// The command palette (C5–C7) and the persona menu (C4). Ctrl K or the top bar's search opens
// the palette on any Sky page; the persona switch (or Ctrl P) opens the menu.
import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { useNavigate } from 'react-router'
import { api, download, type Item } from '../api'
import { fullName, isPersona } from '../characters'
import { K } from '../ds'
import { face, useLibrary } from '../hooks'
import { openMenu, Overlay, type MenuItem } from '../overlay'
import { setPref, usePrefs } from '../prefs'
import { index, lookup, nearly, recent, remember, type Hit } from '../search'
import { is } from '../shortcuts'
import { t, type Key } from '../strings'
import { openFeedback } from './Feedback'

let open = false
const subs = new Set<() => void>()
export const openPalette = () => { open = true; subs.forEach((f) => f()) }
const close = () => { open = false; subs.forEach((f) => f()) }

/** C4: who you play as in new stories. */
export function personaMenu(at: Element, items: Item[], current: number | null | undefined, go: (to: string) => void) {
  const personas = items.filter(isPersona).sort((a, b) => Number(b.id === current) - Number(a.id === current))
  openMenu(at, [
    ...personas.map((p): MenuItem => { const f = face(p); return { label: fullName(p), who: f.who, src: f.src, meta: p.id === current ? t('pm.default') : undefined, checked: p.id === current, onSelect: () => setPref('persona', p.id) } }),
    { label: t('pm.director'), icon: 'eye', checked: current === null, onSelect: () => setPref('persona', null) },
    { divider: true },
    { label: t('pm.new'), icon: 'plus', onSelect: () => go('/you?new=1') },
    { label: t('pm.manage'), icon: 'user', onSelect: () => go('/you') },
  ], t('pm.title'), { footer: t('pm.foot'), width: 300 })
}

type Row = { label: string; icon?: import('../ds/kataki').IconName; who?: string; src?: string; name?: string; meta?: string; shortcut?: string[]; story?: boolean; go: () => void }

export function Palette() {
  const isOpen = useSyncExternalStore((f) => (subs.add(f), () => subs.delete(f)), () => open)
  const navigate = useNavigate()
  const { items } = useLibrary()
  const [prefs] = usePrefs()
  const [q, setQ] = useState('')
  const [hits, setHits] = useState<Hit[]>([])
  const [mean, setMean] = useState<string>()
  const [at, setAt] = useState(0)
  const seq = useRef(0)

  // Ctrl K anywhere; Ctrl P, Ctrl N, Ctrl Shift N, Ctrl , and G-sequences on Sky pages (KEYBOARD.md)
  const g = useRef(0)
  useEffect(() => {
    const on = (e: KeyboardEvent) => {
      const typing = (e.target as Element).closest?.('input, textarea, [contenteditable]')
      const inStory = location.pathname.startsWith('/story/')
      if (is(e, 'search')) { e.preventDefault(); openPalette(); return }
      if (inStory) return
      if (is(e, 'newStory')) { e.preventDefault(); navigate('/stories/new') }
      else if (is(e, 'newCharacter')) { e.preventDefault(); navigate('/characters/new') }
      else if (is(e, 'settings')) { e.preventDefault(); navigate('/settings/general') }
      else if (is(e, 'feedback')) { e.preventDefault(); openFeedback('feedback') }
      else if (is(e, 'persona')) { e.preventDefault(); const el = document.querySelector('.k-persona'); if (el) personaMenu(el, items, prefs.persona as number | null, navigate) }
      else if (e.key === '/' && !typing) { const own = document.querySelector<HTMLInputElement>('main .k-search__input:not(.k-topbar *)'); e.preventDefault(); if (own) own.focus(); else openPalette() }
      else if (!typing && !e.ctrlKey && !e.altKey && !e.metaKey) {
        const k = e.key.toLowerCase()
        if (k === 'g') { g.current = Date.now(); return }
        if (Date.now() - g.current < 1000) {
          const to = { h: '/home', s: '/stories', c: '/characters', w: '/world', y: '/you' }[k]
          if (to) { e.preventDefault(); navigate(to) }
          g.current = 0
        }
      }
    }
    addEventListener('keydown', on)
    return () => removeEventListener('keydown', on)
  }, [navigate, items, prefs.persona])

  useEffect(() => {
    if (!isOpen) return
    setQ('')
    setAt(0)
    index().catch(() => {}) // warm the library for where each hit goes
  }, [isOpen])
  useEffect(() => {
    const mine = ++seq.current
    if (!q.trim()) return setHits([])
    // a short pause, so each keystroke doesn't ask the engine
    const wait = setTimeout(() => {
      lookup(q).then((found) => { if (mine === seq.current) { setHits(found); setAt(0) } }, () => {})
      nearly(q).then((m) => { if (mine === seq.current) setMean(m) }, () => {})
    }, 120)
    return () => clearTimeout(wait)
  }, [q])
  if (!isOpen) return null

  const go = (to: string, r?: Hit) => { if (r) remember({ kind: r.kind, title: r.title, href: r.href }); close(); navigate(to) }
  const kindLabel = (k: Hit['kind']) => t(`kind.${k}` as Key)
  const groups: { title: string; rows: Row[] }[] = []
  if (!q.trim()) {
    const rec = recent()
    if (rec.length) groups.push({ title: t('pal.recent'), rows: rec.map((r) => ({ label: r.title, icon: r.kind === 'story' ? 'chat' : r.kind === 'line' ? 'quote' : 'user', meta: kindLabel(r.kind), story: r.kind === 'story', go: () => go(r.href) })) })
    groups.push({ title: t('pal.do'), rows: [
      { label: t('pal.newStory'), icon: 'plus', shortcut: ['Ctrl', 'N'], go: () => go('/stories/new') },
      { label: t('pal.newCharacter'), icon: 'user', go: () => go('/characters/new') },
      { label: t('pal.persona'), icon: 'users', shortcut: ['Ctrl', 'P'], go: () => { close(); const el = document.querySelector('.k-persona'); if (el) personaMenu(el, items, prefs.persona as number | null, navigate) } },
      { label: t('pal.import'), icon: 'download', go: () => go('/characters') },
      { label: t('pal.settings'), icon: 'settings', shortcut: ['Ctrl', ','], go: () => go('/settings/general') },
      { label: t('pal.feedback'), icon: 'help', go: () => { close(); openFeedback('feedback') } },
    ] })
    groups.push({ title: t('pal.go'), rows: [
      { label: t('pal.home'), icon: 'home', shortcut: ['G', 'then', 'H'], go: () => go('/home') },
      { label: t('pal.stories'), icon: 'chat', shortcut: ['G', 'then', 'S'], go: () => go('/stories') },
      { label: t('pal.characters'), icon: 'users', shortcut: ['G', 'then', 'C'], go: () => go('/characters') },
    ] })
  } else {
    const names = hits.filter((h) => h.kind !== 'line' && h.kind !== 'memory').slice(0, 3)
    const lines = hits.filter((h) => h.kind === 'line').slice(0, 3)
    const where = (h: Hit) => h.story?.book?.title ?? (h.item?.data.links?.book ? '' : t('pal.notFiled'))
    if (names.length) groups.push({ title: t('pal.jump'), rows: names.map((h) => ({
      label: h.title, story: h.kind === 'story', ...(h.item ? { ...face(h.item), name: h.item.name } : { icon: h.kind === 'story' ? 'chat' as const : 'book' as const }),
      meta: t('pal.meta', { kind: kindLabel(h.kind), where: where(h) || t('pal.notFiled') }), go: () => go(h.href, h),
    })) })
    if (lines.length) groups.push({ title: t('pal.lines'), rows: lines.map((h) => ({
      label: `“${(h.text ?? '').replace(/\*/g, '').slice(0, 80)}”`, icon: 'quote', meta: t('pal.lineMeta', { speaker: h.speaker ?? '', story: h.story?.title ?? '', when: h.when ?? '' }), go: () => go(h.href, h),
    })) })
    const top = names[0]
    const doRows: Row[] = []
    if (top?.kind === 'character') doRows.push({ label: t('pal.storyWith', { name: top.title }), icon: 'plus', go: () => go(`/stories/new?with=${top.id}`) })
    if (top?.kind === 'persona') doRows.push({ label: t('pal.personaTo', { name: top.title }), icon: 'users', go: () => { setPref('persona', top.id); close() } })
    if (top?.kind === 'story') doRows.push({ label: t('pal.export', { story: top.title }), icon: 'download', go: () => { close(); download(`/stories/${top.id}/export?as=markdown`) } })
    if (hits.length) {
      doRows.push({ label: t('pal.all', { n: hits.length, q: q.trim() }), icon: 'search', shortcut: ['Ctrl', 'Enter'], go: () => go(`/search?q=${encodeURIComponent(q.trim())}`) })
      groups.push({ title: t('pal.do'), rows: doRows })
    } else {
      groups.push({ title: t('pal.nothing', { q: q.trim() }), rows: [
        ...(mean ? [{ label: t('pal.mean', { name: mean }), icon: 'help' as const, go: () => setQ(mean) }] : []),
        { label: t('pal.searchLines', { q: q.trim() }), icon: 'search', go: () => go(`/search?q=${encodeURIComponent(q.trim())}`) },
        { label: t('pal.makeCharacter', { q: q.trim() }), icon: 'user', go: () => go(`/characters/new?name=${encodeURIComponent(q.trim())}`) },
        { label: t('pal.makePlace', { q: q.trim() }), icon: 'map-pin', go: () => { close(); api('/library', 'POST', { kind: 'place', name: q.trim() }).then(() => navigate('/world')) } },
      ] })
    }
  }
  const flat = groups.flatMap((gr) => gr.rows)
  const keys = (e: KeyboardEvent) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); setAt((x) => (x + (e.key === 'ArrowDown' ? 1 : flat.length - 1)) % Math.max(1, flat.length)) }
    else if (e.key === 'Tab') {
      e.preventDefault()
      const starts = groups.map((_, i) => groups.slice(0, i).reduce((n, gr) => n + gr.rows.length, 0))
      setAt(starts.find((s) => s > at) ?? 0)
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && q.trim()) { e.preventDefault(); go(`/search?q=${encodeURIComponent(q.trim())}`) }
    else if (e.key === 'Enter') { e.preventDefault(); flat[at]?.go() }
  }
  let n = -1
  return (
    <Overlay onClose={close} top>
      <K.CommandPalette query={q} onQuery={setQ} onKeyDown={keys} label={t('pal.label')} placeholder={t('pal.placeholder')}
        moveLabel={t('pal.move')} openLabel={t('pal.open')} filterLabel={t('pal.filter')}
        groups={groups.map((gr) => ({ title: gr.title, items: gr.rows.map((r) => { n++; const i = n; return { ...r, active: i === at, onSelect: r.go, onHover: () => setAt(i) } }) }))} />
    </Overlay>
  )
}
