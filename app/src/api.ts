// The engine's HTTP API. Every call carries the per-launch token: from the preload script in
// the desktop app, or from query params (?port=…&token=…) in a plain browser during development.
// The hash belongs to the router. The engine binds 127.0.0.1, so the token never leaves the machine.

function connection(): { baseUrl: string; token: string } {
  if (window.kataki) return window.kataki
  const query = new URLSearchParams(location.search)
  return { baseUrl: `http://127.0.0.1:${query.get('port')}`, token: query.get('token') ?? '' }
}

const { baseUrl, token } = connection()

export type Kind = 'auto' | 'reasoning' | 'standard'

export type Provider = { id: number; name: string; base_url: string; has_key: boolean }

export type RoleRow = {
  role: string
  provider_id: number | null
  model: string | null
  kind: Kind
  detected_kind: 'reasoning' | 'standard' | null
  params: Record<string, unknown>
  inherited_from: string | null
  effective_provider_id: number | null
  effective_model: string | null
  effective_kind: 'reasoning' | 'standard' | null
}

export type ItemKind = 'character' | 'place' | 'scenario'

export type Pronouns = 'she' | 'he' | 'they'

export type Palette = { bg: [string, string]; ink: string }

/** Opaque to the engine; the UI owns every key after the first three. */
export type ItemData = {
  aliases?: string[]
  first_message?: string
  example_dialogue?: string
  persona?: boolean
  favourite?: boolean
  pronouns?: Pronouns
  palette?: Palette
  portrait?: string // media name (characters, personas)
  image?: string // media name (places)
}

export type Item = {
  id: number
  kind: ItemKind
  name: string
  description: string
  private: string
  data: ItemData
  tags: string[]
  created_at: string // SQLite UTC, "YYYY-MM-DD HH:MM:SS"
  updated_at: string | null
}

/** Time passing, in words the engine's clock reads (clock.parse_skip): [phrase, label]. The label
 *  is also what a skip-only marker line says. */
export const SKIPS: [string, string][] = [
  ['a few hours later', 'A few hours later'],
  ['the next morning', 'The next morning'],
  ['a week later', 'A week later'],
]

/** An entity in a story, with the library item it came from (for its portrait and palette). */
export type Ref = { id: number; name: string; lib_item_id: number | null }

/** Where a story stands now; both the story list and a single story carry it. */
export type Standing = {
  pinned: boolean
  clock: string
  story_time: number
  minute_of_day: number
  persona: Ref | null
  place: Ref | null
  scene_title: string | null
  cast: (Ref & { present: boolean })[] // the AI characters
  last_line: { speaker: string | null; text: string } | null
  new_events: number // Activity you have not seen
  waiting: number // lines the memory reader has not read yet
}

/** A character as they stand now: the peek card, the Chats panel and the profile read this. */
export type Person = {
  id: number
  name: string
  lib_item_id: number | null
  present: boolean
  since: string
  where: string | null
  where_item_id: number | null
  state: { key: string; value: string; private: boolean }[]
  on_mind: { tier: string; text: string } | null
  about_you: {
    count: number
    sharp: number
    hazy: number
    forgotten: number
    samples: { memory_id: number; tier: string; text: string; belief: number }[]
  } | null
  remembers: number
  relationships: { rel: string; other_id: number; other: string; you: boolean; note: string | null; since: string }[]
  secret: string | null
}

/** One thing a memory read (or a time skip) wrote, for the Activity feed. */
export type ActivityEvent = {
  key: string
  kind: 'memory' | 'belief' | 'feeling' | 'time'
  story_id: number
  story: string
  message_id: number
  clock: string
  who: Ref[]
  text: string
  sub: string
  line: { speaker: string | null; text: string }
  new: boolean
}

export type StorySummary = Standing & {
  id: number
  title: string
  created_at: string
  last_at: string
  messages: number
}

export type Story = Standing & {
  id: number
  title: string
  persona_id: number | null
  minutes_per_turn: number
  epoch_offset_min: number
  start_clock: string
  roles: Record<string, unknown>
}

export type Message = {
  id: number
  parent_id: number | null
  role: 'user' | 'assistant' | 'system'
  speaker_id: number | null
  speaker: string | null
  text: string
  hidden: boolean
  edited: boolean
  skip_minutes: number
  clock: string
  scene_id: number | null
  audience?: number[] | null // who could hear it: null = everyone present, [] = a thought
  think_ms?: number | null
  swipe: [number, number]
  reasoning: string | null
  finish: string | null
  model: string | null
}

export type CastEntity = {
  id: number
  kind: string
  name: string
  summary: string
  is_ai: number
  present: boolean
  persona: boolean
  lib_item_id: number | null
}

/** An arrival or departure that changed who is there; `found` = the memory reader inferred it. */
export type PresenceChange = { id: number; message_id: number; entity_id: number; present: boolean; found: boolean; clock: string }

export type Cast = {
  scene: { id: number; place_id: number | null; title: string | null } | null
  entities: CastEntity[]
  changes: PresenceChange[]
}

export type Section = { name: string; tokens: number; cap: number; evicted: number }

/** One recalled memory as the prompt used it, with the numbers behind its score. */
export type LoggedMemory = {
  memory_id: number
  tier: 'sharp' | 'hazy'
  rendered: string // how it went in, or "dropped" when the memory section ran out of room
  tokens: number
  A: number
  A_detail: number
  B: number
  S: number
  G: number
  imp: number
  F: number
  noise: number
  superseded: boolean
  effortful: boolean | null
}

export type ContextLog = {
  id: number
  story_id: number
  message_id: number | null
  speaker_id: number | null
  budget: number
  est_tokens: number
  actual_tokens: number | null
  cached_tokens: number | null
  sections: Section[]
  memories: LoggedMemory[]
  prompt: { role: string; content: string }[] | null
  created_at: string
}

export type KnownMemory = {
  memory_id: number
  kind: string
  detail: string
  gist: string
  importance: number
  hidden: number
  pinned: number
  source: string
  told_by: string | null
  belief: number
  tier: 'sharp' | 'hazy' | 'forgotten'
  A: number
  A_detail: number
  B: number
  superseded: boolean
  story_time: number
}

export type Run = {
  id: number
  from_message_id: number
  to_message_id: number
  trigger: string
  status: string
  stale: number
  attempts: number
  role: string | null
  model: string | null
  warnings: string[]
  error: string | null
  filed: number // memories the run wrote
}

export type Entity = {
  id: number
  kind: string
  name: string
  summary: string
  hidden: number
  run_id: number | null
  lib_item_id: number | null
  aliases: string[]
  flags: { key: string; value: string | null; story_time: number; private: number }[]
}

/** A turn's stream: meta first, then thought and token text, then done or error. */
export type TurnMeta = {
  speaker: { id: number; name: string } | null
  role: string
  model: string
  thinks: boolean
  parent_id: number | null
  skip: number // minutes that passed just before this reply
  from_clock: string
  clock: string // the reply's
  strained: boolean // the speaker had to reach for a memory
  context: { est_tokens: number; budget: number; reserve: number; sections: Section[]; recalled: number }
}

/** `GET /stories/{id}/signals`: per line, who heard it and how clearly they will remember it,
 *  what it meant to someone, what a reply recalled, what a skip made them forget. */
export type Receipt = {
  id: number
  state: 'heard' | 'sharp' | 'hazy' | 'forgotten' | 'absent'
  pending?: boolean // heard, not read by memory yet
  why?: 'away' | 'whisper' // absent
}
export type Callout = {
  kind: 'memory' | 'belief' | 'feeling'
  who: number[]
  text: string
  reason: string | null
  faded: boolean
  memory_id: number | null
}
export type RecallItem = { memory_id: number; tier: 'sharp' | 'hazy'; text: string; how: string; detail: string }
export type Recall = { speaker: number; title: string; items: RecallItem[] }
export type SkipReport = {
  minutes: number
  from_clock: string
  to_clock: string
  faded: { id: number; hazy: number; gone: number }[]
  text: string
}
export type LineSignal = { summary?: string; receipts?: Receipt[]; callouts?: Callout[]; recall?: Recall; skip?: SkipReport }
export type Signals = { read_to: number; lines: Record<string, LineSignal> }

/** `GET /stories/{id}/version`: changes whenever a memory read starts, ends or goes away. */
export type Version = { v: string; waiting: number }
export type TurnDone = {
  message_id: number
  text: string
  skip_minutes: number
  clock: string
  usage: Record<string, number> | null
}
export type TurnError = { message: string; message_id?: number }

function headers(json: boolean): Record<string, string> {
  return { Authorization: `Bearer ${token}`, ...(json ? { 'Content-Type': 'application/json' } : {}) }
}

async function failure(r: Response): Promise<Error> {
  const body = await r.json().catch(() => null)
  const detail = body?.detail
  return new Error(typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : `HTTP ${r.status}`)
}

export async function api<T>(path: string, method = 'GET', json?: unknown): Promise<T> {
  const r = await fetch(baseUrl + path, {
    method,
    headers: headers(json !== undefined),
    body: json === undefined ? undefined : JSON.stringify(json),
  })
  if (!r.ok) throw await failure(r)
  return (r.status === 204 ? undefined : await r.json()) as T
}

/** Store an image with the library; the engine names it by its content. */
export async function upload(blob: Blob): Promise<{ name: string; bytes: number }> {
  const r = await fetch(baseUrl + '/media', { method: 'POST', headers: headers(false), body: blob })
  if (!r.ok) throw await failure(r)
  return r.json()
}

/** A media file as an <img> src. An image request can't carry headers, so the token goes in the query. */
export const mediaUrl = (name: string) => `${baseUrl}/media/${name}?token=${encodeURIComponent(token)}`

/** POST and read server-sent events until the stream ends. Aborting the signal stops the model;
 *  the engine keeps whatever was already written. */
export async function stream(
  path: string,
  json: unknown,
  onEvent: (kind: string, data: any) => void,
  signal: AbortSignal,
): Promise<void> {
  const r = await fetch(baseUrl + path, { method: 'POST', headers: headers(true), body: JSON.stringify(json), signal })
  if (!r.ok || !r.body) throw await failure(r)
  const reader = r.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) return
    buffer += value
    let end: number
    while ((end = buffer.indexOf('\n\n')) >= 0) {
      const block = buffer.slice(0, end)
      buffer = buffer.slice(end + 2)
      const kind = /^event: (.*)$/m.exec(block)?.[1]
      const data = /^data: (.*)$/m.exec(block)?.[1]
      if (kind && data) onEvent(kind, JSON.parse(data))
    }
  }
}
