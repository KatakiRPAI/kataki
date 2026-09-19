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
}

export type StorySummary = { id: number; title: string; created_at: string; messages: number }

export type Story = { id: number; title: string; persona_id: number | null; clock: string }

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
}

export type Cast = { scene: { id: number; place_id: number | null; title: string | null } | null; entities: CastEntity[] }

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
}

export type Entity = {
  id: number
  kind: string
  name: string
  summary: string
  hidden: number
  run_id: number | null
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
  context: { est_tokens: number; budget: number; reserve: number; sections: Section[]; recalled: number }
}
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
