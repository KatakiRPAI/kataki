// New story (G1–G4): docs/handoff/kataki-handoff/SCREENS.md › /stories/new.
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { api, type Book, type Cast, type Item, type Story, type StorySummary } from '../api'
import { K } from '../ds'
import { face, scenery, useLibrary, useLoad, utc } from '../hooks'
import { fullName, isDraft, storiesWith, tagline } from '../characters'
import { Overlay } from '../overlay'
import { t, type Key } from '../strings'

type Presence = 'here' | 'later' | 'no'
type Time = 'dawn' | 'day' | 'dusk' | 'night'
const TIMES: Time[] = ['dawn', 'day', 'dusk', 'night']
const START: Record<Time, number> = { dawn: 390, day: 720, dusk: 1110, night: 1320 } // minutes into Day 1
const PRESENCE: Presence[] = ['here', 'later', 'no']
const presenceLabel = (p: Presence) => t(p === 'here' ? 'ns.presence.here' : p === 'later' ? 'ns.presence.later' : 'ns.presence.no')
const timeLabel = (x: Time) => t(`ns.time.${x}` as Key)
/** A plot's first line, to its first sentence end or about seventy characters. */
const opening = (text = '') => {
  const first = text.replace(/\*/g, '').trim().split(/(?<=[.!?])\s/)[0]
  return first.length <= 70 ? first : first.slice(0, first.lastIndexOf(' ', 70)) + '…'
}
const list = (names: string[]) => new Intl.ListFormat('en', { type: 'conjunction' }).format(names)

export default function NewStory() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { items, byId, reload: reloadLibrary } = useLibrary()
  const [settings] = useLoad(() => api<{ persona?: number }>('/settings'), [])
  const [stories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [books] = useLoad(() => api<Book[]>('/books'), [])

  const [chosen, setChosen] = useState<number[]>(() => (params.get('with') ?? '').split(',').filter(Boolean).map(Number))
  const [presence, setPresence] = useState<Record<number, Presence>>({})
  const [persona, setPersona] = useState<number | null | undefined>() // undefined: the default persona
  const [changing, setChanging] = useState(false)
  const [place, setPlace] = useState<number | 'new' | null>(() => Number(params.get('place')) || null)
  const [fresh, setFresh] = useState({ name: '', like: '', time: 'dusk' as Time, keep: true })
  const [plot, setPlot] = useState<number | null>(() => Number(params.get('plot')) || null)
  const [opens, setOpens] = useState('') // how it opens, without a plot
  const [name, setName] = useState('')
  const [book, setBook] = useState<number | 'none' | 'new'>(() => Number(params.get('book')) || 'none')
  const [bookName, setBookName] = useState('')
  const [finding, setFinding] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  // the most recently played first, as the board has them
  const played = (c: Item) => Math.max(0, ...storiesWith(c, stories).map((s) => utc(s.last_at)))
  const characters = items.filter((i) => i.kind === 'character' && !i.data.persona).sort((a, b) => played(b) - played(a) || a.name.localeCompare(b.name))
  const personas = items.filter((i) => i.kind === 'character' && i.data.persona)
  const places = items.filter((i) => i.kind === 'place' && !i.data.unlisted).sort((a, b) => a.id - b.id) // in the order they were made
  const plots = items.filter((i) => i.kind === 'scenario')
  const me = persona === undefined ? (settings?.persona ? byId.get(settings.persona) : personas[0]) : persona === null ? undefined : byId.get(persona)
  const people = chosen.map((id) => byId.get(id)).filter((i): i is Item => !!i)
  const storiesOf = (c: Item) => (stories ?? []).filter((s) => s.cast.some((x) => x.lib_item_id === c.id)).length
  const suggested = [...people, ...characters.filter((c) => !chosen.includes(c.id))].slice(0, Math.max(5, people.length))
  const where = place === 'new' ? (fresh.name.trim() ? { name: fresh.name.trim() } : undefined) : place ? byId.get(place) : undefined
  const art = place && place !== 'new' ? scenery(byId.get(place)) : {}
  const weekday = new Date().toLocaleDateString('en-GB', { weekday: 'long' })
  const fallback = t('ns.defaultName', { place: where?.name ?? people[0]?.name ?? t('ns.title'), weekday })
  const who = people.length ? list(people.map((p) => p.name)) : t('ns.nobody')
  const bookOptions: [number | 'none' | 'new', string][] = [...(books ?? []).map((b) => [b.id, b.title] as [number, string]), ['none', t('ns.noBook')], ['new', t('ns.newBook')]]
  const toggle = (id: number) => setChosen((c) => (c.includes(id) ? c.filter((x) => x !== id) : [...c, id]))
  const ready = people.length > 0 && (place !== 'new' || !!fresh.name.trim()) && (book !== 'new' || !!bookName.trim()) && !busy

  const start = async () => {
    if (!ready) return
    setBusy(true)
    setError('')
    try {
      let bookId = typeof book === 'number' ? book : null
      if (book === 'new') bookId = (await api<Book>('/books', 'POST', { title: bookName.trim() })).id
      let placeId = typeof place === 'number' ? place : null
      if (place === 'new') {
        const made = await api<Item>('/library', 'POST', {
          kind: 'place', name: fresh.name.trim(), description: fresh.like.trim(),
          data: fresh.keep ? (bookId ? { links: { book: bookId } } : {}) : { unlisted: true },
        })
        placeId = made.id
        reloadLibrary()
      }
      const story = await api<Story>('/stories', 'POST', {
        title: name.trim() || fallback, character_ids: chosen, place_id: placeId, persona_id: me?.id ?? null, scenario_id: plot, first_message: plot ? '' : opens.trim(),
        ...(place === 'new' ? { epoch_offset_min: START[fresh.time] } : {}),
      })
      const away = chosen.filter((id) => (presence[id] ?? 'here') !== 'here')
      if (away.length) {
        const cast = await api<Cast>(`/stories/${story.id}/cast`)
        for (const id of away) {
          const e = cast.entities.find((x) => x.lib_item_id === id)
          if (e) await api(`/stories/${story.id}/presence`, 'POST', { entity_id: e.id, present: false })
        }
      }
      if (bookId) await api(`/stories/${story.id}`, 'PATCH', { book_id: bookId })
      navigate(`/story/${story.id}`)
    } catch (e) {
      setError((e as Error).message)
      setBusy(false)
    }
  }

  return (
    <main className="app__main" aria-label={t('ns.title')} style={{ gap: 24 }}
      onKeyDown={(e) => e.key === 'Escape' && !finding && navigate(-1)}>
      <K.TopBar back={t('ns.back')} backHref="/stories" />
      <div className="pg-head">
        <div>
          <h1 className="pg-title">{t('ns.title')}</h1>
          <p className="pg-sub">{t('ns.sub')}</p>
        </div>
        <K.Button variant="primary" size="lg" disabled={!ready} loading={busy} onClick={start}>{t('ns.start')}</K.Button>
      </div>

      <div className="ns-grid">
        <div className="col" style={{ gap: 22, minWidth: 0 }}>
          <section className="ns-step">
            <K.StepHeader n={1} title={t('ns.who')} />
            <div className="row row--wrap" style={{ gap: 8 }}>
              {suggested.map((c) => {
                const f = face(c)
                return (
                  <K.Chip key={c.id} who={f.who} src={f.src} pressed={chosen.includes(c.id)} onPress={() => toggle(c.id)}>
                    {isDraft(c) ? t('ns.draft', { name: c.name }) : c.name}
                  </K.Chip>
                )
              })}
              <K.Chip icon="search" onClick={() => setFinding(true)}>{t('ns.find')}</K.Chip>
            </div>
            {people.length > 1 && (
              <>
                <K.Callout title={t('ns.group')}>{t('ns.groupBody')}</K.Callout>
                {people.map((p) => (
                  <div key={p.id} className="ns-presence">
                    <span>{p.name}</span>
                    <K.Select label="" options={PRESENCE.map(presenceLabel)} value={presenceLabel(presence[p.id] ?? 'here')}
                      onChange={(v) => setPresence((x) => ({ ...x, [p.id]: PRESENCE.find((q) => presenceLabel(q) === v) ?? 'here' }))} />
                  </div>
                ))}
              </>
            )}
          </section>

          <section className="ns-step">
            <K.StepHeader n={2} title={t('ns.you')} />
            <div className="row row--wrap" style={{ gap: 12 }}>
              {(changing ? [...personas, null] : [me ?? null]).map((p) => {
                const pick = () => { setPersona(p ? p.id : null); setChanging(false) }
                const card = p
                  ? <K.PersonaCard {...face(p)} name={fullName(p)} line={tagline(p)} isDefault={p.id === settings?.persona} selected={p.id === me?.id} />
                  : <K.PersonaCard icon="user" name={t('ns.noPersona')} line={t('ns.noPersonaLine')} selected={!me} />
                return changing
                  ? <button key={p?.id ?? 0} type="button" className="ns-pick" onClick={pick} aria-pressed={p ? p.id === me?.id : !me}>{card}</button>
                  : <div key="me">{card}</div>
              })}
              {!changing && <K.Button size="sm" onClick={() => setChanging(true)}>{t('ns.change')}</K.Button>}
            </div>
          </section>

          <section className="ns-step">
            <K.StepHeader n={3} title={t('ns.where')} optional />
            <div className="row row--wrap" style={{ gap: 8 }}>
              {places.map((p) => (
                <K.Chip key={p.id} icon="map-pin" pressed={place === p.id} onPress={() => setPlace(place === p.id ? null : p.id)}>{p.name}</K.Chip>
              ))}
              <K.Chip icon="plus" pressed={place === 'new'} onPress={() => setPlace(place === 'new' ? null : 'new')}>{t('ns.somewhereNew')}</K.Chip>
            </div>
            {place === 'new' && (
              <div className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 14, background: 'var(--raise)' }}>
                <K.TextField label={t('ns.place.name')} required story value={fresh.name} onChange={(v) => setFresh({ ...fresh, name: v })} />
                <K.TextArea label={t('ns.place.like')} optional story rows={2} value={fresh.like} onChange={(v) => setFresh({ ...fresh, like: v })} />
                <K.Segmented label={t('ns.place.time')} size="sm" options={TIMES.map(timeLabel)} value={timeLabel(fresh.time)}
                  onChange={(v) => setFresh({ ...fresh, time: TIMES.find((x) => timeLabel(x) === v) ?? 'dusk' })} />
                <K.Checkbox label={t('ns.place.keep')} description={t('ns.place.keepSub')} checked={fresh.keep} onChange={(v) => setFresh({ ...fresh, keep: v })} />
              </div>
            )}
          </section>

          <section className="ns-step">
            <K.StepHeader n={4} title={t('ns.what')} optional />
            <div className="ns-plots">
              {plots.map((p) => (
                <button key={p.id} type="button" className="plotpick" aria-pressed={plot === p.id} onClick={() => setPlot(plot === p.id ? null : p.id)}>
                  <span className="plotpick__quote">“{p.description}”</span>
                  <span className="t-meta">{t('ns.plotMeta', { plot: p.name, opening: opening(p.data.first_message) })}</span>
                </button>
              ))}
              <button type="button" className="plotpick" aria-pressed={plot === null} onClick={() => setPlot(null)}>
                <span style={{ fontSize: 14.5, fontWeight: 700 }}>{t('ns.nothing')}</span>
                <span className="t-meta">{t('ns.nothingSub')}</span>
              </button>
            </div>
            {plot === null && <K.TextArea label={t('ns.opens')} optional hint={t('ns.opensHint')} story rows={3} value={opens} onChange={setOpens} />}
          </section>
        </div>

        <aside aria-label={t('ns.scene')} className="card ns-aside">
          <K.Still place={art.place} src={art.src} height={200} alt={where?.name ?? ''} caption={where?.name} />
          <div style={{ padding: '18px 20px 20px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="col" style={{ gap: 4 }}>
              <K.Eyebrow>{t('ns.scene')}</K.Eyebrow>
              <K.StoryName size="card">{name.trim() || fallback}</K.StoryName>
              <span className="t-meta">{me ? t('ns.withYou', { names: who, persona: me.name }) : t('ns.withJustYou', { names: who })}</span>
            </div>
            {people.length > 0 && (
              <div className="col" style={{ gap: 8 }}>
                {people.map((p) => {
                  const f = face(p)
                  return (
                    <div key={p.id} className="row" style={{ gap: 10 }}>
                      <K.Avatar who={f.who} src={f.src} name={p.name} size={26} />
                      <span style={{ fontSize: 13.5 }}><b>{p.name}</b> <span className="t-meta">{t('stories.count', { n: storiesOf(p) })}</span></span>
                    </div>
                  )
                })}
              </div>
            )}
            <K.Select label={t('ns.book')} icon="book" hint={t('ns.bookHint')} options={bookOptions.map(([, l]) => l)}
              value={bookOptions.find(([id]) => id === book)?.[1]} onChange={(v) => setBook(bookOptions.find(([, l]) => l === v)?.[0] ?? 'none')} />
            {book === 'new' && <K.TextField label={t('ns.newBookName')} story value={bookName} onChange={setBookName} />}
            <K.TextField label={t('ns.name')} optional story value={name} onChange={setName} hint={t('ns.nameHint')} max={60} />
            {error && <K.Alert title={t('scene.err.title')}>{error}</K.Alert>}
            <K.Button variant="primary" full size="lg" disabled={!ready} loading={busy} onClick={start}>{t('ns.start')}</K.Button>
          </div>
        </aside>
      </div>

      {finding && (
        <Find characters={characters} personas={personas} me={me?.id} chosen={chosen} storiesOf={storiesOf}
          onClose={() => setFinding(false)} onDone={(ids) => { setChosen(ids); setFinding(false) }} />
      )}
    </main>
  )
}

/** G3: everyone you've made or imported, to pick from. */
function Find({ characters, personas, me, chosen, storiesOf, onClose, onDone }: {
  characters: Item[]; personas: Item[]; me?: number; chosen: number[]; storiesOf: (c: Item) => number
  onClose: () => void; onDone: (ids: number[]) => void
}) {
  const [query, setQuery] = useState('')
  const [picked, setPicked] = useState(chosen)
  const q = query.trim().toLowerCase()
  const everyone = [...characters, ...personas.filter((p) => p.id !== me)].filter((c) => !q || c.name.toLowerCase().includes(q))
  const names = picked.map((id) => [...characters, ...personas].find((c) => c.id === id)?.name).filter((n): n is string => !!n)
  const meItem = personas.find((p) => p.id === me)
  return (
    <Overlay onClose={onClose}>
      <section className="dlg" role="dialog" aria-modal="true" aria-labelledby="find-title">
        <div className="dlg__head">
          <div className="dlg__titles"><h2 className="dlg__title" id="find-title">{t('find.title')}</h2><p className="dlg__desc">{t('find.body')}</p></div>
          <K.IconButton icon="x" label="Close" size="sm" onClick={onClose} />
        </div>
        <div className="dlg__body" style={{ gap: 10 }}>
          <K.SearchField value={query} onChange={setQuery} shortcut={false} label={t('find.search')} placeholder={t('find.search')} />
          <div className="card find-list">
            {[...everyone, ...(meItem && (!q || meItem.name.toLowerCase().includes(q)) ? [meItem] : [])].map((c) => {
              const f = face(c)
              const isMe = c.id === me
              const n = storiesOf(c)
              return (
                <div key={c.id} className="find-row">
                  <K.Avatar who={f.who} src={f.src} name={c.name} size={36} />
                  <div style={{ flex: 1 }}>
                    <K.Checkbox label={c.name} disabled={isMe} checked={picked.includes(c.id)}
                      description={isMe ? t('find.persona') : !c.description.trim() ? t('find.draft') : n ? t('stories.count', { n }) : t('find.never')}
                      onChange={(on) => setPicked((x) => (on ? [...x, c.id] : x.filter((y) => y !== c.id)))} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
        <div className="dlg__foot">
          <span className="dlg__note">{names.length ? list(names) : ''}</span>
          <div className="k-btngroup">
            <K.Button variant="ghost" onClick={onClose}>{t('find.cancel')}</K.Button>
            <K.Button variant="primary" onClick={() => onDone(picked)}>{t('find.done')}</K.Button>
          </div>
        </div>
      </section>
    </Overlay>
  )
}
