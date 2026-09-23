import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { api, download, stream, type Cast, type CastEntity, type Chapter, type ContextLog, type Message, type Signals, type Story, type TurnDone, type TurnMeta, type Version } from '../api'
import { paletteOf } from '../art'
import { href, lastSky, rise, useAction, useLibrary, useLoad, usePoll, type Moving } from '../hooks'
import { Dialog, ErrorLine, Field, Icon, Menu, Trouble, Waiting } from '../ui'
import Composer, { PassTime, remembered, type Meter, type Send, type Skip, type Speaker } from './Composer'
import Lines, { LiveLine, SaidLine, TimeSkip, type Live } from './Lines'
import { Nearby, NewScene, type SceneBody } from './Nearby'
import Backstage from './Backstage'
import Peek from './Peek'
import { CharacterWidget, ClockWidget, Place } from './Widgets'

/** Who is here: the AI characters present, whoever just arrived or else the last to speak
 *  first. */
function onStage(cast: Cast, messages: Message[], arriving?: number): CastEntity[] {
  const present = cast.entities.filter((e) => e.present && e.is_ai && e.kind === 'character')
  const spoke = messages.findLast((m) => m.role === 'assistant' && present.some((e) => e.id === m.speaker_id))
  const lead = present.find((e) => e.id === arriving) ?? present.find((e) => e.id === spoke?.speaker_id) ?? present[0]
  return lead ? [lead, ...present.filter((e) => e !== lead)] : []
}

const listed = (names: string[]) => (names.length > 1 ? `${names.slice(0, -1).join(', ')} and ${names.at(-1)}` : names[0])

function meterOf(used: number, budget: number, recalled: number): Meter {
  const memories = `${recalled} ${recalled === 1 ? 'memory' : 'memories'} recalled`
  return { used: budget ? Math.min(1, used / budget) : 0, label: `~${used.toLocaleString('en')} / ${budget.toLocaleString('en')} tokens · ${memories}` }
}

/** A story, played: the place behind, the chat full height in the middle with the composer docked
 *  in it, the corners, and widgets either side (characters on the right, the clock bottom left). */
export default function Scene({ id, line, backstage: opened }: { id: number; line?: number; backstage?: number }) {
  const { byId } = useLibrary()
  // One guarded load of everything the scene shows; every change calls it again.
  // The version this data was loaded at: the poll compares with it, so a memory read that lands
  // any time after a load (even before the first tick) refreshes the scene.
  const version = useRef('')
  const [data, refreshAll, error] = useLoad(
    () =>
      Promise.all([
        api<Version>(`/stories/${id}/version`),
        api<Story>(`/stories/${id}`),
        api<Message[]>(`/stories/${id}/messages`),
        api<Cast>(`/stories/${id}/cast`),
        api<Signals>(`/stories/${id}/signals`),
        api<Chapter[]>(`/stories/${id}/chapters`),
      ]).then(([at, story, messages, cast, signals, chapters]) => {
        version.current = `${at.v}|${at.waiting}`
        return { story, messages, cast, signals, chapters }
      }),
    [id],
  )
  // Playing a story is looking at it: what the reader wrote is no longer new, here or in the Sky.
  // Again on the way out, for the reads that landed while you played.
  useEffect(() => {
    const seen = () => api(`/stories/${id}/seen`, 'POST').catch(() => {})
    seen()
    return () => {
      seen()
    }
  }, [id])
  const [live, setLive] = useState<Live | null>(null)
  const [said, setSaid] = useState<{ text: string; audience: number[] | null; narrate: boolean; who?: string } | null>(null)
  const [settling, setSettling] = useState(false) // the reply ended; keep it shown until fresh data lands
  const [failed, setFailed] = useState('')
  const [act, actError, acting] = useAction()
  const [arriving, setArriving] = useState<number>()
  const [cutting, setCutting] = useState(false)
  const [newScene, setNewScene] = useState(false)
  const arrivalTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  useEffect(() => () => clearTimeout(arrivalTimer.current), [])

  // In and out of the scene: a friend from the library joins the story; someone away comes back;
  // someone here goes. Whoever arrives steps in with a name card for 3 s.
  const move = (m: Moving) =>
    act(async () => {
      let arrived: number | undefined = m.kind === 'away' ? m.id : undefined
      if (m.kind === 'friend') {
        const after = await api<Cast>(`/stories/${id}/cast`, 'POST', { library_id: m.id })
        arrived = after.entities.find((e) => e.lib_item_id === m.id)?.id
      } else {
        await api(`/stories/${id}/presence`, 'POST', { entity_id: m.id, present: m.kind === 'away' })
      }
      refreshAll()
      if (arrived) {
        setArriving(arrived)
        clearTimeout(arrivalTimer.current)
        arrivalTimer.current = setTimeout(() => setArriving(undefined), 3000)
      }
    })
  // A new scene: cut through black, the story changing under it.
  const cut = async (body: SceneBody) => {
    await api(`/stories/${id}/scene`, 'POST', body)
    setCutting(true)
    setTimeout(refreshAll, 300)
    setTimeout(() => setCutting(false), 600)
  }
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
  const [tick, setTick] = useState(0) // Backstage reloads when this moves
  usePoll(() => {
    api<Version>(`/stories/${id}/version`).then(({ v, waiting }) => {
      const now = `${v}|${waiting}` // lines waiting to be read count too (Backstage shows them)
      if (version.current && now !== version.current) {
        version.current = now // the refresh below will confirm it
        refreshAll()
        setTick((t) => t + 1)
      }
    }, () => {})
  }, 3000, !live)
  // #/story/4/backstage/29 opens Backstage on that character (the profile's "See her memories")
  const [backstage, setBackstage] = useState(opened !== undefined)
  const [picked, setPicked] = useState<Speaker>(null) // who answers next
  const [skip, setSkip] = useState<Skip | null>(null) // time to pass before the next line
  const [advanced, setAdvanced] = useState(remembered) // the composer's toggle; the chat follows it
  const [peek, setPeek] = useState<{ id: number; at: { x: number; y: number } } | null>(null)
  const [focus, setFocus] = useState<number | undefined>(opened) // the character Backstage opens on

  // Time passing: the overlay holds for at least 1.8 s, fades out, and then the clock rolls.
  const [skipping, setSkipping] = useState<{ minutes: number; from: string; to: string; line: number; report?: string; leaving?: boolean } | null>(null)
  const [rolling, setRolling] = useState(false)
  const skipTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const rollTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const played = useRef(new Set<number>()) // a line's skip is a moment, played once
  const onScreen = useRef<{ line: number; leaving: boolean } | null>(null)
  const beforeReply = useRef('') // the clock the reply starts from, for a skip in its own words
  useEffect(() => () => {
    clearTimeout(skipTimer.current)
    clearTimeout(rollTimer.current)
  }, [])
  const closeSkip = () => {
    clearTimeout(skipTimer.current)
    if (onScreen.current) onScreen.current.leaving = true
    setSkipping((was) => (was?.leaving ? was : was && { ...was, leaving: true }))
    skipTimer.current = setTimeout(() => {
      onScreen.current = null
      setSkipping(null)
      setRolling(true) // the clock rolls as the mist lifts
      rollTimer.current = setTimeout(() => setRolling(false), 800)
    }, 400)
  }
  const holdSkip = (ms: number) => {
    clearTimeout(skipTimer.current)
    skipTimer.current = setTimeout(closeSkip, ms)
  }
  const playSkip = (minutes: number, from: string, to: string, line: number) => {
    if (played.current.has(line)) return // a retake of the reply after it is not a new skip
    played.current.add(line)
    onScreen.current = { line, leaving: false }
    setSkipping({ minutes, from, to, line })
    holdSkip(2600)
    // the engine writes what it cost each of them; hold a moment longer once it arrives
    api<Signals>(`/stories/${id}/signals`).then((s) => {
      const report = s.lines[line]?.skip?.text
      if (!report || onScreen.current?.line !== line || onScreen.current.leaving) return
      setSkipping((was) => (was && was.line === line ? { ...was, report } : was))
      holdSkip(1600) // long enough to read what it cost them
    }, () => {})
  }
  const undoSkip = () =>
    act(async () => {
      const line = skipping?.line
      if (!line) return
      closeSkip()
      // the line may have been written moments ago, before this scene's data was refreshed
      const known = data?.messages.find((m) => m.id === line)
      const message = known ?? (await api<Message[]>(`/stories/${id}/messages`)).find((m) => m.id === line)
      const only = message?.role === 'system' // a marker with nothing but the skip goes too
      await api(`/messages/${line}`, 'PATCH', only ? { skip_minutes: 0, hidden: true } : { skip_minutes: 0 })
      refreshAll()
    })

  const generate = async (path: string, body: object, replacing?: number, rewriting?: number) => {
    const was = { clock: data?.story.clock ?? '' } // the clock before this turn, for a skip the reply itself takes
    const ctl = new AbortController()
    controller.current = ctl
    setLive({ speaker: '', speakerId: null, text: '', thoughts: '', strained: false, replacing, rewriting })
    try {
      await stream(path, body, (kind, value) => {
        if (kind === 'meta') {
          const meta = value as TurnMeta
          setLive((l) => l && { ...l, speaker: meta.speaker?.name ?? 'The narrator', speakerId: meta.speaker?.id ?? null, strained: meta.strained, clock: meta.clock, from: meta.from_clock })
          setMeter(meterOf(meta.context.est_tokens, meta.context.budget, meta.context.recalled))
          beforeReply.current = meta.clock
          if (!replacing && !rewriting && meta.skip >= 1440 && meta.parent_id) {
            playSkip(meta.skip, meta.from_clock, meta.clock, meta.parent_id)
          }
        } else if (kind === 'thought') {
          setLive((l) => l && { ...l, thoughts: l.thoughts + value, thoughtAt: l.thoughtAt ?? performance.now() })
        } else if (kind === 'token') {
          setLive((l) => l && { ...l, text: l.text + value, thinkMs: l.thinkMs ?? (l.thoughtAt === undefined ? undefined : performance.now() - l.thoughtAt) })
        } else if (kind === 'done') {
          const done = value as TurnDone
          // the reply's own narration moved the clock: it starts from where the reply began
          if (done.skip_minutes >= 1440) playSkip(done.skip_minutes, beforeReply.current || was.clock, done.clock, done.message_id)
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
    if (s.text) setSaid({ text: s.text, audience: s.audience, narrate: s.narrate })
    if (s.reply) return generate(`/stories/${id}/turn`, { text: s.text, speaker: s.speaker, audience: s.audience, skip: s.skip, narrate: s.narrate })
    const before = data?.story.clock ?? ''
    try {
      const after = await api<Message[]>(`/stories/${id}/line`, 'POST', { text: s.text, audience: s.audience, skip: s.skip, narrate: s.narrate })
      const last = after.at(-1)
      if (last && last.skip_minutes >= 1440) playSkip(last.skip_minutes, before, last.clock, last.id)
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
    const leave = (e: KeyboardEvent) =>
      e.key === 'Escape' && !skipping && !document.querySelector('dialog[open], :popover-open') && setReading(false)
    addEventListener('keydown', leave)
    return () => removeEventListener('keydown', leave)
  }, [reading, skipping])
  useEffect(() => () => clearTimeout(sleepTimer.current), [])

  // Open at the newest line, or at the deep-linked one; follow a reply as it is written.
  const convo = useRef<HTMLDivElement>(null)
  const count = data?.messages.length ?? 0
  const marked = data?.chapters.length ?? 0 // a chapter card is height the conversation gained
  const landed = useRef<number>(undefined) // the deep-linked line we have already come to rest on
  useEffect(() => {
    if (line && landed.current === line) return // a line you send after is not a reason to go back
    const target = line ? document.getElementById(`line-${line}`) : null
    if (!target) {
      if (convo.current) convo.current.scrollTop = convo.current.scrollHeight
      return
    }
    landed.current = line
    // Arriving through the dive, the lines are still settling (fonts, portraits, receipts), and
    // the one we came for drifts away under them. Hold it in the middle until they stop moving,
    // or until you scroll for yourself.
    let frame = 0
    let tall = -1
    let raf = 0
    const hold = () => {
      const now = convo.current?.scrollHeight ?? 0
      if (now !== tall) {
        tall = now
        target.scrollIntoView({ block: 'center' })
      }
      if (++frame < 90) raf = requestAnimationFrame(hold)
    }
    raf = requestAnimationFrame(hold)
    const stop = () => cancelAnimationFrame(raf)
    addEventListener('wheel', stop, { passive: true })
    addEventListener('pointerdown', stop)
    return () => {
      stop()
      removeEventListener('wheel', stop)
      removeEventListener('pointerdown', stop)
    }
  }, [line, count, marked, backstage])
  useEffect(() => {
    if (convo.current && (live || said)) convo.current.scrollTop = convo.current.scrollHeight
  }, [live, said])

  if (!data) {
    return (
      <div className="k-scene ka-scene ka-scene--waiting">
        {error ? <Trouble title="This story won't open">{error}</Trouble> : <Waiting rows={4} />}
      </div>
    )
  }
  const { story, messages, cast, signals, chapters } = data
  const item = (e: { lib_item_id: number | null }) => (e.lib_item_id ? byId.get(e.lib_item_id) : undefined)
  const people = onStage(cast, messages, arriving)
  // later lines win, so each speaker keeps the face of the last line that had one
  const faces = new Map(messages.flatMap((m) => (m.speaker_id && m.expression ? [[m.speaker_id, m.expression] as const] : [])))
  const away = cast.entities.filter((e) => !e.present && e.is_ai && e.kind === 'character')
  const missing = !!line && !messages.some((m) => m.id === line)
  const peeking = peek && cast.entities.find((e) => e.id === peek.id)
  const who = [
    people.length ? `with ${listed(people.map((e) => e.name))}` : 'alone',
    story.persona ? `as ${story.persona.name}` : 'directing',
  ].join(' · ')
  const writer = cast.entities.find((e) => e.id === live?.speakerId)
  const writerItem = writer && item(writer)
  const cutAt = live?.rewriting ? messages.findIndex((m) => m.id === live.rewriting) : -1
  const shown = live?.replacing ? messages.filter((m) => m.id !== live.replacing) : cutAt >= 0 ? messages.slice(0, cutAt) : messages
  // an edited line, played on from: the new take streams in after it; the old one is a swipe away
  const rewrite = (m: Message, text: string) => {
    setFailed('')
    setSaid({ text, audience: m.audience ?? null, narrate: false, who: m.speaker ?? (story.persona ? 'Narrator' : 'You') })
    return generate(`/messages/${m.id}/rewrite`, { text }, undefined, m.id)
  }
  const newest = messages.at(-1)
  // Which chapter you are in: the one whose stretch the newest line falls in, and whose own
  // opening is on the take this story is reading — otherwise the bar would name a chapter the
  // conversation never shows. Between a chapter closed early and the next one there is none, and
  // the bar says nothing rather than lie.
  const here =
    newest &&
    chapters.findLast(
      (c) =>
        c.from_message_id <= newest.id &&
        (c.ends_at ?? 0) >= newest.id &&
        messages.some((m) => m.id === c.from_message_id),
    )
  const retake = () => newest && generate(`/stories/${id}/regenerate`, {}, newest.id)
  // "no model is set", "could not reach ...": something to go and fix, not a line to shrug at
  const offline = /model|reach|connect|provider/i.test(failed)

  return (
    <div className={`k-scene ka-scene${reading && !backstage ? ' is-reading' : ''}${awake ? ' is-awake' : ''}${backstage ? ' is-backstage' : ''}${skipping ? ' is-skipping' : ''}`}
      onPointerMove={reading ? wake : undefined}>
      {backstage && <Backstage story={story} cast={cast} tick={tick} focus={focus} onChange={refreshAll} />}
      <Place item={story.place ? item(story.place) : undefined} minute={story.minute_of_day} />
      <div className="k-corner k-corner--left ka-corner">
        <button type="button" className="k-scene-round k-sglass" onClick={rise} aria-label="Float back up to the Sky">
          <Icon name="cloud" size={20} />
        </button>
        <div className="ka-corner__title">
          <h1>{story.title}</h1>
          <span>
            {here && (
              <>
                <strong className="ka-corner__chapter">{here.title}</strong>
                {' · '}
              </>
            )}
            {who}
          </span>
        </div>
      </div>
      <div className="k-corner k-corner--right ka-corner">
        <button type="button" role="switch" aria-checked={backstage} className="k-scene-pill k-sglass ka-bs-toggle"
          onClick={() => setBackstage((b) => !b)}>
          <Icon name="layers" size={16} />
          Backstage
          <span className={`k-switch${backstage ? ' is-on' : ''}`} aria-hidden="true" />
        </button>
        <StoryMenu story={story} chapters={chapters} messages={messages} at={newest?.id} reading={reading}
          onReading={backstage ? undefined : () => setReading((r) => !r)} onChange={refreshAll}
          onNewScene={() => setNewScene(true)} />
      </div>
      <section className="k-chat ka-chat" aria-label="The story">
        <div className="k-chat__scroll ka-chat__scroll" ref={convo}>
          <div className="k-chat__inner ka-chat__inner">
            <Lines story={story} messages={shown} cast={cast} signals={signals} chapters={chapters} flash={line} advanced={advanced}
              busy={!!live} onChange={refreshAll} onRetake={retake} onRewrite={rewrite} />
            {missing && <p className="k-sysnote">That line is no longer in this version of the story.</p>}
            {said && (
              <SaidLine who={said.who ?? (said.narrate ? 'Narrator' : (story.persona?.name ?? 'You'))} text={said.text} audience={said.audience} advanced={advanced}
                hearers={said.audience === null ? people : people.filter((e) => said.audience!.includes(e.id))} />
            )}
            {live && <LiveLine live={live} item={writerItem} ink={writer ? paletteOf(writerItem, writer.name).ink : undefined} />}
            {offline ? (
              <Trouble
                title="The model isn't answering"
                action={<a className="k-btn k-btn--sm" href={href('/settings')}><Icon name="server" size={15} />Check Models</a>}
              >
                {failed}
              </Trouble>
            ) : (
              <ErrorLine error={failed || actError || error} />
            )}
          </div>
        </div>
        <Composer
          story={story}
          people={people}
          away={away}
          live={!!live}
          picked={picked}
          onPick={setPicked}
          advanced={advanced}
          onAdvanced={setAdvanced}
          skip={skip}
          onSkip={setSkip}
          writer={live && live.speakerId === null && live.speaker ? 'the narrator' : (live?.speaker ?? '')}
          meter={meter}
          onSend={send}
          onStop={() => controller.current?.abort()}
        />
      </section>
      <aside className="ka-widgets ka-widgets--right" aria-label="Who is here">
        {people.map((e) => (
          <CharacterWidget key={e.id} entity={e} item={item(e)} face={faces.get(e.id)} joined={e.id === arriving}
            state={live?.speakerId === e.id ? (live.text ? 'writing' : 'thinking') : undefined}
            onPeek={(at) => setPeek({ id: e.id, at })} />
        ))}
        <Nearby cast={cast} busy={acting || !!live} onMove={move} />
      </aside>
      <aside className="ka-widgets ka-widgets--left" aria-label="The story clock">
        <ClockWidget story={story} chapter={here?.title} rolling={rolling}
          passTime={<PassTime disabled={!!live} onPick={setSkip} className="ka-clock__pass" />} />
      </aside>
      {peeking && (
        <Peek
          key={peeking.id}
          story={id}
          entity={peeking}
          at={peek!.at}
          tick={tick}
          busy={acting || !!live}
          onClose={() => setPeek(null)}
          onAnswer={() => {
            setPicked(peeking.id)
            setPeek(null)
          }}
          onMove={() => {
            move({ kind: peeking.present ? 'here' : 'away', id: peeking.id })
            setPeek(null)
          }}
          onBackstage={() => {
            setFocus(peeking.id)
            setBackstage(true)
            setPeek(null)
          }}
        />
      )}
      <NewScene open={newScene} story={story} cast={cast} onClose={() => setNewScene(false)} onCut={cut} />
      {cutting && <div className="ka-cut" aria-hidden="true" />}
      {skipping && (
        <TimeSkip
          title={story.title}
          minutes={skipping.minutes}
          from={skipping.from}
          to={skipping.to}
          report={skipping.report}
          leaving={!!skipping.leaving}
          onUndo={undoSkip}
          onHold={() => clearTimeout(skipTimer.current)}
          onClose={closeSkip}
        />
      )}
    </div>
  )
}

type Dialogs = 'rename' | 'minutes' | 'delete' | 'chapter' | 'chapters' | 'export' | null

/** The story menu: reading mode, chapters, rename, minutes per turn, pin, delete (with a confirm). */
function StoryMenu({ story, chapters, messages, at, reading, onReading, onChange, onNewScene }: {
  story: Story
  chapters: Chapter[]
  messages: Message[] // the take this story is reading: what "go to it" can actually come to
  at?: number // the newest line: where a chapter started "here" begins
  reading: boolean
  onReading?: () => void // none while Backstage is open
  onChange: () => void
  onNewScene: () => void
}) {
  const [open, setOpen] = useState<Dialogs>(null)
  const [run, error, busy, forget] = useAction()
  // what went wrong in the dialog you just closed is not news about the next one
  const close = () => {
    setOpen(null)
    forget()
  }
  const save = (body: object) =>
    run(async () => {
      await api(`/stories/${story.id}`, 'PATCH', body)
      close()
      onChange()
    })
  /** The first line of this chapter that is on screen — a marker carries an anchor too. */
  const opensAt = (c: Chapter) =>
    messages.find((m) => m.id >= c.from_message_id && m.id <= (c.ends_at ?? m.id))
  // Coming to a chapter is scrolling, not routing: the hash may already be that line, and
  // assigning the same hash again changes nothing.
  const goTo = (c: Chapter) => {
    close()
    const line = opensAt(c)
    if (line) document.getElementById(`line-${line.id}`)?.scrollIntoView({ block: 'center' })
  }
  // Chapters are part of what the scene loads, so a change to one just asks it to load again.
  const chapter = (fn: () => Promise<unknown>, thenClose = false) =>
    run(async () => {
      await fn()
      if (thenClose) close()
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
        <button type="button" disabled={!onReading} onClick={onReading}>
          <Icon name="book" size={16} />
          {reading ? 'Leave reading mode' : 'Reading mode'}
        </button>
        <button type="button" onClick={onNewScene}>
          <Icon name="film" size={16} />
          New scene…
        </button>
        <button type="button" disabled={!at || chapters.some((c) => c.from_message_id === at)}
          onClick={() => setOpen('chapter')}>
          <Icon name="quill" size={16} />
          Start a chapter here…
        </button>
        <button type="button" disabled={!chapters.length} onClick={() => setOpen('chapters')}>
          <Icon name="book" size={16} />
          Chapters
        </button>
        <button type="button" onClick={() => setOpen('export')}>
          <Icon name="download" size={16} />
          Take it out…
        </button>
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
      <Dialog open={open === 'chapter'} onClose={close} title="Start a chapter here">
        <p className="ka-muted">
          It begins at the newest line and runs on as you play. Whatever was running ends just before it.
        </p>
        <OneField label="Chapter title" initial="" busy={busy} error={error}
          onSave={(title) =>
            chapter(async () => { await api(`/stories/${story.id}/chapters`, 'POST', { title, from_message_id: at }) }, true)
          } />
      </Dialog>
      <Dialog open={open === 'chapters'} onClose={close} title={`Chapters of “${story.title}”`}>
        <ol className="ka-chapters">
          {chapters.map((c, i) => (
            <li key={c.id} className="ka-chapters__row">
              <span className="ka-chapters__n" aria-hidden="true">{i + 1}</span>
              <form
                className="ka-chapters__body"
                onSubmit={(e) => {
                  e.preventDefault()
                  const title = String(new FormData(e.currentTarget).get('title') ?? '').trim()
                  if (title && title !== c.title) chapter(async () => { await api(`/chapters/${c.id}`, 'PATCH', { title }) })
                }}
              >
                <input name="title" className="k-input" defaultValue={c.title} maxLength={200}
                  aria-label={`Title of chapter ${i + 1}`} />
                <span className="ka-muted ka-small">
                  {[c.from_clock, `${c.lines} ${c.lines === 1 ? 'line' : 'lines'}`, c.open ? 'still running' : c.to_clock]
                    .filter(Boolean)
                    .join(' · ')}
                </span>
                <span className="ka-row">
                  <button type="submit" className="k-sbtn" disabled={busy}>Save the title</button>
                  <button type="button" className="k-sbtn" disabled={busy || !opensAt(c)}
                    onClick={() => goTo(c)}>
                    Go to it
                  </button>
                  <button type="button" className="k-sbtn ka-sbtn--danger" disabled={busy}
                    onClick={() => chapter(async () => { await api(`/chapters/${c.id}`, 'DELETE') })}>
                    Delete
                  </button>
                </span>
              </form>
            </li>
          ))}
        </ol>
        <p className="ka-muted ka-small">
          {chapters.length
            ? 'Deleting a chapter gives its lines back to the one before it. The story keeps every line either way.'
            : 'No chapters. The whole story is one stretch.'}
        </p>
        <ErrorLine error={error} />
      </Dialog>
      <Dialog open={open === 'export'} onClose={close} title={`Take “${story.title}” out`}>
        <p className="ka-muted">
          A copy, for you to keep or read anywhere. The story stays here either way.
        </p>
        <div className="ka-stack">
          <button type="button" className="k-sbtn ka-out" disabled={busy}
            onClick={() => run(async () => { await download(`/stories/${story.id}/export?as=markdown`); close() })}>
            <Icon name="quote" size={16} />
            <span className="ka-out__text">
              <strong>As a page to read</strong>
              <small>Markdown: its title, its chapters, and every line under the name that said it.</small>
            </span>
          </button>
          <button type="button" className="k-sbtn ka-out" disabled={busy}
            onClick={() => run(async () => { await download(`/stories/${story.id}/export?as=jsonl`); close() })}>
            <Icon name="grid" size={16} />
            <span className="ka-out__text">
              <strong>As lines to keep</strong>
              <small>JSONL: one line per message — what was said, by whom, and when. Nothing of the engine's.</small>
            </span>
          </button>
        </div>
        <ErrorLine error={error} />
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
