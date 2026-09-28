// The engine's HTTP API. Every call carries the per-launch token: from the preload script in
// the desktop app, or from query params (?port=…&token=…) in a plain browser during development.
// The hash belongs to the router. The engine binds 127.0.0.1, so the token never leaves the machine.

function connection(): { baseUrl: string; token: string } {
  if (window.kataki) return window.kataki
  // kept for the tab, since the router drops the query on its first navigation
  const query = new URLSearchParams(location.search)
  if (query.get('port')) sessionStorage.setItem('kataki', JSON.stringify({ port: query.get('port'), token: query.get('token') ?? '' }))
  // served by the engine itself (kataki serve --web): the API is this page's own origin
  if (!query.get('port') && query.get('token')) sessionStorage.setItem('kataki', JSON.stringify({ token: query.get('token') }))
  const kept = JSON.parse(sessionStorage.getItem('kataki') ?? '{}')
  return { baseUrl: kept.port ? `http://127.0.0.1:${kept.port}` : location.origin, token: kept.token ?? '' }
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
  looks?: string // what anyone can see of them; the description stays their own
  image?: string // media name (places)
  pack?: Pack // sprites made from the portrait (characters)
  history?: string[] // earlier pictures (portrait or image), newest first, to go back to
  packs?: Record<string, Pack> // the sprites made from each kept portrait
  links?: { book?: number; stories?: number[]; characters?: number[] } // places and plots, filed by hand
  unlisted?: boolean // a place made for one story and not kept in World
  tagline?: string // the card line (characters)
  lines?: string[] // how they talk: sample lines, also joined into example_dialogue
  focus?: string // where the face is in the portrait, "x% y%"
  alt?: string // the portrait described, for screen readers
  places?: number[] // places they know
  relationships?: { id: number; feels: string }[] // an authored starting point
  fade?: 'inherit' | 'fast' | 'lifelike' | 'slow' | 'never'
  model?: { provider_id: number; model: string } // which model plays them (F2); none = the default
  doubt?: boolean // they can doubt you
  edits?: number // how many times the profile was saved
  source?: 'shipped' | 'made' | 'imported'
  time?: 'dawn' | 'day' | 'dusk' | 'night' // a place's usual time
  exits?: string[] // a place's ways out
  place?: number // where a plot happens
}

/** A character profile the model wrote from your own words (`POST /library/draft`). */
export type Drafted = {
  name: string
  pronouns: Pronouns
  looks: string
  description: string
  secret: string
  example_dialogue: string
  first_message: string
  aliases: string[]
  tags: string[]
}

/** The five expressions the stage can show, in the order the profile shows them. */
export const EXPRESSIONS = ['neutral', 'smiling', 'wary', 'surprised', 'doubtful'] as const
export type Expression = (typeof EXPRESSIONS)[number]
/** Cut-out sprites and the portrait they were made from (stale once the portrait changes). */
export type Pack = { from: string; sprites: Partial<Record<Expression, string>> }

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

/** Any amount of time, "X units later", in words the engine's clock reads ("1 hour later"). */
export const UNITS = ['minutes', 'hours', 'days', 'weeks', 'months', 'years'] as const
export type Unit = (typeof UNITS)[number]
export const later = (n: number, unit: Unit) => `${n} ${n === 1 ? unit.slice(0, -1) : unit} later`

/** An entity in a story, with the library item it came from (for its portrait and palette). */
export type Ref = { id: number; name: string; lib_item_id: number | null }

/** Where a story stands now; both the story list and a single story carry it. */
export type Standing = {
  pinned: boolean
  clock: string
  date: string // in the story's own words, counted from its named moments
  story_time: number
  minute_of_day: number
  persona: Ref | null
  place: Ref | null
  scene_title: string | null
  cast: (Ref & { present: boolean })[] // the AI characters
  plot_id: number | null // the plot it started from
  places: number[] // the library places it has used
  last_line: { speaker: string | null; text: string } | null
  new_events: number // Activity you have not seen
  waiting: number // lines the memory reader has not read yet
  book: { id: number; title: string; order: number } | null // and where in it this story sits
  tags: string[]
}

/** What a file would become, read before anything is made of it (`POST /import/look`). */
export type Look = {
  kind: 'card' | 'chat' | 'lorebook' | 'kataki'
  title: string
  what: string[]
  notes: string[]
  needs_story: boolean
}

/** One story this person also plays in (`GET /library/{id}/same`). */
export type Same = {
  entity_id: number
  name: string
  story_id: number
  story: string
  is_ai: number
  remembers: number
}

/** One story looking back at another. `direction` is from the story that was asked. */
export type Link = {
  id: number
  from_story_id: number
  to_story_id: number
  kind: 'continuation' | 'shared_universe' | 'reference'
  offset_min: number
  note: string | null
  from_title: string
  to_title: string
  direction: 'back' | 'forward'
}

/** A saved shelf: a name over a set of tags, for one kind of thing. Kept in settings. */
export type Folder = { name: string; kind: 'story' | 'character'; tags: string[] }

/** A stretch of one story, from a line to a line. The last one is open: it runs to whatever the
 *  newest line is, and grows as you play. */
export type Chapter = {
  id: number
  story_id: number
  title: string
  from_message_id: number
  to_message_id: number | null
  open: boolean
  ends_at: number | null
  lines: number
  from_clock: string | null
  to_clock: string | null
}

/** A shelf of stories, in the order they read. */
export type Book = {
  id: number
  title: string
  blurb: string
  stories: number
  created_at: string
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

/** How well someone holds what they know about a persona. */
export type Knower = {
  id: number
  name: string
  lib_item_id: number | null
  count: number
  sharp: number
  hazy: number
  forgotten: number
}

/** Everywhere a friend (or a persona) has been: the profile page and "Who knows you". */
export type Profile = {
  stories: {
    id: number
    title: string
    role: 'ai' | 'persona'
    clock: string
    person: Person | null // what they are like in this story
    known_by: Knower[] | null // for a persona: who knows them, and how well
  }[]
  places: { name: string; lib_item_id: number | null; story: string; story_id: number; clock: string }[]
}

/** One thing a memory read (or a time skip) wrote, for the Activity feed. */
export type ActivityEvent = {
  key: string
  kind: 'memory' | 'belief' | 'feeling' | 'time'
  story_id: number
  story: string
  message_id: number
  clock: string
  date: string // the story's date in its own words
  at: string // when it happened in real time (SQLite UTC)
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
  start_date: string
  moments: Moment[] // what its dates count from
  roles: Record<string, unknown>
  ui: StoryUi // the app's own state for this story; the engine keeps it and never reads it
}

/** A moment a story has named ("the storm"), at a story time in minutes. */
export type Moment = { name: string; at: number }

/** A widget in the Scene: what it shows, whether it stays out, and where you put it (fractions of
 *  the window; none = its column, characters on the right and the clock bottom left). */
export type WidgetSpec = { id: string; kind: 'character' | 'clock' | 'place' | 'cast' | 'notes' | 'nearby'; entity?: number; pinned: boolean; at?: { x: number; y: number } }
export type StoryUi = { widgets?: WidgetSpec[]; dismissed?: number[]; notes?: string }

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
  date: string // the story's date in its own words: "The evening of the storm", or "Day 1"
  scene_id: number | null
  audience?: number[] | null // who could hear it: null = everyone present, [] = a thought
  think_ms?: number | null
  expression?: Expression | null // the face it was said with, for someone with sprites
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
  from_date: string // the same two in the story's own words
  date: string
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
  tone: 'memory' | 'belief' | 'feeling' | 'warm' | 'mood' // the colour of the reaction
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
  expression: Expression | null
  text: string
  skip_minutes: number
  clock: string
  date: string
  usage: Record<string, number> | null
}
export type TurnError = { message: string; message_id?: number }

function headers(json: boolean): Record<string, string> {
  return { Authorization: `Bearer ${token}`, ...(json ? { 'Content-Type': 'application/json' } : {}) }
}

/** A picture that failed says why, whether the provider refused it, and who else could try. */
export type PictureFailure = { message: string; refused?: boolean; alt?: string | null }

async function failure(r: Response): Promise<Error & { detail?: unknown }> {
  const body = await r.json().catch(() => null)
  const detail = body?.detail
  // N2: the library can't be written (disk full or read-only); the whole window says so
  if (r.status === 507) dispatchEvent(new CustomEvent('kataki:disk', { detail: detail?.code ?? 'DISK_FULL' }))
  const said = typeof detail === 'string' ? detail : detail?.message ?? (detail ? JSON.stringify(detail) : `HTTP ${r.status}`)
  return Object.assign(new Error(said), { detail })
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

/** Ask the engine for a file and hand it to the browser to save under the name the engine chose.
 *  A download can't carry a header, so it is fetched with one and saved from memory — fine for a
 *  story or one library on this machine.
 *  ponytail: stream to disk through the main process if a library ever outgrows memory. */
export async function download(path: string): Promise<string> {
  const r = await fetch(baseUrl + path, { headers: headers(false) })
  if (!r.ok) throw await failure(r)
  const said = r.headers.get('Content-Disposition') ?? ''
  const name = /filename="([^"]+)"/.exec(said)?.[1] || 'kataki'
  const url = URL.createObjectURL(await r.blob())
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 30_000) // after the save has taken it
  return name
}

/** POST a file as its own bytes: the engine reads the file, not a JSON envelope round it. */
export async function sendFile<T>(path: string, blob: Blob): Promise<T> {
  const r = await fetch(baseUrl + path, { method: 'POST', headers: headers(false), body: blob })
  if (!r.ok) throw await failure(r)
  return r.json()
}

/** Store an image with the library; the engine names it by its content. */
export const upload = (blob: Blob) => sendFile<{ name: string; bytes: number }>('/media', blob)

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

/** `GET /messages/{id}/mind`: how one reply came about, only from what the engine recorded.
 *  `gold`: it reached the prompt the reply was written from. */
export type MindNode = {
  id: string
  column: 'in' | 'sense' | 'inside' | 'decide'
  kind: 'heard' | 'saw' | 'place' | 'time' | 'attention' | 'cue' | 'recall' | 'belief' | 'feeling' | 'persona' | 'expression'
  title: string
  text: string
  weight: number | null
  gold: boolean
  detail: Record<string, unknown> | null
}
export type Mind = {
  message_id: number
  speaker: { id: number | null; name: string }
  clock: string
  date: string
  nodes: MindNode[]
  links: { from: string; to: string; gold: boolean }[]
  more: { recall?: number; feeling?: number }
  spoke: { text: string; model: string | null; tokens: number | null; ms: number | null; timings: Record<string, number> }
}

/** `GET /stories/{id}/feelings?who=`: how one character has come to feel about you, counted at
 *  each memory read (relationships carry words, not numbers, so these are counts). */
export type Feelings = {
  who: number
  about: number
  points: { run: number; story_time: number; date: string; warmth: number; trust: number; doubt: number }[]
  skips: { story_time: number; label: string }[]
  counted: true
}
