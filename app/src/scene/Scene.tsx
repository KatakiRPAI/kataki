import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { api, stream, type Cast, type CastEntity, type ContextLog, type Message, type Story, type TurnMeta, type Version } from '../api'
import { paletteOf, SunArc } from '../art'
import { href, lastSky, rise, useAction, useLibrary, useLoad, usePoll } from '../hooks'
import { Dialog, ErrorLine, Field, Icon, Menu } from '../ui'
import Composer, { type Meter, type Send } from './Composer'
import Lines, { LiveLine, SaidLine, type Live } from './Lines'
import Stage from './Stage'

/** Who is on stage: the AI characters present, the last to speak first. */
function onStage(cast: Cast, messages: Message[]): CastEntity[] {
  const present = cast.entities.filter((e) => e.present && e.is_ai && e.kind === 'character')
  const spoke = messages.findLast((m) => m.role === 'assistant' && present.some((e) => e.id === m.speaker_id))
  const lead = present.find((e) => e.id === spoke?.speaker_id) ?? present[0]
  return lead ? [lead, ...present.filter((e) => e !== lead)] : []
}

const listed = (names: string[]) => (names.length > 1 ? `${names.slice(0, -1).join(', ')} and ${names.at(-1)}` : names[0])

function meterOf(used: number, budget: number, recalled: number): Meter {
  const memories = `${recalled} ${recalled === 1 ? 'memory' : 'memories'} recalled`
  return { used: budget ? Math.min(1, used / budget) : 0, label: `~${used.toLocaleString('en')} / ${budget.toLocaleString('en')} tokens · ${memories}` }
}

/** A story, played: the stage, the top bar, the conversation and the composer. */
export default function Scene({ id, line }: { id: number; line?: number }) {
  const { byId } = useLibrary()
  // One guarded load of everything the scene shows; every change calls it again.
  const [data, refreshAll, error] = useLoad(
    () =>
      Promise.all([
        api<Story>(`/stories/${id}`),
        api<Message[]>(`/stories/${id}/messages`),
        api<Cast>(`/stories/${id}/cast`),
      ]).then(([story, messages, cast]) => ({ story, messages, cast })),
    [id],
  )
  const [live, setLive] = useState<Live | null>(null)
  const [said, setSaid] = useState<{ text: string; audience: number[] | null } | null>(null)
  const [settling, setSettling] = useState(false) // the reply ended; keep it shown until fresh data lands
  const [failed, setFailed] = useState('')
  const [meter, setMeter] = useState<Meter>()
  const controller = useRef<AbortController | null>(null)

  useEffect(() => {
    api<ContextLog>(`/stories/${id}/context`).then(
      (c) => setMeter(meterOf(c.est_tokens, c.budget, c.memories.filter((m) => m.rendered !== 'dropped').length)),
      () => {}, // no prompt built yet
    )
  }, [id])
  useEffect(() => () => controller.current?.abort(), []) // leaving the scene stops the reply
  // before paint, so the saved reply never shows beside the live one
  useLayoutEffect(() => {
    if (!settling) return
    setLive(null)
    setSaid(null)
    setSettling(false)
  }, [data]) // eslint-disable-line react-hooks/exhaustive-deps

  // Memory reads in the background: when the version moves, what the scene shows may have too.
  // Not while a reply streams: the fresh lines would double the ones on screen.
  const version = useRef('')
  usePoll(() => {
    api<Version>(`/stories/${id}/version`).then(({ v }) => {
      if (version.current && v !== version.current) refreshAll()
      version.current = v
    }, () => {})
  }, 3000, !live)

  const generate = async (path: string, body: object, replacing?: number) => {
    const ctl = new AbortController()
    controller.current = ctl
    setLive({ speaker: '', speakerId: null, text: '', thoughts: '', strained: false, replacing })
    try {
      await stream(path, body, (kind, value) => {
        if (kind === 'meta') {
          const meta = value as TurnMeta
          setLive((l) => l && { ...l, speaker: meta.speaker?.name ?? 'The narrator', speakerId: meta.speaker?.id ?? null, strained: meta.strained, clock: meta.clock, from: meta.from_clock })
          setMeter(meterOf(meta.context.est_tokens, meta.context.budget, meta.context.recalled))
        } else if (kind === 'thought') {
          setLive((l) => l && { ...l, thoughts: l.thoughts + value, thoughtAt: l.thoughtAt ?? performance.now() })
        } else if (kind === 'token') {
          setLive((l) => l && { ...l, text: l.text + value, thinkMs: l.thinkMs ?? (l.thoughtAt === undefined ? undefined : performance.now() - l.thoughtAt) })
        } else if (kind === 'error') {
          setFailed(value.message)
        }
      }, ctl.signal)
    } catch (e) {
      if (!ctl.signal.aborted) setFailed((e as Error).message)
    } finally {
      if (controller.current === ctl) controller.current = null
      // a stopped reply is saved by the engine a moment after the connection closes
      if (ctl.signal.aborted) await new Promise((r) => setTimeout(r, 400))
      setSettling(true)
      refreshAll()
    }
  }

  const send = async (s: Send) => {
    setFailed('')
    if (s.text) setSaid({ text: s.text, audience: s.audience })
    if (s.reply) return generate(`/stories/${id}/turn`, { text: s.text, speaker: s.speaker, audience: s.audience, skip: s.skip })
    try {
      await api(`/stories/${id}/line`, 'POST', { text: s.text, audience: s.audience, skip: s.skip })
    } catch (e) {
      setFailed((e as Error).message)
    }
    setSettling(true)
    refreshAll()
  }

  // Reading mode: the controls fade until the pointer moves or focus lands on them; Esc leaves.
  const [reading, setReading] = useState(false)
  const [awake, setAwake] = useState(false)
  const sleepTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const wake = () => {
    setAwake(true)
    clearTimeout(sleepTimer.current)
    sleepTimer.current = setTimeout(() => setAwake(false), 2500)
  }
  useEffect(() => {
    if (!reading) return
    const leave = (e: KeyboardEvent) => e.key === 'Escape' && !document.querySelector('dialog[open], :popover-open') && setReading(false)
    addEventListener('keydown', leave)
    return () => removeEventListener('keydown', leave)
  }, [reading])
  useEffect(() => () => clearTimeout(sleepTimer.current), [])

  // Open at the newest line, or at the deep-linked one; follow a reply as it is written.
  const convo = useRef<HTMLDivElement>(null)
  const count = data?.messages.length ?? 0
  useEffect(() => {
    const target = line ? document.getElementById(`line-${line}`) : null
    if (target) {
      target.scrollIntoView({ block: 'center' })
    } else if (convo.current) {
      convo.current.scrollTop = convo.current.scrollHeight
    }
  }, [line, count])
  useEffect(() => {
    if (convo.current && (live || said)) convo.current.scrollTop = convo.current.scrollHeight
  }, [live, said])

  if (!data) {
    return (
      <div className="k-scene ka-scene">
        <ErrorLine error={error} />
      </div>
    )
  }
  const { story, messages, cast } = data
  const people = onStage(cast, messages)
  const away = cast.entities.filter((e) => !e.present && e.is_ai && e.kind === 'character')
  const missing = !!line && !messages.some((m) => m.id === line)
  const who = [
    people.length ? `with ${listed(people.map((e) => e.name))}` : 'alone',
    story.persona ? `as ${story.persona.name}` : 'directing',
  ].join(' · ')
  const writer = cast.entities.find((e) => e.id === live?.speakerId)
  const writerItem = writer?.lib_item_id ? byId.get(writer.lib_item_id) : undefined
  const shown = live?.replacing ? messages.filter((m) => m.id !== live.replacing) : messages
  const newest = messages.at(-1)
  const retake = () => newest && generate(`/stories/${id}/regenerate`, {}, newest.id)

  return (
    <div className={`k-scene ka-scene${reading ? ' is-reading' : ''}${awake ? ' is-awake' : ''}`} onPointerMove={reading ? wake : undefined}>
      <Stage story={story} people={people} />
      <div className="ka-veil" />
      <header className="k-topbar ka-topbar">
        <div className="ka-topbar__side">
          <button type="button" className="k-scene-round k-sglass" onClick={rise} aria-label="Float back up to the Sky">
            <Icon name="cloud" size={20} />
          </button>
          <div className="ka-topbar__title">
            <h1>{story.title}</h1>
            <span>{who}</span>
          </div>
        </div>
        <div className="k-scene-pill k-sglass">
          <SunArc minute={story.minute_of_day} />
          {story.place && <strong>{story.place.name}</strong>}
          <span className="ka-topbar__clock">{story.clock}</span>
        </div>
        <div className="ka-topbar__side ka-topbar__side--end">
          <button type="button" className="k-scene-round k-sglass" aria-label="Reading mode" aria-pressed={reading}
            onClick={() => setReading((r) => !r)}>
            <Icon name="book" size={18} />
          </button>
          <StoryMenu story={story} onChange={refreshAll} />
        </div>
      </header>
      <div className="k-convo-scrim" />
      <div className="k-convo ka-convo" ref={convo}>
        <Lines story={story} messages={shown} cast={cast} flash={line} busy={!!live} onChange={refreshAll} onRetake={retake} />
        {missing && <p className="k-sysnote">That line is no longer in this version of the story.</p>}
        {said && <SaidLine who={story.persona?.name ?? 'You'} text={said.text} audience={said.audience} />}
        {live && <LiveLine live={live} item={writerItem} ink={writer ? paletteOf(writerItem, writer.name).ink : undefined} />}
        <ErrorLine error={failed || error} />
      </div>
      <Composer
        story={story}
        people={people}
        away={away}
        live={!!live}
        writer={live && live.speakerId === null && live.speaker ? 'the narrator' : (live?.speaker ?? '')}
        meter={meter}
        onSend={send}
        onStop={() => controller.current?.abort()}
      />
    </div>
  )
}

type Dialogs = 'rename' | 'minutes' | 'delete' | null

/** The story menu: rename, minutes per turn, pin, delete (with a confirm). */
function StoryMenu({ story, onChange }: { story: Story; onChange: () => void }) {
  const [open, setOpen] = useState<Dialogs>(null)
  const [run, error, busy] = useAction()
  const close = () => setOpen(null)
  const save = (body: object) =>
    run(async () => {
      await api(`/stories/${story.id}`, 'PATCH', body)
      close()
      onChange()
    })
  const remove = () =>
    run(async () => {
      await api(`/stories/${story.id}`, 'DELETE')
      close()
      lastSky.path = '/chats' // the story is gone; float up to the list of chats
      rise()
    })
  return (
    <>
      <Menu label="Story menu" className="k-scene-round k-sglass">
        <button type="button" onClick={() => setOpen('rename')}>
          <Icon name="edit" size={16} />
          Rename…
        </button>
        <button type="button" onClick={() => setOpen('minutes')}>
          <Icon name="clock" size={16} />
          Minutes per turn…
        </button>
        <button type="button" onClick={() => save({ pinned: !story.pinned })}>
          <Icon name="pin" size={16} />
          {story.pinned ? 'Unpin story' : 'Pin story'}
        </button>
        <a href={href('/classic')}>
          <Icon name="grid" size={16} />
          Open in classic view
        </a>
        <button type="button" onClick={() => setOpen('delete')}>
          <Icon name="x" size={16} />
          Delete story…
        </button>
      </Menu>
      <Dialog open={open === 'rename'} onClose={close} title="Rename this story">
        <OneField label="Title" initial={story.title} busy={busy} error={error} onSave={(title) => save({ title })} />
      </Dialog>
      <Dialog open={open === 'minutes'} onClose={close} title="Minutes per turn">
        <p className="ka-muted">How far the story clock moves with each line. Skips come on top.</p>
        <OneField label="Minutes" initial={String(story.minutes_per_turn)} number busy={busy} error={error}
          onSave={(v) => save({ minutes_per_turn: Math.max(1, Math.round(Number(v))) })} />
      </Dialog>
      <Dialog open={open === 'delete'} onClose={close} title="Delete this story?">
        <p className="ka-muted">
          “{story.title}” and everything its characters remember of it will be gone. This can't be undone.
        </p>
        <ErrorLine error={error} />
        <div className="ka-row ka-row--end">
          <button type="button" className="k-sbtn" onClick={close}>Keep it</button>
          <button type="button" className="k-sbtn ka-sbtn--danger" disabled={busy} onClick={remove}>Delete story</button>
        </div>
      </Dialog>
    </>
  )
}

/** One field and Save: mounted fresh each time its dialog opens. */
function OneField({ label, initial, number, busy, error, onSave }: {
  label: string
  initial: string
  number?: boolean
  busy: boolean
  error: string
  onSave: (value: string) => void
}) {
  const [value, setValue] = useState(initial)
  const ok = number ? Number(value) >= 1 : !!value.trim()
  return (
    <form className="ka-stack" onSubmit={(e) => { e.preventDefault(); if (ok) onSave(value.trim()) }}>
      <Field label={label}>
        <input className="k-input" autoFocus value={value} onChange={(e) => setValue(e.target.value)}
          {...(number ? { type: 'number', min: 1, max: 1440 } : {})} />
      </Field>
      <ErrorLine error={error} />
      <div className="ka-row ka-row--end">
        <button type="submit" className="k-sbtn ka-sbtn--primary" disabled={busy || !ok}>Save</button>
      </div>
    </form>
  )
}
