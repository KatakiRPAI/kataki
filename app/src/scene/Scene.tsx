// The Scene (P1, P9, P19): docs/handoff/kataki-handoff/SCENE.md. Lines, the composer, a reply
// streaming in, Stop, Try again, the cast and the clock. Takes, edits, modes, widgets editing,
// time and Backstage come back in slice 4 of docs/specs/2026-09-28-handoff-3.md.
import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { api, stream, type Cast, type CastEntity, type Message, type Story, type TurnMeta } from '../api'
import { K } from '../ds'
import { face, fullTime, scenery, twelve, useLibrary, useLoad } from '../hooks'
import { pacer, SPEEDS, type Speed } from '../pace'
import { t } from '../strings'

type Live = { speaker: string; speakerId: number | null; text: string; thoughtAt?: number; thinkMs?: number }
type Answer = 'any' | 'narrator' | `${number}`
const COLOURS = ['mike', 'theo', '4', '5', '6']

export default function Scene() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const { byId } = useLibrary()
  const [prefs] = useLoad(() => api<{ reply_speed?: Speed }>('/settings'), [])
  const [data, reload, error] = useLoad(
    () => Promise.all([api<Story>(`/stories/${id}`), api<Message[]>(`/stories/${id}/messages`), api<Cast>(`/stories/${id}/cast`)])
      .then(([story, messages, cast]) => ({ story, messages, cast })),
    [id],
  )
  const [live, setLive] = useState<Live | null>(null)
  const [said, setSaid] = useState<string | null>(null)
  const [failed, setFailed] = useState('')
  const [draft, setDraft] = useState('')
  const [advanced, setAdvanced] = useState(false)
  const [answer, setAnswer] = useState<Answer>('any')
  const controller = useRef<AbortController | null>(null)
  const retryBody = useRef<object | null>(null)
  const lines = useRef<HTMLDivElement>(null)

  useEffect(() => () => controller.current?.abort(), []) // leaving the scene stops the reply
  useEffect(() => {
    api(`/stories/${id}/seen`, 'POST').catch(() => {})
  }, [id])
  // Opening a story, and every new line, scrolls to the end.
  useLayoutEffect(() => {
    const el = lines.current?.querySelector('.k-chat__lines')
    if (el) el.scrollTop = el.scrollHeight
  }, [data, live?.text, said, failed])
  // Esc with nothing open goes back up to the Sky (ROUTES.md › Global navigation).
  useEffect(() => {
    const on = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || e.defaultPrevented) return
      if (controller.current) controller.current.abort()
      else if (!document.querySelector('dialog[open], :popover-open')) navigate(-1)
    }
    addEventListener('keydown', on)
    return () => removeEventListener('keydown', on)
  }, [navigate])

  const generate = async (body: object) => {
    retryBody.current = body
    setFailed('')
    const ctl = new AbortController()
    controller.current = ctl
    setLive({ speaker: '', speakerId: null, text: '' })
    const typed = pacer((text) => setLive((l) => l && { ...l, text: l.text + text, thinkMs: l.thinkMs ?? (l.thoughtAt ? performance.now() - l.thoughtAt : undefined) }),
      SPEEDS[prefs?.reply_speed ?? 'normal'] ?? SPEEDS.normal)
    try {
      await stream(`/stories/${id}/turn`, body, (kind, value) => {
        if (kind === 'meta') {
          const meta = value as TurnMeta
          setLive((l) => l && { ...l, speaker: meta.speaker?.name ?? t('scene.narrator'), speakerId: meta.speaker?.id ?? null })
        } else if (kind === 'thought') setLive((l) => l && { ...l, thoughtAt: l.thoughtAt ?? performance.now() })
        else if (kind === 'token') typed.push(value)
        else if (kind === 'error') setFailed(value.message)
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

  const speaker = answer === 'any' ? null : answer === 'narrator' ? 'narrator' : Number(answer)
  const send = (text: string) => {
    if (live) return
    const line = text.trim()
    const narrate = line.startsWith('>')
    const said = narrate ? line.replace(/^>+\s*/, '') : line
    setDraft('')
    if (said) setSaid(said)
    // the user's line is written first; only the reply waits for a model (SCENE.md › A turn)
    generate({ text: said || null, speaker, audience: null, skip: null, narrate })
  }
  const retry = () => generate({ text: null, speaker: (retryBody.current as { speaker?: unknown } | null)?.speaker ?? null })

  if (!data) {
    return (
      <div className="scene">
        <div className="scene__tint" />
        <div className="scene__chat">
          {error ? <K.Alert title={t('scene.wontOpen')}>{error}</K.Alert> : <K.Spinner label={t('scene.label')} />}
        </div>
      </div>
    )
  }

  const { story, messages, cast } = data
  const item = (e: { lib_item_id: number | null }) => (e.lib_item_id ? byId.get(e.lib_item_id) : undefined)
  const persona = story.persona?.name
  const characters = cast.entities.filter((e) => e.is_ai && e.kind === 'character')
  const present = characters.filter((e) => e.present)
  const colour = (speakerId: number | null, role: Message['role']) => {
    if (role === 'user') return 'var(--speaker-liv)'
    const i = characters.findIndex((e) => e.id === speakerId)
    return i < 0 ? 'var(--scene-ink)' : `var(--speaker-${COLOURS[i % COLOURS.length]})`
  }
  const lead = live?.speakerId ? characters.find((e) => e.id === live.speakerId) : present[0]
  const place = story.place ? byId.get(story.place.lib_item_id ?? -1) : undefined
  const art = scenery(place)
  const artSrc = art.src ?? (art.place ? K.ART[art.place]?.src ?? undefined : undefined)
  const offline = /model|reach|connect|provider/i.test(failed)
  const first = messages.length === 0 && !said
  const placeholder = live
    ? t('scene.placeholderAnswering', { name: live.speaker || lead?.name || t('scene.narrator') })
    : first && lead ? t('scene.placeholderFirst', { name: lead.name, persona: persona ?? 'you' })
    : t('scene.placeholder', { persona: persona ?? 'you' })
  const hearing = present.map((e) => { const f = face(item(e), e.name); return { who: f.who, src: f.src } })
  const answers = [
    { id: 'any', label: t('scene.answers.any'), icon: 'users' as const },
    ...present.map((e) => ({ id: String(e.id), label: e.name, ...face(item(e), e.name) })),
    { id: 'narrator', label: t('scene.answers.narrator'), icon: 'quill' as const },
  ]

  return (
    <div className="scene">
      {artSrc ? <img className="scene__art" src={artSrc} alt={place?.name ?? ''} /> : <div className="scene__art scene__place" />}
      <div className="scene__tint" />
      <div className="scene__vig" />
      <div className="scene__tl">
        <K.SceneHeader title={story.title} backHref="/home"
          subtitle={persona ? t('scene.subtitle', { persona, book: story.book?.title ?? 'none' }) : t('scene.directing')} />
      </div>
      <div className="scene__tr">
        <K.BackstageToggle />
        <K.SceneButton icon="search" label={t('scene.search')} />
        <K.SceneButton icon="dots" label={t('scene.menu')} />
      </div>

      <div className="scene__chat" ref={lines}>
        <K.ChatPanel label={t('scene.label')} composer={
          <K.Composer value={draft} onChange={setDraft} onSend={send} placeholder={placeholder}
            streaming={!!live} onStop={() => controller.current?.abort()} onContinue={() => send('')}
            advanced={advanced} onAdvanced={setAdvanced}
            hearing={hearing} hearingText={present.length ? t('scene.hearingAll') : undefined}
            answers={answers} answer={answer} onAnswer={(a) => setAnswer(a as Answer)} />
        }>
          {story.place && <K.TitleCard>{`${story.place.name} · ${story.date}`}</K.TitleCard>}
          {messages.filter((m) => !m.hidden && m.text).map((m) => (
            <K.ChatLine key={m.id} speaker={String(m.speaker_id ?? m.role)} color={colour(m.speaker_id, m.role)}
              name={m.role === 'user' ? (persona ?? t('scene.narrator')) : (m.speaker ?? t('scene.narrator'))}
              time={twelve(m.clock)} exact={m.clock.slice(-5)} timeDetail={fullTime(m.clock, m.date)} text={m.text}
              take={m.swipe[1] > 1 ? `${m.swipe[0]}/${m.swipe[1]}` : undefined}
              thought={m.think_ms ? t('scene.thought', { s: Math.round(m.think_ms / 1000) }) : undefined} />
          ))}
          {said && <K.ChatLine speaker="user" color="var(--speaker-liv)" name={persona ?? t('scene.narrator')} time="" text={said} />}
          {live && (
            <K.ChatLine speaker={String(live.speakerId)} color={colour(live.speakerId, 'assistant')} name={live.speaker || '…'} time=""
              text={live.text} writing thought={live.thinkMs ? t('scene.thought', { s: Math.round(live.thinkMs / 1000) }) : undefined} />
          )}
          {failed && (
            <div className="lineerr" role="alert">
              <K.Icon name="alert" size={18} color="var(--bad)" />
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <b style={{ fontSize: 14 }}>{t(offline ? 'scene.err.offline' : 'scene.err.title')}</b>
                <span className="scene-t">{failed}</span>
                <div className="row" style={{ gap: 8 }}>
                  <button type="button" className="k-btn k-btn--scene-send" onClick={retry}>{t('scene.err.retry')}</button>
                  {offline && <a className="k-btn k-btn--scene-ghost" href="/settings/models">{t('scene.err.models')}</a>}
                </div>
              </div>
            </div>
          )}
        </K.ChatPanel>
      </div>

      <div className="scene__right">
        {present.map((e: CastEntity) => {
          const f = face(item(e), e.name)
          return (
            <K.CharacterWidget key={e.id} who={f.who ?? ''} src={f.src} name={e.name}
              thinking={live?.speakerId === e.id && !live.text} status={t('scene.here')} />
          )
        })}
      </div>
      <div className="scene__left">
        <K.ClockWidget time={twelve(story.clock)} rel={story.date} place={story.place?.name ?? ''}
          exact={story.clock.slice(-5)} detail={fullTime(story.clock, story.date)}
          kind={story.minute_of_day >= 1200 || story.minute_of_day < 360 ? 'night' : 'dusk'} />
      </div>
    </div>
  )
}
