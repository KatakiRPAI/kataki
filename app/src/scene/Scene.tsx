import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { api, stream, type Cast, type CastEntity, type ContextLog, type Message, type Story, type TurnMeta, type Version } from '../api'
import { paletteOf, SunArc } from '../art'
import { href, rise, useLibrary, useLoad, usePoll } from '../hooks'
import { ErrorLine, Icon, Menu } from '../ui'
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

  const generate = async (body: object) => {
    const ctl = new AbortController()
    controller.current = ctl
    setLive({ speaker: '', speakerId: null, text: '', thoughts: '', strained: false })
    try {
      await stream(`/stories/${id}/turn`, body, (kind, value) => {
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
    if (s.reply) return generate({ text: s.text, speaker: s.speaker, audience: s.audience, skip: s.skip })
    try {
      await api(`/stories/${id}/line`, 'POST', { text: s.text, audience: s.audience, skip: s.skip })
    } catch (e) {
      setFailed((e as Error).message)
    }
    setSettling(true)
    refreshAll()
  }

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

  return (
    <div className="k-scene ka-scene">
      <Stage story={story} people={people} />
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
          <Menu label="Story menu" className="k-scene-round k-sglass">
            <a href={href('/classic')}>Open in classic view</a>
          </Menu>
        </div>
      </header>
      <div className="k-convo-scrim" />
      <div className="k-convo ka-convo" ref={convo}>
        <Lines story={story} messages={messages} cast={cast} flash={line} onChange={refreshAll} />
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
