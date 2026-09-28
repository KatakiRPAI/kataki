// Local search over everything (C5–C9): names, lines, memories, places and plots. Built in the
// renderer from what the engine already serves.
// ponytail: reads every story's lines on first use and keeps them 30 s; an engine full-text
// endpoint (SQLite FTS) replaces this when libraries get big.
import { api, type Book, type Item, type Message, type StorySummary } from './api'
import { utc } from './hooks'

export type Hit = {
  kind: 'story' | 'character' | 'persona' | 'place' | 'scenario' | 'book' | 'line' | 'memory'
  id: number
  title: string
  text?: string // the line or memory itself
  href: string
  item?: Item
  story?: StorySummary
  speaker?: string
  when?: string // the story's own time
  at: number // real time, for Newest first
  score: number
}
type Index = { stories: StorySummary[]; items: Item[]; books: Book[]; lines: { m: Message; s: StorySummary }[]; memories: { id: number; detail: string; s: StorySummary; at: number }[] }

let cached: { at: number; index: Promise<Index> } | null = null
export function index(): Promise<Index> {
  if (cached && Date.now() - cached.at < 30_000) return cached.index
  const build = (async () => {
    const [stories, items, books] = await Promise.all([api<StorySummary[]>('/stories'), api<Item[]>('/library'), api<Book[]>('/books')])
    const lines: Index['lines'] = []
    const memories: Index['memories'] = []
    await Promise.all(stories.map(async (s) => {
      const [ms, mems] = await Promise.all([api<Message[]>(`/stories/${s.id}/messages`), api<{ id: number; detail: string; hidden: number }[]>(`/stories/${s.id}/memories`)])
      for (const m of ms) if (m.role !== 'system' && !m.hidden && m.text) lines.push({ m, s })
      for (const r of mems) if (!r.hidden) memories.push({ id: r.id, detail: r.detail, s, at: utc(s.last_at) })
    }))
    return { stories, items, books, lines, memories }
  })()
  cached = { at: Date.now(), index: build }
  return build
}
export const forget = () => { cached = null }

const score = (text: string, q: string) => {
  const t = text.toLowerCase()
  return t === q ? 100 : t.startsWith(q) ? 80 : new RegExp(`\\b${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`).test(t) ? 60 : t.includes(q) ? 40 : 0
}

export function find(ix: Index, query: string): Hit[] {
  const q = query.trim().toLowerCase()
  if (!q) return []
  const hits: Hit[] = []
  for (const s of ix.stories) { const n = score(s.title, q); if (n) hits.push({ kind: 'story', id: s.id, title: s.title, href: `/story/${s.id}`, story: s, at: utc(s.last_at), score: n + 5 }) }
  for (const i of ix.items) {
    const n = Math.max(score(i.name, q), ...(i.data.aliases ?? []).map((a) => score(a, q) - 5))
    if (!n) continue
    const kind = i.kind === 'character' ? (i.data.persona ? 'persona' : 'character') : i.kind
    hits.push({ kind, id: i.id, title: i.name, item: i, href: kind === 'character' ? `/characters/${i.id}` : kind === 'persona' ? '/you' : '/world', at: utc(i.updated_at ?? i.created_at), score: n + 4 })
  }
  for (const b of ix.books) { const n = score(b.title, q); if (n) hits.push({ kind: 'book', id: b.id, title: b.title, href: '/world', at: 0, score: n + 3 }) }
  for (const { m, s } of ix.lines) {
    const n = score(m.text, q)
    if (n) hits.push({ kind: 'line', id: m.id, title: m.text, text: m.text, speaker: m.speaker ?? '', story: s, when: m.date, href: `/story/${s.id}?line=${m.id}`, at: utc(s.last_at), score: n / 2 })
  }
  for (const r of ix.memories) {
    const n = score(r.detail, q)
    if (n) hits.push({ kind: 'memory', id: r.id, title: r.detail, text: r.detail, story: r.s, href: `/story/${r.s.id}?backstage=0`, at: r.at, score: n / 2 - 1 })
  }
  return hits.sort((a, b) => b.score - a.score)
}

/** A name one letter away from what was typed ("Did you mean"). */
export function nearly(ix: Index, query: string): string | undefined {
  const q = query.trim().toLowerCase()
  const names = [...ix.items.map((i) => i.name), ...ix.stories.map((s) => s.title)]
  return names.find((n) => { const a = n.toLowerCase(); return a !== q && distance(a, q) === 1 })
}
function distance(a: string, b: string): number {
  if (Math.abs(a.length - b.length) > 1) return 2
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)])
  for (let j = 1; j <= b.length; j++) d[0][j] = j
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1))
  return d[a.length][b.length]
}

// recently opened (C6): kept in this browser only
const RECENT = 'kataki.recent'
export type Recent = { kind: Hit['kind']; title: string; href: string }
export function remember(r: Recent) {
  try {
    const all = JSON.parse(localStorage.getItem(RECENT) ?? '[]') as Recent[]
    localStorage.setItem(RECENT, JSON.stringify([r, ...all.filter((x) => x.href !== r.href)].slice(0, 3)))
  } catch { /* nothing kept */ }
}
export function recent(): Recent[] {
  try { return JSON.parse(localStorage.getItem(RECENT) ?? '[]') } catch { return [] }
}
