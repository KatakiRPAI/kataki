// The Scene (P1–P21, Q1–Q5): docs/handoff/kataki-handoff/SCENE.md.
import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'
import { api, stream, type Provider, type RoleRow, type Cast, type CastEntity, type ContextLog, type KnownMemory, type Message, type Person, type Signals, type Story, type StoryUi, type TurnDone, type TurnMeta, type Version } from '../api'
import { K } from '../ds'
import { face, scenery, twelve, useLibrary, useLoad, useNarrow, usePoll, useTitle } from '../hooks'
import { openMenu, Overlay, toast, type MenuItem } from '../overlay'
import { pacer, SPEEDS, type Speed } from '../pace'
import { pref } from '../prefs'
import { t } from '../strings'
import { is, keysOf, parts } from '../shortcuts'
import { openFeedback } from '../sky/Feedback'
import { classify, err } from '../errors'
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
  // the model's name, for the error's own words
  const [provider] = useLoad(async () => {
    const rp = (await api<RoleRow[]>('/roles')).find((r) => r.role === 'rp')
    return (await api<Provider[]>('/providers')).find((p) => p.id === rp?.effective_provider_id)
  }, [])
  const providerName = provider?.name ?? ''
  const providerUrl = (provider?.base_url ?? '').replace(/^https?:\/\//, '')
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
  useTitle(data?.story.title)
  const [live, setLive] = useState<Live | null>(null)
  const [said, setSaid] = useState<string | null>(null)
  const [failed, setFailed] = useState('')
  const [draft, setDraft] = useState('')
  const home = pref<Mode>('story.composerMode', 'Auto') // a mode picked in the menu is for one line, then this again
  const [mode, setMode] = useState<Mode>(home)
  const [advanced, setAdvancedState] = useState(kept)
  const [answer, setAnswer] = useState<Answer>('any')
  const [queue, setQueue] = useState<string[]>([])
  const [editing, setEditing] = useState<number>()
  const [open, setOpen] = useState<Open>(null)
  const [card, setCard] = useState<number>()
  const [confirm, setConfirm] = useState<{ kind: 'rewind' | 'delete'; m: Message } | null>(null)
  const [arranging, setArranging] = useState(false)
  const [reading, setReading] = useState(false)
  const [backstage, setBackstage] = useState(params.has('backstage'))
  const [finding, setFinding] = useState(false)
  const [found, setFound] = useState<number | undefined>(() => Number(params.get('line')) || undefined) // a line opened from search
  const [skip, setSkip] = useState<Skip | null>(null)
  const [meter, setMeter] = useState<{ used: number; budget: number }>()
  const [tick, setTick] = useState(0)
  const [here, setHere] = useState(false) // below 1024 the widgets fold into a Here sheet (R4)
  const controller = useRef<AbortController | null>(null)
  const retryBody = useRef<{ path: string; body: object } | null>(null)
  const chat = useRef<HTMLDivElement>(null)
  const follow = useRef(!params.get('line'))
  const [below, setBelow] = useState(false)
  const setAdvanced = (v: boolean) => { setAdvancedState(v); try { localStorage.setItem(ADVANCED, v ? '1' : '0') } catch { /* kept for the session */ } }

  useEffect(() => () => controller.current?.abort(), [])
  useEffect(() => { api(`/stories/${id}/seen`, 'POST').catch(() => {}) }, [id])
  useEffect(() => { if (data && !params.get('line')) document.querySelector<HTMLElement>('.k-chat__composer textarea')?.focus() }, [!!data]) // eslint-disable-line react-hooks/exhaustive-deps
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
  const narrow = useNarrow(1024) // R4: the header folds, the widgets go behind "Here"
  const present = data?.cast.entities.filter((e) => e.is_ai && e.kind === 'character' && e.present) ?? []
  /** Your line is written first; only the reply waits for a model (SCENE.md › A turn). */
  const send = async (text: string, extra: { skip?: string } = {}) => {
    const line = text.trim()
    if (live) {
      if (line) { setQueue((q) => [...q, line]); setDraft('') }
      return
    }
    const how = force(line, mode)
    setMode(home)
    setDraft('')
    const lead = typeof speaker === 'number' ? speaker : present[0]?.id
    const audience = how.mode === 'Think' ? [] : how.mode === 'Whisper' ? (lead ? [lead] : []) : null
    if (how.mode === 'Think') {
      try {
        await api(`/stories/${id}/line`, 'POST', { text: how.text, audience: [], skip: extra.skip ?? null })
      } catch {
        setDraft(line) // it stays in the composer until it can be written
        const e = err('LINE_SAVE_FAILED')
        toast(e.title, { icon: 'alert', action: e.actions[0], onAction: () => send(line, extra) }, 10000)
      }
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

  useEffect(() => {
    if (!failed || live || !['REPLY_UNREACHABLE', 'API_UNREACHABLE', 'API_RATE_LIMITED'].includes(classify(failed))) return
    const again = setTimeout(() => retry(), 10_000)
    return () => clearTimeout(again)
  }, [failed, live]) // eslint-disable-line react-hooks/exhaustive-deps
  const retry = () => {
    const was = retryBody.current
    if (!was) return
    if (was.path.endsWith('/turn')) return generate(was.path, { text: null, speaker: (was.body as { speaker?: unknown }).speaker ?? null })
    return generate(was.path, was.body)
  }
  const [passFailed, setPassFailed] = useState<Pass>()
  const pass = async (p: Pass) => {
    setOpen(null)
    const before = data?.story.date ?? ''
    try { await passNow(p, before) } catch { setPassFailed(p) }
    reload()
  }
  const passNow = async (p: Pass, before: string) => {
    if (p.place) {
      await api(`/stories/${id}/scene`, 'POST', { present: present.map((e) => e.id), library_place_id: p.place, skip: p.skip })
    } else {
      const after = await api<Message[]>(`/stories/${id}/line`, 'POST', { text: null, audience: null, skip: p.skip })
      const last = after.at(-1)
      if (last && last.skip_minutes >= 1440) showSkip(last.skip_minutes, before, last.date, last.id)
    }
  }
  const undoSkip = async (m: Message | number) => {
    const line = typeof m === 'number' ? data?.messages.find((x) => x.id === m) ?? (await api<Message[]>(`/stories/${id}/messages`)).find((x) => x.id === m) : m
    if (!line) return
    setSkip(null)
    await api(`/messages/${line.id}`, 'PATCH', line.role === 'system' ? { skip_minutes: 0, hidden: true } : { skip_minutes: 0 })
    toast(t('toast.skipUndone'), {}, 3000)
    reload()
  }
  const pin = (on: boolean) => api(`/stories/${id}`, 'PATCH', { pinned: on }).then(() => {
    reload()
    toast(t('toast.pinned', { pinned: on ? 'yes' : 'no' }), { icon: 'pushpin', action: t('toast.undo'), onAction: () => api(`/stories/${id}`, 'PATCH', { pinned: !on }).then(reload) }, 10000)
  })
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
      if (hidden) toast(t('toast.hidden'), { icon: 'eyeoff', action: t('toast.undo'), onAction: () => api(`/messages/${m.id}`, 'PATCH', { hidden: false }).then(reload) }, 6000)
    },
    undoSkip: (m) => undoSkip(m),
    undoPresence: (pid) => api(`/presence/${pid}`, 'DELETE').then(reload),
    menu: (at, m) => openMenu(at, lineMenu(m)),
  }
  /** How many lines follow this one on the story as it reads now. */
  const after = (m: Message) => { const all = data?.messages ?? []; const i = all.findIndex((x) => x.id === m.id); return i < 0 ? 0 : all.length - 1 - i }
  const lineMenu = (m: Message): MenuItem[] => [
    { label: t('lm.copy'), icon: 'quote', onSelect: () => navigator.clipboard?.writeText(m.text).then(() => toast(t('toast.copiedLine'), {}, 2000), () => {}) },
    { label: t('lm.edit'), detail: m.role === 'user' ? t('lm.editDetail') : undefined, icon: 'edit', disabled: !!live, onSelect: () => setEditing(m.id) },
    ...(m.role === 'assistant' && m.id === data?.messages.findLast((x) => x.role === 'assistant')?.id
      ? [{ label: t('lm.newTake'), icon: 'refresh' as const, disabled: !!live, onSelect: () => act.retake(m) }] : []),
    { label: t(m.hidden ? 'lm.show' : 'lm.hide'), icon: 'eyeoff', onSelect: () => act.hide(m, !m.hidden) },
    { label: t('lm.branch'), icon: 'merge', disabled: !!live, onSelect: () => api<{ story_id: number }>(`/messages/${m.id}/branch`, 'POST').then((b) => { toast(t('toast.branched', { story: `${data?.story.title} · branch` }), {}, 4000); navigate(`/story/${b.story_id}`) }) },
    { divider: true },
    ...(after(m) > 0 ? [{ label: t('lm.rewind'), detail: t('lm.rewindDetail', { n: after(m) }), icon: 'undo' as const, danger: true, disabled: !!live, onSelect: () => setConfirm({ kind: 'rewind', m }) }]
      : [{ label: t('lm.delete'), detail: t('lm.deleteDetail'), icon: 'trash' as const, danger: true, disabled: !!live, onSelect: () => setConfirm({ kind: 'delete', m }) }]),
  ]
  const storyMenu = (): MenuItem[] => [
    { label: t('sm.edit'), detail: t('sm.editDetail'), icon: 'layers', shortcut: parts(keysOf('widgets')), onSelect: () => { setReading(false); setArranging(true) } },
    { label: t('sm.reading'), detail: t('sm.readingDetail'), icon: 'book', shortcut: parts(keysOf('reading')), onSelect: () => setReading(true) },
    { label: t('sm.scene'), detail: t('sm.sceneDetail'), icon: 'map-pin', onSelect: () => setOpen('place') },
    { label: t('sm.pass'), detail: t('sm.passDetail'), icon: 'clock', disabled: !!live, onSelect: () => setOpen('pass') },
    { label: t('sm.plot'), detail: t('sm.plotDetail'), icon: 'quote', disabled: !!live || !items.some((i) => i.kind === 'scenario'), onSelect: () => openMenu(document.querySelector('.scene__tr .k-scenebtn:last-child') ?? document.body, plotMenu()) },
    { label: t('sm.backstage'), detail: t('sm.backstageDetail'), icon: 'cpu', shortcut: parts(keysOf('backstage')), onSelect: () => setBackstage(true) },
    { label: t('sm.settings'), detail: t('sm.settingsDetail'), icon: 'settings', onSelect: () => setOpen('settings') },
    { divider: true },
    { label: t('sm.export'), icon: 'download', onSelect: () => setOpen('export') },
    { label: t(data?.story.pinned ? 'sm.unpin' : 'sm.pin'), icon: 'pushpin', onSelect: () => pin(!data?.story.pinned) },
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
      // F6 cycles the regions: header, the story, the composer, the widgets (KEYBOARD.md › The Scene)
      if (e.key === 'F6') {
        e.preventDefault()
        const regions = ['.scene__tl .k-scenebtn', '.scene__chat .k-line', '.scene__chat textarea', '.scene__right .k-widget button, .scene__left .k-widget button']
          .map((q) => document.querySelector<HTMLElement>(q)).filter((x): x is HTMLElement => !!x)
        const at = regions.findIndex((r) => r.closest('.scene__tl, .scene__chat .k-chat__lines, .k-chat__composer, .scene__right, .scene__left')?.contains(document.activeElement))
        regions[(at + (e.shiftKey ? regions.length - 1 : 1)) % regions.length]?.focus()
        return
      }
      // Alt ← / Alt → flip the takes of the focused line, or the last reply
      if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight') && data) {
        const id = Number((document.activeElement?.closest('.k-line') as HTMLElement | null)?.id.replace('line-', ''))
        const m = data.messages.find((x) => x.id === id) ?? data.messages.findLast((x) => x.role === 'assistant')
        if (m && m.swipe[1] > 1) { e.preventDefault(); act.swipe(m, e.key === 'ArrowLeft' ? -1 : 1) }
        return
      }
      if (!ctrl) return
      if (is(e, 'backstage')) { e.preventDefault(); setBackstage((b) => !b) }
      else if (is(e, 'find')) { e.preventDefault(); setFinding(true) }
      else if (is(e, 'widgets')) { e.preventDefault(); setArranging(true) }
      else if (is(e, 'reading')) { e.preventDefault(); setReading((r) => !r) }
      else if (is(e, 'continue')) { e.preventDefault(); send('') }
      else if (is(e, 'regenerate') && !live) {
        const last = data?.messages.findLast((m) => m.role === 'assistant')
        if (last && last.id === data?.messages.at(-1)?.id) { e.preventDefault(); act.retake(last) }
      }
    }
    addEventListener('keydown', on)
    return () => removeEventListener('keydown', on)
  })

  if (!data) {
    if (/\b404\b|not found/i.test(error)) return <Gone />
    return (
      <div className="scene">
        <div className="scene__tint" />
        <div className="scene__chat">{!error ? <K.Spinner label={t('scene.label')} />
          : (() => { const e = err('STORY_UNREADABLE', { story: t('scene.thisStory'), goodLines: '…', badLines: t('scene.some') }); return (
            <K.Alert title={e.title} code={e.code} actions={<><K.Button href="/settings/data">{e.actions[1]}</K.Button><K.Button variant="ghost" onClick={() => openFeedback('bug')}>{e.actions[2]}</K.Button></>}>{e.body}</K.Alert>
          ) })()}</div>
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
  const failedCode = classify(failed, !!providerName && !/^(localhost|127\.|\[::1\])/.test(providerUrl))
  const offline = ['REPLY_UNREACHABLE', 'API_UNREACHABLE', 'MODEL_GONE', 'REPLY_TIMEOUT'].includes(failedCode)
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
    if (is(e, 'sendPass')) { e.preventDefault(); send(draft).then(() => setOpen('pass')); return true }
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
            : narrow ? t('scene.subtitleNarrow', { persona: persona ?? t('scene.nobody'), time: twelve(story.clock), place: story.place?.name ?? 'none' })
            : persona ? t('scene.subtitle', { persona, book: story.book?.title ?? 'none' }) : t('scene.directing')} />
      </div>
      <div className="scene__tr">
        {narrow && !backstage && (
          <button type="button" className="scene__herepill" aria-pressed={here} onClick={() => setHere((x) => !x)}>
            <K.AvatarStack people={present.map((e) => face(itemOf(e.id), e.name))} size={26} max={3} />{t('scene.here')}
          </button>
        )}
        {narrow ? <K.SceneButton icon="layers" label={t('sc.backstage')} pressed={backstage} onClick={() => setBackstage((x) => !x)} /> : <K.BackstageToggle on={backstage} onToggle={setBackstage} />}
        {backstage ? <K.SceneButton icon="x" label={t('bs.leave')} onClick={() => setBackstage(false)} /> : (
          <>
            {!narrow && <K.SceneButton icon="search" label={t('scene.search')} onClick={() => setFinding(true)} />}
            <K.SceneButton icon="dots" label={t('scene.menu')} onClick={(e: { currentTarget: Element }) => openMenu(e.currentTarget, storyMenu())} />
          </>
        )}
      </div>
    </>
  )

  return (
    <div className={`scene${arranging ? ' is-arranging' : ''}${here ? ' show-here' : ''}`}>
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
                toast(t('toast.forgot', { name: 'none', n: 1 }), { icon: 'eyeoff', action: t('toast.undo'), onAction: () => api(`/memories/${m.memory_id}`, 'PATCH', { hidden: false }).then(() => setTick((x) => x + 1)) })
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
              {failed && (() => {
                const e = err(failedCode, { name: lead?.name ?? t('scene.narrator'), server: providerName, time: twelve(story.clock), seconds: 60 })
                const does = (a: string) =>
                  /^Try/.test(a) ? retry
                  : /Edit my line/.test(a) && messages.at(-1)?.role === 'user' ? () => { setFailed(''); setEditing(messages.at(-1)!.id) }
                  : /New take/.test(a) ? () => { const r = messages.findLast((m) => m.role === 'assistant'); if (r) act.retake(r) }
                  : /Continue it/.test(a) ? () => send('')
                  : /Keep it/.test(a) ? () => setFailed('')
                  : /own model|Open Settings/.test(a) ? () => navigate('/settings/models')
                  : undefined
                return (
                  <div className="lineerr" role="alert" title={failed}>
                    <K.Icon name="alert" size={18} color="var(--bad)" />
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <b style={{ fontSize: 14 }}>{e.title}</b>
                      <span className="scene-t">{e.body}</span>
                      <div className="row row--wrap" style={{ gap: 8 }}>
                        {e.actions.map((a, i) => { const run = does(a); return run ? <button key={a} type="button" className={`k-btn ${i ? 'k-btn--scene-ghost' : 'k-btn--scene-send'}`} onClick={run}>{a}</button> : null })}
                      </div>
                      <span className="errcode">{e.code}</span>
                    </div>
                  </div>
                )
              })()}
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
              onOpen={setCard} busy={!!live} detail={feelingOf}
              onAnswer={(eid) => { setAnswer(String(eid) as Answer); setAdvanced(true) }}
              onMove={(eid) => { const e = characters.find((x) => x.id === eid); if (e) move(e) }}
              onArrange={() => { setReading(false); setArranging(true) }} onSetTime={() => setOpen('place')} />
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
      {passFailed && (() => { const e = err('TIMESKIP_FAILED', { fromTime: twelve(story.clock) }); return (
        <Overlay onClose={() => setPassFailed(undefined)}>
          <K.Dialog icon="clock" tone="warm" size="sm" title={e.title} description={e.body} onClose={() => setPassFailed(undefined)}
            actions={[<K.Button key="c" variant="ghost" onClick={() => setPassFailed(undefined)}>{e.actions[1]}</K.Button>, <K.Button key="t" variant="primary" onClick={() => { const p = passFailed; setPassFailed(undefined); pass(p) }}>{e.actions[0]}</K.Button>]} />
        </Overlay>
      ) })()}
      {open === 'place' && (
        <ScenePlace story={story} characters={characters} onClose={() => setOpen(null)}
          onChange={(body) => {
            setOpen(null)
            // moving is a new scene; staying but letting the hour turn is only time passing
            const same = !body.library_place_id && characters.every((e) => body.present.includes(e.id) === e.present)
            ;(same && body.skip ? api(`/stories/${id}/line`, 'POST', { text: null, audience: null, skip: body.skip }) : api(`/stories/${id}/scene`, 'POST', body)).then(reload)
          }} />
      )}
      {open === 'settings' && <StorySettings story={story} advanced={advanced} onAdvanced={setAdvanced} onClose={() => setOpen(null)} onChange={reload} />}
      {open === 'export' && <Export story={story} onClose={() => setOpen(null)} />}
      {open === 'delete' && (
        <Delete story={story} onClose={() => setOpen(null)} onExport={() => setOpen('export')}
          onDelete={() => { setOpen(null); api(`/stories/${id}`, 'DELETE').then(() => navigate('/stories', { replace: true })) }} />
      )}
      {confirm && (
        <Overlay onClose={() => setConfirm(null)}>
          <K.Dialog icon={confirm.kind === 'rewind' ? 'undo' : 'trash'} tone="bad" size="sm" onClose={() => setConfirm(null)}
            title={confirm.kind === 'rewind' ? t('rw.title', { time: twelve(confirm.m.clock) }) : t('dl.title')}
            description={confirm.kind === 'rewind' ? t('rw.body', { n: after(confirm.m) }) : t('dl.body')}
            actions={[
              <K.Button key="c" variant="ghost" onClick={() => setConfirm(null)}>{t('rw.cancel')}</K.Button>,
              <K.Button key="g" variant="danger" onClick={() => {
                const { kind, m } = confirm
                setConfirm(null)
                ;(kind === 'rewind' ? api(`/messages/${m.id}/rewind`, 'POST') : api(`/messages/${m.id}`, 'DELETE')).then(reload)
              }}>{t(confirm.kind === 'rewind' ? 'rw.go' : 'dl.go')}</K.Button>,
            ]} />
        </Overlay>
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

/** A story that isn't there any more (deleted in another window, an old link): say so and go Home (M3 › toast.notFound). */
function Gone() {
  const navigate = useNavigate()
  useEffect(() => { toast(t('toast.notFound'), { icon: 'alert' }, 6000); navigate('/home', { replace: true }) }, []) // eslint-disable-line react-hooks/exhaustive-deps
  return null
}
