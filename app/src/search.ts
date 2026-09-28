// Search over everything (C5–C9): the engine finds names, lines and memories that contain the
// words (GET /search); this ranks them and says where each one goes.
import { api, type Item, type StorySummary } from './api'
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
  when?: string
  at: number // real time, for Newest first
  score: number
}
type Found = {
  stories: { id: number; title: string }[]
  items: { id: number; kind: Item['kind']; name: string; description: string }[]
  books: { id: number; title: string }[]
  lines: { id: number; story_id: number; story_title: string; speaker: string | null; text: string }[]
  memories: { id: number; story_id: number; story_title: string; detail: string }[]
}
type Library = { stories: StorySummary[]; items: Item[] }

let cached: { at: number; lib: Promise<Library> } | null = null
/** The stories and library, to say where a hit goes; kept 30 s. */
export function index(): Promise<Library> {
  if (cached && Date.now() - cached.at < 30_000) return cached.lib
  const lib = Promise.all([api<StorySummary[]>('/stories'), api<Item[]>('/library')]).then(([stories, items]) => ({ stories, items }))
  cached = { at: Date.now(), lib }
  return lib
}

const score = (text: string, q: string) => {
  const t = text.toLowerCase()
  return t === q ? 100 : t.startsWith(q) ? 80 : new RegExp(`\\b${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`).test(t) ? 60 : t.includes(q) ? 40 : 1
}

/** Everything that contains `query`, best first. */
export async function lookup(query: string): Promise<Hit[]> {
  const q = query.trim().toLowerCase()
  if (!q) return []
  const [lib, found] = await Promise.all([index(), api<Found>(`/search?q=${encodeURIComponent(q)}`)])
  const story = (id: number) => lib.stories.find((s) => s.id === id)
  const item = (id: number) => lib.items.find((i) => i.id === id)
  const hits: Hit[] = []
  for (const s of found.stories) hits.push({ kind: 'story', id: s.id, title: s.title, href: `/story/${s.id}`, story: story(s.id), at: utc(story(s.id)?.last_at ?? '1970-01-01 00:00:00'), score: score(s.title, q) + 5 })
  for (const f of found.items) {
    const i = item(f.id)
    if (i?.data.unlisted) continue
    const kind = f.kind === 'character' ? (i?.data.persona ? 'persona' : 'character') : f.kind
    hits.push({ kind, id: f.id, title: f.name, text: f.description || undefined, item: i, href: kind === 'character' ? `/characters/${f.id}` : kind === 'persona' ? '/you' : '/world', at: i ? utc(i.updated_at ?? i.created_at) : 0, score: score(f.name, q) + 4 })
  }
  for (const b of found.books) hits.push({ kind: 'book', id: b.id, title: b.title, href: '/world', at: 0, score: score(b.title, q) + 3 })
  for (const l of found.lines) {
    const s = story(l.story_id)
    hits.push({ kind: 'line', id: l.id, title: l.text, text: l.text, speaker: l.speaker ?? '', story: s, when: s?.date, href: `/story/${l.story_id}?line=${l.id}`, at: utc(s?.last_at ?? '1970-01-01 00:00:00'), score: score(l.text, q) / 2 })
  }
  for (const m of found.memories) {
    const s = story(m.story_id)
    hits.push({ kind: 'memory', id: m.id, title: m.detail, text: m.detail, story: s, href: `/story/${m.story_id}?backstage=0`, at: utc(s?.last_at ?? '1970-01-01 00:00:00'), score: score(m.detail, q) / 2 - 1 })
  }
  return hits.sort((a, b) => b.score - a.score)
}

/** A name one letter away from what was typed ("Did you mean"). */
export async function nearly(query: string): Promise<string | undefined> {
  const q = query.trim().toLowerCase()
  const lib = await index()
  const names = [...lib.items.map((i) => i.name), ...lib.stories.map((s) => s.title)]
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
