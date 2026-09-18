import { useEffect, useRef, useState } from 'react'
import { api, stream, type Cast, type Item, type Message, type Story } from './api'
import Inspector from './Inspector'
import { ErrorLine, Prose, useAction, useLoad } from './ui'

type Live = { speaker: string; text: string; thoughts: string }
type Meter = { est_tokens: number; budget: number; reserve: number; recalled: number }
type Speaker = 'auto' | 'narrator' | number

const UNITS: [number, string][] = [
  [525600, 'year'], [43200, 'month'], [10080, 'week'], [1440, 'day'], [60, 'hour'], [1, 'minute'],
]

function duration(minutes: number): string {
  const [size, name] = UNITS.find(([u]) => minutes >= u) ?? [1, 'minute']
  const n = Math.round(minutes / size)
  return `${n} ${name}${n === 1 ? '' : 's'}`
}

export default function StoryView({ id, onDeleted }: { id: number; onDeleted: () => void }) {
  const [story, reloadStory] = useLoad(() => api<Story>(`/stories/${id}`), [id])
  const [cast, reloadCast] = useLoad(() => api<Cast>(`/stories/${id}/cast`), [id])
  const [messages, setMessages] = useState<Message[]>([])
  const [live, setLive] = useState<Live | null>(null)
  const [said, setSaid] = useState<string | null>(null) // the user's line, shown before the engine confirms it
  const [meter, setMeter] = useState<Meter | null>(null)
  const [error, setError] = useState('')
  const [tick, setTick] = useState(0) // tells the inspector to look again
  const [text, setText] = useState('')
  const [speaker, setSpeaker] = useState<Speaker>('auto')
  const controller = useRef<AbortController | null>(null)
  const end = useRef<HTMLDivElement>(null)

  const loadMessages = () => api<Message[]>(`/stories/${id}/messages`).then(setMessages, (e: Error) => setError(e.message))
  useEffect(() => {
    loadMessages()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])
  useEffect(() => {
    // a block, not an expression: scrollIntoView() returns a Promise in current Chromium, and
    // React treats whatever an effect returns as its cleanup function
    end.current?.scrollIntoView({ block: 'end' })
  }, [messages.length, live?.text])

  const refresh = () => {
    loadMessages()
    reloadCast()
    reloadStory()
    setTick((t) => t + 1)
  }

  const generate = async (path: string, body: unknown) => {
    setError('')
    const ctl = new AbortController()
    controller.current = ctl
    setLive({ speaker: '…', text: '', thoughts: '' })
    try {
      await stream(
        path,
        body,
        (kind, data) => {
          if (kind === 'meta') {
            setLive((l) => l && { ...l, speaker: data.speaker?.name ?? 'Narrator' })
            setMeter(data.context)
          } else if (kind === 'token') setLive((l) => l && { ...l, text: l.text + data })
          else if (kind === 'thought') setLive((l) => l && { ...l, thoughts: l.thoughts + data })
          else if (kind === 'error') setError(data.message)
        },
        ctl.signal,
      )
    } catch (e) {
      if (!ctl.signal.aborted) setError((e as Error).message)
    } finally {
      controller.current = null
      // a stopped reply is saved by the engine a moment after the connection closes
      if (ctl.signal.aborted) await new Promise((r) => setTimeout(r, 400))
      setLive(null)
      setSaid(null)
      refresh()
    }
  }

  const send = (line: string | null) => {
    if (live) return
    setSaid(line)
    setText('')
    generate(`/stories/${id}/turn`, { text: line, speaker: speaker === 'auto' ? null : speaker })
  }

  const persona = cast?.entities.find((e) => e.persona)
  const voices = cast?.entities.filter((e) => e.kind === 'character' && e.is_ai && e.present) ?? []
  const lastId = messages.at(-1)?.id

  return (
    <div className="story">
      <section className="chat" aria-label="Story">
        <header className="row">
          <h1 style={{ margin: 0 }}>{story?.title}</h1>
          <small>{story?.clock}</small>
          <span className="spacer" />
          <button
            className="link danger"
            onClick={() => {
              if (confirm(`Delete "${story?.title}" and everything it remembers? This cannot be undone.`))
                api(`/stories/${id}`, 'DELETE').then(onDeleted, (e: Error) => setError(e.message))
            }}
          >
            Delete story
          </button>
        </header>
        <div className="messages">
          {messages.length === 0 && !live && <p className="muted">The story has not started. Say something, or press Continue.</p>}
          {messages.map((m) => (
            <MessageView
              key={m.id}
              m={m}
              last={m.id === lastId}
              busy={!!live}
              storyId={id}
              onMessages={(ms) => {
                setMessages(ms)
                setTick((t) => t + 1)
              }}
              onRegenerate={() => generate(`/stories/${id}/regenerate`, {})}
            />
          ))}
          {said && (
            <article className="msg user">
              <span className="who">{persona?.name ?? 'You'}</span>
              <div className="body"><Prose text={said} /></div>
            </article>
          )}
          {live && (
            <article className="msg assistant" aria-live="polite">
              <span className="who">{live.speaker}</span>
              <div className="body">
                {live.thoughts && (
                  <details>
                    <summary>Thinking…</summary>
                    <pre>{live.thoughts}</pre>
                  </details>
                )}
                {live.text ? <Prose text={live.text} /> : <p className="muted">…</p>}
              </div>
            </article>
          )}
          <div ref={end} />
        </div>
        <div className="composer">
          <ErrorLine error={error} />
          {meter && (
            <div title={`${meter.est_tokens} of ${meter.budget} tokens, ${meter.reserve} kept free for the reply`}>
              <div className="meter" aria-hidden="true">
                <span style={{ width: `${(100 * meter.est_tokens) / meter.budget}%` }} />
                <span className="reserve" style={{ width: `${(100 * meter.reserve) / meter.budget}%` }} />
              </div>
              <small>
                ~{meter.est_tokens.toLocaleString()} / {meter.budget.toLocaleString()} tokens · {meter.recalled} memor
                {meter.recalled === 1 ? 'y' : 'ies'} recalled
              </small>
            </div>
          )}
          <textarea
            rows={3}
            value={text}
            aria-label="Your line"
            placeholder={persona ? `Speak or act as ${persona.name}… (Enter sends, Shift+Enter for a new line)` : 'Direct the story…'}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && text.trim()) {
                e.preventDefault()
                send(text.trim())
              }
            }}
          />
          <div className="row">
            <label className="row" style={{ display: 'flex' }}>
              Reply from
              <select value={String(speaker)} onChange={(e) => setSpeaker(e.target.value === 'auto' || e.target.value === 'narrator' ? e.target.value : Number(e.target.value))}>
                <option value="auto">Whoever fits</option>
                <option value="narrator">The narrator</option>
                {voices.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
              </select>
            </label>
            <span className="spacer" />
            <button onClick={() => send(null)} disabled={!!live}>Continue</button>
            {live ? (
              <button className="danger" onClick={() => controller.current?.abort()}>Stop</button>
            ) : (
              <button className="primary" onClick={() => text.trim() && send(text.trim())} disabled={!text.trim()}>Send</button>
            )}
          </div>
        </div>
      </section>
      <aside className="side" aria-label="Scene and memory">
        {cast && <ScenePanel storyId={id} cast={cast} clock={story?.clock ?? ''} onChanged={refresh} />}
        <Inspector storyId={id} cast={cast} tick={tick} />
      </aside>
    </div>
  )
}

function MessageView({
  m,
  last,
  busy,
  storyId,
  onMessages,
  onRegenerate,
}: {
  m: Message
  last: boolean
  busy: boolean
  storyId: number
  onMessages: (ms: Message[]) => void
  onRegenerate: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(m.text)
  const [run, error] = useAction()
  const patch = (body: object) => run(async () => onMessages(await api<Message[]>(`/messages/${m.id}`, 'PATCH', body)))
  const swipe = (step: 1 | -1) =>
    run(async () => onMessages(await api<Message[]>(`/stories/${storyId}/swipe`, 'POST', { message_id: m.id, step })))
  const [index, count] = m.swipe
  const canRetake = last && m.role === 'assistant' && m.parent_id !== null

  if (m.role === 'system')
    return (
      <article className="msg system">
        <div className="body">{m.text}</div>
      </article>
    )

  return (
    <article className={`msg ${m.role}${m.hidden ? ' hidden' : ''}`}>
      <div>
        <span className="who">{m.speaker ?? (m.role === 'user' ? 'You' : 'Narrator')}</span>
        <small>{m.clock}</small>
      </div>
      <div className="body">
        {editing ? (
          <div className="stack">
            <textarea rows={Math.min(12, draft.split('\n').length + 2)} value={draft} onChange={(e) => setDraft(e.target.value)} />
            <div className="row">
              <button className="primary" onClick={() => { patch({ text: draft }); setEditing(false) }}>Save</button>
              <button onClick={() => { setDraft(m.text); setEditing(false) }}>Cancel</button>
            </div>
          </div>
        ) : (
          <Prose text={m.text} />
        )}
        {m.reasoning && (
          <details>
            <summary>Thoughts</summary>
            <pre>{m.reasoning}</pre>
          </details>
        )}
      </div>
      <div className="tools">
        {m.skip_minutes > 0 && (
          <span className="chip">
            {duration(m.skip_minutes)} later
            <button className="link" onClick={() => patch({ skip_minutes: 0 })} title="This line did not skip time">undo</button>
          </span>
        )}
        {m.finish === 'stopped' && <span className="chip">stopped</span>}
        {m.edited && <span className="chip">edited</span>}
        {(count > 1 || canRetake) && (
          <span className="row" style={{ gap: 0 }}>
            <button className="link" aria-label="Previous take" disabled={busy || count < 2} onClick={() => swipe(-1)}>‹</button>
            <small>{index}/{count}</small>
            <button
              className="link"
              aria-label={canRetake && index === count ? 'New take' : 'Next take'}
              disabled={busy || (count < 2 && !canRetake)}
              onClick={() => (canRetake && index === count ? onRegenerate() : swipe(1))}
            >
              ›
            </button>
          </span>
        )}
        <span className="spacer" />
        <button className="link" disabled={busy} onClick={() => setEditing(true)}>Edit</button>
        <button className="link" disabled={busy} onClick={() => patch({ hidden: !m.hidden })} title="Hidden lines stay in the story but never reach the model">
          {m.hidden ? 'Unhide' : 'Hide'}
        </button>
      </div>
      <ErrorLine error={error} />
    </article>
  )
}

function ScenePanel({ storyId, cast, clock, onChanged }: { storyId: number; cast: Cast; clock: string; onChanged: () => void }) {
  const [run, error, busy] = useAction()
  const [library] = useLoad(() => api<Item[]>('/library'), [])
  const [place, setPlace] = useState('')
  const [title, setTitle] = useState('')
  const [who, setWho] = useState<number[]>([])
  const characters = cast.entities.filter((e) => e.kind === 'character')
  const here = cast.entities.find((e) => e.id === cast.scene?.place_id)

  return (
    <section className="stack">
      <h3>Scene</h3>
      <div>
        <strong>{cast.scene?.title ?? here?.name ?? 'Somewhere'}</strong> <small>{clock}</small>
      </div>
      {characters.map((c) => (
        <label key={c.id} className="check">
          <input
            type="checkbox"
            checked={c.present}
            disabled={busy}
            onChange={(e) =>
              run(async () => {
                await api(`/stories/${storyId}/presence`, 'POST', { entity_id: c.id, present: e.target.checked })
                onChanged()
              })
            }
          />
          {c.name} {c.persona && <small>(you)</small>} {!c.present && <small>away: hears nothing said here</small>}
        </label>
      ))}
      <label>
        Someone new joins
        <select
          value=""
          onChange={(e) =>
            e.target.value &&
            run(async () => {
              await api(`/stories/${storyId}/cast`, 'POST', { library_id: Number(e.target.value) })
              onChanged()
            })
          }
        >
          <option value="">Pick from the library…</option>
          {library?.filter((i) => i.kind === 'character' && !characters.some((c) => c.name === i.name)).map((i) => (
            <option key={i.id} value={i.id}>{i.name}</option>
          ))}
        </select>
      </label>
      <details>
        <summary>New scene</summary>
        <form
          className="stack"
          style={{ marginTop: '0.5rem' }}
          onSubmit={(e) => {
            e.preventDefault()
            const [source, placeId] = place.split(':')
            run(async () => {
              await api(`/stories/${storyId}/scene`, 'POST', {
                present: who,
                title: title || null,
                place_id: source === 'story' ? Number(placeId) : null,
                library_place_id: source === 'library' ? Number(placeId) : null,
              })
              setTitle('')
              setWho([])
              onChanged()
            })
          }}
        >
          <label>
            Where
            <select value={place} onChange={(e) => setPlace(e.target.value)}>
              <option value="">Unnamed place</option>
              {cast.entities.filter((e) => e.kind === 'place').map((p) => <option key={p.id} value={`story:${p.id}`}>{p.name}</option>)}
              {library?.filter((i) => i.kind === 'place' && !cast.entities.some((e) => e.name === i.name)).map((i) => (
                <option key={i.id} value={`library:${i.id}`}>{i.name} (from the library)</option>
              ))}
            </select>
          </label>
          <label>Title (optional)<input value={title} onChange={(e) => setTitle(e.target.value)} /></label>
          {characters.map((c) => (
            <label key={c.id} className="check">
              <input type="checkbox" checked={who.includes(c.id)} onChange={() => setWho((w) => (w.includes(c.id) ? w.filter((x) => x !== c.id) : [...w, c.id]))} />
              {c.name}
            </label>
          ))}
          <button className="primary" disabled={busy}>Cut to the new scene</button>
        </form>
      </details>
      <ErrorLine error={error} />
    </section>
  )
}
