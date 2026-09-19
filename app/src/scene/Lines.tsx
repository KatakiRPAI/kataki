import { useState, type CSSProperties, type ReactNode } from 'react'
import { api, type Cast, type Item, type Message, type Story } from '../api'
import { Avatar, paletteOf, pronounsOf } from '../art'
import { useAction, useLibrary } from '../hooks'
import { ErrorLine, Icon, Prose } from '../ui'

const YEAR = 365 * 1440
const COUNT = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve']
const UNITS: [number, string][] = [[YEAR, 'year'], [30 * 1440, 'month'], [7 * 1440, 'week'], [1440, 'day'], [60, 'hour'], [1, 'minute']]

/** "Six years later", "An hour later". */
function later(minutes: number): string {
  const [size, unit] = UNITS.find(([s]) => minutes >= s) ?? UNITS[UNITS.length - 1]
  const n = Math.round(minutes / size)
  const count = n === 1 ? (unit === 'hour' ? 'An' : 'A') : (COUNT[n] ?? String(n))
  return `${count} ${unit}${n === 1 ? '' : 's'} later`
}

// Clock labels are "Day 3, 14:20" or "Year 7, Day 1, 09:30".
const dayOf = (clock: string) => clock.slice(0, -7)
const timeOf = (clock: string) => clock.slice(-5)

/** Where a skip lands, at the scale of the skip: "Year 7", "Day 3" or "14:20". */
function landing(minutes: number, clock: string) {
  if (minutes >= YEAR) return clock.startsWith('Year') ? clock.split(', ')[0] : 'Year 1'
  return minutes >= 1440 ? dayOf(clock) : timeOf(clock)
}

const yearOf = (day: string) => (day.startsWith('Year') ? day.split(', ')[0] : 'Year 1')

/** A line's stamp: the time, led by the year or day when that changed since the last line. */
function stampOf(clock: string, lastDay: string) {
  const day = dayOf(clock)
  if (day === lastDay) return timeOf(clock)
  const lead = yearOf(day) !== yearOf(lastDay) ? yearOf(day) : day.split(', ').at(-1)
  return `${lead} · ${timeOf(clock)}`
}

const unmark = (text: string) => text.replace(/^—\s*|\s*—$/g, '')

function names(ids: number[], cast: Cast) {
  const all = ids.map((id) => cast.entities.find((e) => e.id === id)?.name ?? 'someone')
  return all.length > 1 ? `${all.slice(0, -1).join(', ')} and ${all.at(-1)}` : all[0]
}

/** The conversation: lines, title cards for the opening, scenes and skips, and notes on who came
 *  and went. `flash` marks a deep-linked line; `busy` while a reply is written. */
export default function Lines({ story, messages, cast, flash, busy, onChange, onRetake }: {
  story: Story
  messages: Message[]
  cast: Cast
  flash?: number
  busy: boolean
  onChange: () => void
  onRetake: () => void
}) {
  const { byId } = useLibrary()
  const [run, error] = useAction()
  const entity = (id: number | null) => cast.entities.find((e) => e.id === id)
  const itemOf = (id: number | null) => {
    const lib = entity(id)?.lib_item_id
    return lib ? byId.get(lib) : undefined
  }
  const ink = (m: Message) =>
    m.speaker_id === null ? undefined
    : m.speaker_id === story.persona?.id ? 'var(--k-speaker-aren)'
    : paletteOf(itemOf(m.speaker_id), m.speaker ?? '').ink

  const undoSkip = (m: Message, only: boolean) =>
    run(async () => {
      await api(`/messages/${m.id}`, 'PATCH', only ? { skip_minutes: 0, hidden: true } : { skip_minutes: 0 })
      onChange()
    })

  const undoPresence = (presenceId: number) =>
    run(async () => {
      await api(`/presence/${presenceId}`, 'DELETE')
      onChange()
    })

  const scenes = messages.some((m, i) => i > 0 && m.role === 'system' && m.scene_id !== messages[i - 1].scene_id)
  const opening = [scenes ? null : (story.place?.name ?? story.scene_title), story.start_clock].filter(Boolean).join(' · ')
  const out: ReactNode[] = [<Card key="opening">{opening}</Card>]
  const newest = messages.at(-1)
  let day = dayOf(story.start_clock)
  messages.forEach((m, i) => {
    const newScene = m.role === 'system' && i > 0 && m.scene_id !== messages[i - 1].scene_id
    const skipOnly = m.role === 'system' && !newScene
    if (m.skip_minutes > 0)
      out.push(
        <Card key={`skip-${m.id}`}>
          {later(m.skip_minutes)} · {landing(m.skip_minutes, m.clock)}
          <button type="button" className="ka-card-undo" onClick={() => undoSkip(m, skipOnly)}>
            <Icon name="undo" size={11} />
            Undo
          </button>
        </Card>,
      )
    if (newScene) out.push(<Card key={`scene-${m.id}`}>{unmark(m.text)} · {m.clock}</Card>)
    else if (skipOnly) {
      if (!m.hidden && m.skip_minutes === 0) out.push(<p key={m.id} className="k-sysnote">{unmark(m.text)}</p>)
    } else {
      const stamp = stampOf(m.clock, day)
      day = dayOf(m.clock)
      out.push(
        <Line
          key={m.id}
          storyId={story.id}
          m={m}
          stamp={stamp}
          ink={ink(m)}
          to={m.audience?.length ? names(m.audience, cast) : ''}
          flash={m.id === flash}
          retake={m === newest && m.role === 'assistant' && m.parent_id !== null}
          busy={busy}
          onChange={onChange}
          onRetake={onRetake}
        />,
      )
    }
    for (const c of cast.changes.filter((c) => c.message_id === m.id)) {
      const item = itemOf(c.entity_id)
      const name = entity(c.entity_id)?.name ?? 'Someone'
      const [they, hear] = { she: ['she', 'hears'], he: ['he', 'hears'], they: ['they', 'hear'] }[pronounsOf(item)]
      const They = they[0].toUpperCase() + they.slice(1)
      const by = c.found ? 'Noticed in the story' : 'Brought in by you'
      out.push(
        <div key={`change-${c.id}`} className={`k-sysnote ka-note${c.present ? '' : ' ka-note--left'}`}>
          <Avatar item={item} name={name} size={24} />
          <span className="ka-note__text">
            <span>{c.present ? `${name} joins` : `${name} left. ${They} won't hear what's said now.`}</span>
            {(c.present || c.found) && <small>{c.present ? `${by} · ${they} ${hear} everything from here on` : by}</small>}
          </span>
          <button type="button" className="ka-note__undo" disabled={busy} onClick={() => undoPresence(c.id)}>
            <Icon name="undo" size={12} />
            Undo
          </button>
        </div>,
      )
    }
  })
  return (
    <>
      {out}
      <ErrorLine error={error} />
    </>
  )
}

function Card({ children }: { children: ReactNode }) {
  return <div className="k-titlecard">{children}</div>
}

/** One line, with its tools on hover or focus: takes (the last arrow on the newest reply asks for
 *  a new one), inline Edit, and Hide (the line stays in the story but never reaches the model). */
function Line({ storyId, m, stamp, ink, to, flash, retake, busy, onChange, onRetake }: {
  storyId: number
  m: Message
  stamp: string
  ink?: string
  to: string // who a whisper was for
  flash: boolean
  retake: boolean
  busy: boolean
  onChange: () => void
  onRetake: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(m.text)
  const [run, error, working] = useAction()
  const off = busy || working
  const patch = (body: object) =>
    run(async () => {
      await api(`/messages/${m.id}`, 'PATCH', body)
      onChange()
    })
  const swipe = (step: 1 | -1) =>
    run(async () => {
      await api(`/stories/${storyId}/swipe`, 'POST', { message_id: m.id, step })
      onChange()
    })
  const save = async () => {
    if (draft.trim() && draft !== m.text) await patch({ text: draft.trim() })
    setEditing(false)
  }
  const [index, count] = m.swipe
  const fresh = retake && index === count // the next arrow asks for a new take
  return (
    <article
      id={`line-${m.id}`}
      className={`k-line ka-line${m.hidden ? ' is-hidden' : ''}${flash ? ' is-flash' : ''}`}
      style={{ '--speaker': ink } as CSSProperties}
    >
      {!editing && (
        <div className="k-line__tools">
          {(count > 1 || retake) && (
            <>
              <button type="button" aria-label="Previous take" disabled={off || count < 2} onClick={() => swipe(-1)}>
                <Icon name="left" size={15} />
              </button>
              <span className="ka-takes">{index}/{count}</span>
              <button type="button" aria-label={fresh ? 'New take' : 'Next take'} disabled={off || (count < 2 && !retake)}
                onClick={() => (fresh ? onRetake() : swipe(1))}>
                <Icon name="right" size={15} />
              </button>
              <span className="ka-tools__rule" />
            </>
          )}
          <button type="button" disabled={off} onClick={() => { setDraft(m.text); setEditing(true) }}>
            <Icon name="edit" size={14} />
            Edit
          </button>
          <button type="button" disabled={off} onClick={() => patch({ hidden: !m.hidden })}
            title={m.hidden ? undefined : 'It stays in the story but never reaches the AI'}>
            <Icon name={m.hidden ? 'eye' : 'eyeoff'} size={14} />
            {m.hidden ? 'Unhide' : 'Hide'}
          </button>
        </div>
      )}
      <div className="k-line__head">
        <span className="k-line__who">{m.speaker ?? (m.role === 'user' ? 'You' : 'Narrator')}</span>
        <span className="k-line__stamp">{stamp}</span>
        {m.edited && <span className="k-line__mark">edited</span>}
        {m.finish === 'stopped' && <span className="k-line__mark">stopped</span>}
        {m.hidden && <span className="k-line__mark">hidden</span>}
        {m.audience?.length === 0 && <span className="k-line__mark">thought</span>}
        {to && <span className="k-line__mark">whispered to {to}</span>}
      </div>
      {editing ? (
        <div className="ka-edit">
          <label className="k-sr" htmlFor={`edit-${m.id}`}>Edit the line</label>
          <textarea id={`edit-${m.id}`} rows={Math.min(10, draft.split('\n').length + 2)} value={draft} autoFocus
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') setEditing(false)
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) save()
            }} />
          <div className="ka-row ka-row--end">
            <button type="button" className="k-sbtn" onClick={() => setEditing(false)}>Cancel</button>
            <button type="button" className="k-sbtn ka-sbtn--primary" disabled={working} onClick={save}>Save</button>
          </div>
        </div>
      ) : (
        <div className="k-line__body">
          <Prose text={m.text} />
        </div>
      )}
      {m.think_ms != null && m.reasoning && <Thought ms={m.think_ms} notes={m.reasoning} />}
      <ErrorLine error={error} />
    </article>
  )
}

/** "Thought for 4 s": opens the reply's notes (inline until Backstage lands). */
function Thought({ ms, notes }: { ms: number; notes: string }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button type="button" className="ka-thought" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <Icon name="thought" size={13} />
        Thought for {Math.max(1, Math.round(ms / 1000))} s
      </button>
      {open && <p className="ka-notes">{notes}</p>}
    </>
  )
}

/** A reply being written: who, thinking or writing, and the text so far. */
export type Live = {
  speaker: string // '' until the engine says who answers
  speakerId: number | null
  text: string
  thoughts: string
  strained: boolean // they are reaching for a memory
  clock?: string // the reply's, and the one before any time passed (from meta)
  from?: string
  replacing?: number // a new take: the reply it will stand in for, hidden meanwhile
  thoughtAt?: number // performance.now() of the first thought
  thinkMs?: number // first thought to first word
}

const POSSESSIVE = { she: 'Her', he: 'His', they: 'Their' }

export function LiveLine({ live, item, ink }: { live: Live; item?: Item; ink?: string }) {
  const [open, setOpen] = useState(false)
  const name = live.speaker
  if (!live.text) {
    const doing = live.strained ? 'is trying to remember…' : 'is thinking…'
    return (
      <div className="ka-thinking" role="status">
        <div className="k-sysnote ka-note">
          <Avatar item={item} name={name || '?'} size={36} />
          <span className="ka-note__text">
            <span className="ka-thinking__doing">{name ? `${name} ${doing}` : 'Thinking…'}</span>
            {live.thoughts && (
              <small>
                {POSSESSIVE[pronounsOf(item)]} notes stay backstage ·{' '}
                <button type="button" className="ka-notes-link" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
                  {open ? 'hide them' : 'read them'}
                </button>
              </small>
            )}
          </span>
          <span className="k-thinking__dots"><i /><i /><i /></span>
        </div>
        {open && <p className="ka-notes">{live.thoughts}</p>}
      </div>
    )
  }
  return (
    <article className="k-line ka-line ka-line--live" style={{ '--speaker': ink } as CSSProperties} aria-busy="true">
      <div className="k-line__head">
        <span className="k-line__who">{live.speakerId === null ? 'Narrator' : name}</span>
        {live.clock && live.from && <span className="k-line__stamp">{stampOf(live.clock, dayOf(live.from))}</span>}
        <span className="k-line__stamp ka-writing">writing…</span>
      </div>
      <div className="k-line__body">
        <Prose text={live.text} tail={<span className="k-caret" />} />
      </div>
      {live.thinkMs != null && <Thought ms={live.thinkMs} notes={live.thoughts} />}
    </article>
  )
}

/** The user's line, shown the moment it is sent, until the engine's copy arrives. */
export function SaidLine({ who, text, audience }: { who: string; text: string; audience: number[] | null }) {
  return (
    <article className="k-line ka-line" style={{ '--speaker': 'var(--k-speaker-aren)' } as CSSProperties}>
      <div className="k-line__head">
        <span className="k-line__who">{who}</span>
        {audience?.length === 0 && <span className="k-line__mark">thought</span>}
        {!!audience?.length && <span className="k-line__mark">whispered</span>}
      </div>
      <div className="k-line__body">
        <Prose text={text} />
      </div>
    </article>
  )
}
