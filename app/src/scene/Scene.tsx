// The Scene (P1–P21, Q1–Q5): docs/handoff/kataki-handoff/SCENE.md.
import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'
import { api, stream, type Cast, type CastEntity, type ContextLog, type KnownMemory, type Message, type Person, type Signals, type Story, type StoryUi, type TurnDone, type TurnMeta, type Version } from '../api'
import { K } from '../ds'
import { face, scenery, useLibrary, useLoad, usePoll } from '../hooks'
import { openMenu, toast, type MenuItem } from '../overlay'
import { pacer, SPEEDS, type Speed } from '../pace'
import { t } from '../strings'
import { Delete, Export } from '../sky/Stories'
import Backstage from './Backstage'
import Lines, { type LineActions } from './Lines'
import { force, read, type Mode } from './modes'
import { CharacterCard, FindBar, PassTime, ScenePlace, StorySettings, type Pass } from './Overlays'
import { later } from './time'
import { Board, defaults } from './Widgets'

type Live = { speaker: string; speakerId: number | null; text: string; thoughtAt?: number; thinkMs?: number; replacing?: number; rewriting?: number }
type Answer = 'any' | 'narrator' | `${number}`
type Open = 'pass' | 'place' | 'settings' | 'export' | 'delete' | null
type Skip = { minutes: number; from: string; to: string; line: number; note?: string }
const COLOURS = ['mike', 'theo', '4', '5', '6']
const ADVANCED = 'kataki.composer.advanced'
const kept = () => { try { return localStorage.getItem(ADVANCED) === '1' } catch { return false } }

export default function Scene() {
  const id = Number(useParams().id)
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { byId, items } = useLibrary()
  const [prefs] = useLoad(() => api<{ reply_speed?: Speed }>('/settings'), [])
  const version = useRef('')
  const [data, reload, error] = useLoad(
    () => Promise.all([
      api<Version>(`/stories/${id}/version`), api<Story>(`/stories/${id}`), api<Message[]>(`/stories/${id}/messages`),
      api<Cast>(`/stories/${id}/cast`), api<Signals>(`/stories/${id}/signals`), api<Person[]>(`/stories/${id}/people`),
    ]).then(([v, story, messages, cast, signals, people]) => {
      version.current = `${v.v}|${v.waiting}`
      return { story, messages, cast, signals, people }
    }),
    [id],
  )
  const [live, setLive] = useState<Live | null>(null)
  const [said, setSaid] = useState<string | null>(null)
  const [failed, setFailed] = useState('')
  const [draft, setDraft] = useState('')
  const [mode, setMode] = useState<Mode>('Auto')
  const [advanced, setAdvancedState] = useState(kept)
  const [answer, setAnswer] = useState<Answer>('any')
  const [queue, setQueue] = useState<string[]>([])
  const [editing, setEditing] = useState<number>()
  const [open, setOpen] = useState<Open>(null)
  const [card, setCard] = useState<number>()
  const [arranging, setArranging] = useState(false)
  const [reading, setReading] = useState(false)
  const [backstage, setBackstage] = useState(params.has('backstage'))
  const [finding, setFinding] = useState(false)
  const [found, setFound] = useState<number>()
  const [skip, setSkip] = useState<Skip | null>(null)
  const [meter, setMeter] = useState<{ used: number; budget: number }>()
  const [tick, setTick] = useState(0)
  const controller = useRef<AbortController | null>(null)
  const retryBody = useRef<{ path: string; body: object } | null>(null)
  const chat = useRef<HTMLDivElement>(null)
  const follow = useRef(true)
  const [below, setBelow] = useState(false)
  const setAdvanced = (v: boolean) => { setAdvancedState(v); try { localStorage.setItem(ADVANCED, v ? '1' : '0') } catch { /* kept for the session */ } }

  useEffect(() => () => controller.current?.abort(), [])
  useEffect(() => { api(`/stories/${id}/seen`, 'POST').catch(() => {}) }, [id])
  useEffect(() => {
    api<ContextLog>(`/stories/${id}/context`).then((c) => setMeter({ used: c.est_tokens, budget: c.budget }), () => {})
  }, [id])
  // Memory reads land in the background; when the story's version moves, what shows may have too.
  usePoll(() => {
    api<Version>(`/stories/${id}/version`).then(({ v, waiting }) => {
      const now = `${v}|${waiting}`
      if (version.current && now !== version.current) { version.current = now; reload(); setTick((x) => x + 1) }
    }, () => {})
  }, 3000, !live)

  // Opening a story, and every new line, keeps the newest line in view unless you scrolled up.
  const lines = () => chat.current?.querySelector<HTMLElement>('.k-chat__lines')
  useLayoutEffect(() => {
    const el = lines()
    if (el && follow.current) el.scrollTop = el.scrollHeight
  }, [data, live?.text, said, failed])
  useEffect(() => {
    const el = lines()
    if (!el) return
    const on = () => {
      const up = el.scrollHeight - el.scrollTop - el.clientHeight
      follow.current = up < 40
      setBelow(up > el.clientHeight)
    }
    el.addEventListener('scroll', on, { passive: true })
    return () => el.removeEventListener('scroll', on)
  }, [!!data, reading]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (found) document.getElementById(`line-${found}`)?.scrollIntoView({ block: 'center' })
  }, [found])

  const generate = async (path: string, body: object, extra: Partial<Live> = {}) => {
    retryBody.current = { path, body }
    setFailed('')
    const ctl = new AbortController()
    controller.current = ctl
    follow.current = true
    const from = { date: data?.story.date ?? '', clock: data?.story.clock ?? '' }
    setLive({ speaker: '', speakerId: null, text: '', ...extra })
    const typed = pacer((text) => setLive((l) => l && { ...l, text: l.text + text, thinkMs: l.thinkMs ?? (l.thoughtAt ? performance.now() - l.thoughtAt : undefined) }),
      SPEEDS[prefs?.reply_speed ?? 'normal'] ?? SPEEDS.normal)
    try {
      await stream(path, body, (kind, value) => {
        if (kind === 'meta') {
          const meta = value as TurnMeta
          setLive((l) => l && { ...l, speaker: meta.speaker?.name ?? t('scene.narrator'), speakerId: meta.speaker?.id ?? null })
          setMeter({ used: meta.context.est_tokens, budget: meta.context.budget })
          if (!extra.replacing && !extra.rewriting && meta.skip >= 1440 && meta.parent_id) showSkip(meta.skip, meta.from_date, meta.date, meta.parent_id)
        } else if (kind === 'thought') setLive((l) => l && { ...l, thoughtAt: l.thoughtAt ?? performance.now() })
        else if (kind === 'token') typed.push(value)
        else if (kind === 'done') {
          const done = value as TurnDone
          if (done.skip_minutes >= 1440) showSkip(done.skip_minutes, from.date, done.date, done.message_id)
        } else if (kind === 'error') setFailed(value.message)
      }, ctl.signal)
      await typed.drain()
    } catch (e) {
      if (!ctl.signal.aborted) setFailed((e as Error).message)
    } finally {
      typed.flush()
      if (controller.current === ctl) controller.current = null
      if (ctl.signal.aborted) await new Promise((r) => setTimeout(r, 400)) // the engine saves a stopped reply a moment later
      await reload()
      setLive(null)
      setSaid(null)
    }
  }
  // The time skip card (P12): the story, how much time, from → to, and what it cost a memory.
  const skipTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const showSkip = (minutes: number, from: string, to: string, line: number) => {
    setSkip({ minutes, from, to, line })
    clearTimeout(skipTimer.current)
    skipTimer.current = setTimeout(() => setSkip(null), 4200)
    api<Signals>(`/stories/${id}/signals`).then((s) => {
      const note = s.lines[line]?.skip?.text
      if (note) setSkip((k) => (k && k.line === line ? { ...k, note } : k))
    }, () => {})
  }
  useEffect(() => () => clearTimeout(skipTimer.current), [])

  const speaker = answer === 'any' ? null : answer === 'narrator' ? 'narrator' : Number(answer)
  const present = data?.cast.entities.filter((e) => e.is_ai && e.kind === 'character' && e.present) ?? []
  /** Your line is written first; only the reply waits for a model (SCENE.md › A turn). */
  const send = async (text: string, extra: { skip?: string } = {}) => {
    const line = text.trim()
    if (live) {
      if (line) { setQueue((q) => [...q, line]); setDraft('') }
      return
    }
    const how = force(line, mode)
    setMode('Auto')
    setDraft('')
    const lead = typeof speaker === 'number' ? speaker : present[0]?.id
    const audience = how.mode === 'Think' ? [] : how.mode === 'Whisper' ? (lead ? [lead] : []) : null
    if (how.mode === 'Think') {
      await api(`/stories/${id}/line`, 'POST', { text: how.text, audience: [], skip: extra.skip ?? null })
      return reload()
    }
    if (how.text) setSaid(how.text)
    await generate(`/stories/${id}/turn`, { text: how.text || null, speaker, audience, skip: extra.skip ?? null, narrate: how.mode === 'Narrate' })
  }
  // Lines typed while a reply was writing go out in order, one turn each.
  useEffect(() => {
    if (live || !queue.length) return
    const [next, ...rest] = queue
    setQueue(rest)
    send(next)
  }, [live, queue]) // eslint-disable-line react-hooks/exhaustive-deps

  const retry = () => {
    const was = retryBody.current
    if (!was) return
    if (was.path.endsWith('/turn')) return generate(was.path, { text: null, speaker: (was.body as { speaker?: unknown }).speaker ?? null })
    return generate(was.path, was.body)
  }
  const pass = async (p: Pass) => {
    setOpen(null)
    const before = data?.story.date ?? ''
    if (p.place) {
      await api(`/stories/${id}/scene`, 'POST', { present: present.map((e) => e.id), library_place_id: p.place, skip: p.skip })
    } else {
      const after = await api<Message[]>(`/stories/${id}/line`, 'POST', { text: null, audience: null, skip: p.skip })
      const last = after.at(-1)
      if (last && last.skip_minutes >= 1440) showSkip(last.skip_minutes, before, last.date, last.id)
    }
    reload()
  }
  const undoSkip = async (m: Message | number) => {
    const line = typeof m === 'number' ? data?.messages.find((x) => x.id === m) ?? (await api<Message[]>(`/stories/${id}/messages`)).find((x) => x.id === m) : m
    if (!line) return
    setSkip(null)
    await api(`/messages/${line.id}`, 'PATCH', line.role === 'system' ? { skip_minutes: 0, hidden: true } : { skip_minutes: 0 })
    toast(t('toast.skipUndone'), {}, 3000)
    reload()
  }
  const saveUi = (ui: StoryUi) => data && api(`/stories/${id}`, 'PATCH', { ui: { ...data.story.ui, ...ui } }).then(reload)
  const move = async (e: CastEntity) => {
    await api(`/stories/${id}/presence`, 'POST', { entity_id: e.id, present: !e.present })
    reload()
  }

  const act: LineActions = {
    swipe: (m, step) => api(`/stories/${id}/swipe`, 'POST', { message_id: m.id, step }).then(reload),
    retake: (m) => generate(`/stories/${id}/regenerate`, {}, { replacing: m.id }),
    save: (m, text) => api(`/messages/${m.id}`, 'PATCH', { text }).then(reload),
    rewrite: (m, text) => { setSaid(m.role === 'user' ? text : null); generate(`/messages/${m.id}/rewrite`, { text }, { rewriting: m.id }) },
    hide: (m, hidden) => {
      api(`/messages/${m.id}`, 'PATCH', { hidden }).then(reload)
      if (hidden) toast(t('toast.hidden'), { action: t('toast.undo'), onAction: () => api(`/messages/${m.id}`, 'PATCH', { hidden: false }).then(reload) }, 6000)
    },
    undoSkip: (m) => undoSkip(m),
    undoPresence: (pid) => api(`/presence/${pid}`, 'DELETE').then(reload),
    menu: (at, m) => openMenu(at, lineMenu(m)),
  }
  const lineMenu = (m: Message): MenuItem[] => [
    { label: t('lm.copy'), icon: 'quote', onSelect: () => navigator.clipboard?.writeText(m.text).then(() => toast(t('toast.copiedLine'), {}, 2000), () => {}) },
    { label: t('lm.edit'), detail: m.role === 'user' ? t('lm.editDetail') : undefined, icon: 'edit', disabled: !!live, onSelect: () => setEditing(m.id) },
    ...(m.role === 'assistant' && m.id === data?.messages.findLast((x) => x.role === 'assistant')?.id
      ? [{ label: t('lm.newTake'), icon: 'refresh' as const, disabled: !!live, onSelect: () => act.retake(m) }] : []),
    { divider: true },
    { label: t(m.hidden ? 'lm.show' : 'lm.hide'), icon: 'eyeoff', onSelect: () => act.hide(m, !m.hidden) },
  ]
  const storyMenu = (): MenuItem[] => [
    { label: t('sm.edit'), detail: t('sm.editDetail'), icon: 'layers', onSelect: () => { setReading(false); setArranging(true) } },
    { label: t('sm.reading'), detail: t('sm.readingDetail'), icon: 'book', onSelect: () => setReading(true) },
    { label: t('sm.scene'), detail: t('sm.sceneDetail'), icon: 'map-pin', onSelect: () => setOpen('place') },
    { label: t('sm.pass'), detail: t('sm.passDetail'), icon: 'clock', disabled: !!live, onSelect: () => setOpen('pass') },
    { label: t('sm.plot'), detail: t('sm.plotDetail'), icon: 'quote', disabled: !!live || !items.some((i) => i.kind === 'scenario'), onSelect: () => openMenu(document.querySelector('.scene__tr .k-scenebtn:last-child') ?? document.body, plotMenu()) },
    { label: t('sm.backstage'), detail: t('sm.backstageDetail'), icon: 'cpu', onSelect: () => setBackstage(true) },
    { label: t('sm.settings'), detail: t('sm.settingsDetail'), icon: 'settings', onSelect: () => setOpen('settings') },
    { divider: true },
    { label: t('sm.export'), icon: 'download', onSelect: () => setOpen('export') },
    { label: t(data?.story.pinned ? 'sm.unpin' : 'sm.pin'), icon: 'pushpin', onSelect: () => api(`/stories/${id}`, 'PATCH', { pinned: !data?.story.pinned }).then(reload) },
    { divider: true },
    { label: t('sm.delete'), icon: 'trash', danger: true, onSelect: () => setOpen('delete') },
  ]
  // A plot dropped in: the narrator speaks its opening line (P21).
  const plotMenu = (): MenuItem[] => items.filter((i) => i.kind === 'scenario').map((p) => ({
    label: p.name, detail: p.description, icon: 'quote' as const,
    onSelect: () => api(`/stories/${id}/line`, 'POST', { text: (p.data.first_message || p.description).replace(/^\*|\*$/g, ''), audience: null, narrate: true }).then(reload),
  }))

  // Keys (KEYBOARD.md): Esc stops, then leaves whatever is open, then goes back up to the Sky.
  useEffect(() => {
    const on = (e: KeyboardEvent) => {
      const ctrl = e.ctrlKey || e.metaKey
      if (e.key === 'Escape' && !e.defaultPrevented) {
        if (controller.current) controller.current.abort()
        else if (document.querySelector('.ov, [role="menu"]')) return
        else if (reading) setReading(false)
        else if (backstage) setBackstage(false)
        else if (!arranging && editing === undefined) navigate(-1)
        return
      }
      if (!ctrl) return
      const k = e.key.toLowerCase()
      if (k === 'b') { e.preventDefault(); setBackstage((b) => !b) }
      else if (k === 'f') { e.preventDefault(); setFinding(true) }
      else if (k === 'e' && !e.shiftKey) { e.preventDefault(); setArranging(true) }
      else if (k === 'r' && e.shiftKey) { e.preventDefault(); setReading((r) => !r) }
      else if (k === 'j') { e.preventDefault(); send('') }
      else if (k === 'r' && !e.shiftKey && !live) {
        const last = data?.messages.findLast((m) => m.role === 'assistant')
        if (last && last.id === data?.messages.at(-1)?.id) { e.preventDefault(); act.retake(last) }
      }
    }
    addEventListener('keydown', on)
    return () => removeEventListener('keydown', on)
  })

  if (!data) {
    return (
      <div className="scene">
        <div className="scene__tint" />
        <div className="scene__chat">{error ? <K.Alert title={t('scene.wontOpen')}>{error}</K.Alert> : <K.Spinner label={t('scene.label')} />}</div>
      </div>
    )
  }

  const { story, messages, cast, signals, people } = data
  const item = (e: { lib_item_id: number | null }) => (e.lib_item_id ? byId.get(e.lib_item_id) : undefined)
  const itemOf = (entityId: number | null) => { const e = cast.entities.find((x) => x.id === entityId); return e ? item(e) : undefined }
  const persona = story.persona?.name
  const characters = cast.entities.filter((e) => e.is_ai && e.kind === 'character')
  const away = characters.filter((e) => !e.present)
  const colour = (m: Message) => {
    if (m.role === 'user') return 'var(--speaker-liv)'
    const i = characters.findIndex((e) => e.id === m.speaker_id)
    return i < 0 ? 'var(--scene-ink)' : `var(--speaker-${COLOURS[i % COLOURS.length]})`
  }
  const cutAt = live?.rewriting ? messages.findIndex((m) => m.id === live.rewriting) : -1
  const shown = live?.replacing ? messages.filter((m) => m.id !== live.replacing) : cutAt >= 0 ? messages.slice(0, cutAt) : messages
  const lead = live?.speakerId ? characters.find((e) => e.id === live.speakerId) : present[0]
  const place = story.place ? item(story.place) : undefined
  const art = scenery(place)
  const artSrc = art.src ?? (art.place ? K.ART[art.place]?.src ?? undefined : undefined)
  const offline = /model|reach|connect|provider|server/i.test(failed)
  const first = !messages.some((m) => m.role === 'user') && !said
  const who = persona ?? 'you'
  const placeholder = live ? t('scene.placeholderAnswering', { name: live.speaker || lead?.name || t('scene.narrator') })
    : offline ? t('composer.placeholderOffline')
    : first && lead ? t('scene.placeholderFirst', { name: lead.name, persona: who })
    : t('scene.placeholder', { persona: who })
  const reading1 = read(draft)
  const detected = mode === 'Auto' ? reading1.detected : ''
  const heard = mode === 'Think' || reading1.mode === 'Think' ? [] : present
  const answers = [
    { id: 'any', label: t('scene.answers.any'), icon: 'users' as const },
    ...present.map((e) => ({ id: String(e.id), label: e.name, ...face(item(e), e.name) })),
    { id: 'narrator', label: t('scene.answers.narrator'), icon: 'quill' as const },
  ]
  const lastSpeakers = [messages.at(-1)?.speaker_id].filter((x): x is number => typeof x === 'number')
  const cardEntity = characters.find((e) => e.id === card)
  const feelingOf = (eid: number) => people.find((p) => p.id === eid)?.relationships.find((r) => r.you)?.rel
  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send(draft).then(() => setOpen('pass')); return true }
    if (e.key === 'ArrowUp' && !draft) {
      const mine = messages.findLast((m) => m.role === 'user' && !m.hidden)
      if (mine) { e.preventDefault(); setEditing(mine.id); return true }
    }
    if (e.key === 'Tab' && advanced && !e.shiftKey) {
      e.preventDefault()
      const i = answers.findIndex((a) => a.id === answer)
      setAnswer(answers[(i + 1) % answers.length].id as Answer)
      return true
    }
    return false
  }
  const header = (
    <>
      <div className="scene__tl">
        <K.SceneHeader title={story.title} backHref="/home"
          subtitle={backstage ? t('bs.sub', { n: messages.filter((m) => m.role === 'assistant').length, time: story.clock.slice(-5) })
            : persona ? t('scene.subtitle', { persona, book: story.book?.title ?? 'none' }) : t('scene.directing')} />
      </div>
      <div className="scene__tr">
        <K.BackstageToggle on={backstage} onToggle={setBackstage} />
        {backstage ? <K.SceneButton icon="x" label={t('bs.leave')} onClick={() => setBackstage(false)} /> : (
          <>
            <K.SceneButton icon="search" label={t('scene.search')} onClick={() => setFinding(true)} />
            <K.SceneButton icon="dots" label={t('scene.menu')} onClick={(e: { currentTarget: Element }) => openMenu(e.currentTarget, storyMenu())} />
          </>
        )}
      </div>
    </>
  )

  return (
    <div className={`scene${arranging ? ' is-arranging' : ''}`}>
      {artSrc ? <img className="scene__art" src={artSrc} alt={place?.name ?? ''} /> : <div className="scene__art scene__place" />}
      <div className="scene__tint" />
      <div className="scene__vig" />

      {reading ? (
        <>
          <div className="scene__tl row" style={{ gap: 12 }}>
            <K.SceneButton icon="x" label={t('read.leave')} onClick={() => setReading(false)} />
            <span className="scene-t">{t('read.hint')}</span>
          </div>
          <div className="scene__tr">
            <K.SceneButton icon="search" label={t('scene.search')} onClick={() => setFinding(true)} />
            <K.SceneButton icon="download" label={t('read.export')} onClick={() => setOpen('export')} />
          </div>
          <div className="readcol" aria-label={t('scene.label')}>
            <Lines story={story} messages={messages} cast={cast} advanced={false} busy colour={colour} itemOf={itemOf} act={act} reading found={found}
              onEditing={() => {}} />
          </div>
        </>
      ) : (
        <>
          {header}
          {backstage && (
            <Backstage story={story} messages={messages} cast={cast.entities} tick={tick} focus={Number(params.get('backstage')) || undefined}
              onForget={(m: KnownMemory) => {
                api(`/memories/${m.memory_id}`, 'PATCH', { hidden: true }).then(() => setTick((x) => x + 1))
                toast(t('toast.forgot', { n: 1 }), { action: t('toast.undo'), onAction: () => api(`/memories/${m.memory_id}`, 'PATCH', { hidden: false }).then(() => setTick((x) => x + 1)) })
              }} />
          )}
          <div className="scene__chat" ref={chat} inert={arranging || backstage}>
            <K.ChatPanel label={t('scene.label')} composer={
              <K.Composer value={draft} onChange={setDraft} onSend={(v: string) => send(v)} placeholder={placeholder} onKey={onKey}
                streaming={!!live} onStop={() => controller.current?.abort()} onContinue={() => send('')} onPassTime={() => setOpen('pass')}
                advanced={advanced} onAdvanced={setAdvanced} mode={mode === 'Auto' ? t('mode.auto') : mode} detected={detected}
                onMode={(e: { currentTarget: Element }) => openMenu(e.currentTarget, (['Auto', 'Say', 'Do', 'Whisper', 'Think', 'Narrate'] as Mode[]).map((m) => ({
                  label: t(`mode.${m.toLowerCase()}` as 'mode.auto'), detail: t(`mode.${m.toLowerCase()}Sub` as 'mode.autoSub'), checked: m === mode, onSelect: () => setMode(m),
                })), t('mode.label'))}
                queued={queue.length ? t('composer.queued', { n: queue.length }) : undefined}
                hearing={heard.map((e) => ({ ...face(item(e), e.name) }))}
                hearingText={heard.length ? t('scene.hearing', { names: new Intl.ListFormat('en').format(heard.map((e) => e.name)) }) : t('mode.thinkSub')}
                away={away.length ? t('composer.away', { names: new Intl.ListFormat('en').format(away.map((e) => e.name)), n: away.length }) : undefined}
                tokens={meter ? t('scene.tokens', { used: meter.used.toLocaleString('en'), limit: meter.budget.toLocaleString('en') }) : undefined}
                meter={meter?.budget ? Math.min(100, Math.round((100 * meter.used) / meter.budget)) : undefined}
                answers={answers} answer={answer} onAnswer={(a: string) => setAnswer(a as Answer)} />
            }>
              <Lines story={story} messages={shown} cast={cast} signals={signals} advanced={advanced} busy={!!live} editing={editing} onEditing={setEditing}
                colour={colour} itemOf={itemOf} act={act} found={found} />
              {said && <K.ChatLine speaker="user" color="var(--speaker-liv)" name={persona ?? t('scene.narrator')} time="" text={said} />}
              {live && (
                <K.ChatLine speaker={String(live.speakerId)} color={colour({ role: 'assistant', speaker_id: live.speakerId } as Message)} name={live.speaker || '…'} time=""
                  text={live.text} writing thought={live.thinkMs ? t('scene.thought', { s: Math.max(1, Math.round(live.thinkMs / 1000)) }) : undefined} />
              )}
              {failed && (
                <div className="lineerr" role="alert">
                  <K.Icon name="alert" size={18} color="var(--bad)" />
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <b style={{ fontSize: 14 }}>{t(offline ? 'scene.err.offline' : 'scene.err.title')}</b>
                    <span className="scene-t">{failed}</span>
                    <div className="row" style={{ gap: 8 }}>
                      <button type="button" className="k-btn k-btn--scene-send" onClick={retry}>{t('scene.err.retry')}</button>
                      {messages.at(-1)?.role === 'user' && <button type="button" className="k-btn k-btn--scene-ghost" onClick={() => { setFailed(''); setEditing(messages.at(-1)!.id) }}>{t('scene.err.editLine')}</button>}
                      {offline && <a className="k-btn k-btn--scene-ghost" href="/settings/models">{t('scene.err.models')}</a>}
                    </div>
                  </div>
                </div>
              )}
            </K.ChatPanel>
            {below && (
              <button type="button" className="k-scenechip jump" onClick={() => { follow.current = true; const el = lines(); if (el) el.scrollTop = el.scrollHeight }}>
                <K.Icon name="down" size={14} />{t('scene.jump')}
              </button>
            )}
          </div>
          {!backstage && (
            <Board story={story} people={present} everyone={characters} itemOf={item} speaking={live && !live.text ? live.speakerId ?? undefined : undefined}
              active={lastSpeakers} editing={arranging} onDone={() => setArranging(false)} onSave={saveUi} onPassTime={() => setOpen('pass')}
              onOpen={setCard} busy={!!live} detail={feelingOf} />
          )}
        </>
      )}

      {finding && (
        <FindBar ids={(q) => messages.filter((m) => !m.hidden && m.text.toLowerCase().includes(q)).map((m) => m.id)} onFind={setFound} onClose={() => setFinding(false)} />
      )}
      {skip && (
        <div className="skipwrap">
          <K.TimeSkipCard story={story.title} from={skip.from} to={skip.to} note={skip.note} onUndo={() => undoSkip(skip.line)}>{later(skip.minutes)}</K.TimeSkipCard>
        </div>
      )}
      {open === 'pass' && <PassTime story={story} onClose={() => setOpen(null)} onPass={pass} />}
      {open === 'place' && (
        <ScenePlace story={story} characters={characters} onClose={() => setOpen(null)}
          onChange={(body) => { setOpen(null); api(`/stories/${id}/scene`, 'POST', body).then(reload) }} />
      )}
      {open === 'settings' && <StorySettings story={story} advanced={advanced} onAdvanced={setAdvanced} onClose={() => setOpen(null)} onChange={reload} />}
      {open === 'export' && <Export story={story} onClose={() => setOpen(null)} />}
      {open === 'delete' && (
        <Delete story={story} onClose={() => setOpen(null)} onExport={() => setOpen('export')}
          onDelete={() => { setOpen(null); api(`/stories/${id}`, 'DELETE').then(() => navigate('/stories', { replace: true })) }} />
      )}
      {cardEntity && (
        <CharacterCard story={story} entity={cardEntity} item={item(cardEntity)} onClose={() => setCard(undefined)}
          onAnswer={() => { setAnswer(String(cardEntity.id) as Answer); setAdvanced(true); setCard(undefined) }}
          onMove={() => { move(cardEntity); setCard(undefined) }}
          onWidget={(story.ui.widgets ?? defaults(present)).some((w) => w.entity === cardEntity.id) ? undefined
            : () => { saveUi({ widgets: [...(story.ui.widgets ?? defaults(present)), { id: `c${cardEntity.id}`, kind: 'character', entity: cardEntity.id, pinned: true }] }); setCard(undefined) }} />
      )}
    </div>
  )
}
