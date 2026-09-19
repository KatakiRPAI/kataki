import { useId, useState, type CSSProperties } from 'react'
import { api, type Item, type StorySummary } from '../api'
import { Avatar, Figure, Orb, paletteOf, Room } from '../art'
import { href, useLibrary, useLoad } from '../hooks'
import { ErrorLine, Icon, Prose } from '../ui'
import Friends from './Friends'

type Settings = { persona?: number | null }

const greeting = (hour = new Date().getHours()) =>
  hour >= 5 && hour < 12 ? 'Good morning' : hour >= 12 && hour < 17 ? 'Good afternoon' : 'Good evening'

/** The choice of who you are in new chats: each persona, the director, or a new persona. */
export function PersonaChoices({ current, personas, onPick, big = false }: {
  current?: Item
  personas: Item[]
  onPick: (id: number | null) => void
  big?: boolean
}) {
  const size = big ? 48 : 40
  return (
    <div className="ka-choices">
      {personas.map((p) => (
        <button key={p.id} type="button" className="ka-choice" aria-pressed={p.id === current?.id} onClick={() => onPick(p.id)}>
          <Avatar item={p} size={size} />
          <span className="ka-stack ka-stack--tight">
            <strong>{p.name}</strong>
            {p.description && <span className="ka-muted ka-small">{p.description.split('\n')[0]}</span>}
          </span>
          {p.id === current?.id && <Icon name="check" size={18} />}
        </button>
      ))}
      <button type="button" className="ka-choice" aria-pressed={!current} onClick={() => onPick(null)}>
        <span className="ka-choice__tile" style={{ width: size, height: size }}><Icon name="quill" size={20} /></span>
        <span className="ka-stack ka-stack--tight">
          <strong>Director</strong>
          <span className="ka-muted ka-small">Play no one. Direct the story.</span>
        </span>
        {!current && <Icon name="check" size={18} />}
      </button>
      <a className="ka-choice ka-choice--new" href={href('/you/new')}>
        <span className="ka-choice__tile ka-choice__tile--new" style={{ width: size, height: size }}><Icon name="plus" size={20} /></span>
        <strong>New persona</strong>
      </a>
      <span className="ka-muted ka-small ka-choice__note">
        Each chat keeps the persona it started with. Characters know each of your personas separately.
      </span>
    </div>
  )
}

/** Your avatar, which opens the choice of who you are in new chats. */
export function PersonaSwitcher({ current, personas, onPick }: {
  current?: Item
  personas: Item[]
  onPick: (id: number | null) => void
}) {
  const id = useId()
  return (
    <>
      <button type="button" className="ka-me" popoverTarget={id} aria-label={`You are ${current?.name ?? 'the director'}. Switch who you are`}>
        <Avatar item={current} name={current?.name ?? 'Director'} size={62} className="k-avatar--ring" />
        <span className="ka-me__badge"><Icon name="swap" size={12} /></span>
      </button>
      <div id={id} popover="auto" className="ka-menu ka-switcher">
        <span className="k-eyebrow ka-eyebrow">Who are you in new chats?</span>
        <PersonaChoices
          current={current}
          personas={personas}
          onPick={(value) => {
            onPick(value)
            document.getElementById(id)?.hidePopover()
          }}
        />
      </div>
    </>
  )
}

/** The story you played last, as a still you can dive back into. */
function Continue({ story, byId }: { story: StorySummary; byId: Map<number, Item> }) {
  const lib = (libId: number | null) => byId.get(libId ?? -1)
  const speaker = story.cast.find((c) => c.name === story.last_line?.speaker)
  const shown = speaker ?? story.cast.find((c) => c.present) ?? story.cast[0]
  const persona = story.last_line?.speaker === story.persona?.name
  const ink = persona ? 'var(--k-speaker-aren)' : paletteOf(lib(speaker?.lib_item_id ?? null), speaker?.name).ink
  const here = story.cast.filter((c) => c.present).map((c) => c.name)
  const meta = [story.place?.name, story.clock, here.length ? `with ${here.join(' and ')}` : '', story.persona ? `as ${story.persona.name}` : 'directing']
  return (
    <section className="k-continue ka-continue" aria-label="Continue your last scene">
      <Room item={lib(story.place?.lib_item_id ?? null)} minute={story.minute_of_day} />
      {shown && <Figure item={lib(shown.lib_item_id)} name={shown.name} className="ka-continue__figure" />}
      <span className="k-continue__scrim" />
      <div className="ka-continue__text">
        <span className="ka-glass-chip">
          <Icon name="spark" size={13} />
          Continue
        </span>
        <span className="ka-continue__title">{story.title}</span>
        <span className="ka-continue__meta">{meta.filter(Boolean).join(' · ')}</span>
        {story.last_line && (
          <div className="ka-continue__line">
            {story.last_line.speaker && <span className="ka-continue__who" style={{ color: ink } as CSSProperties}>{story.last_line.speaker}</span>}
            <Prose text={story.last_line.text} />
          </div>
        )}
      </div>
      {/* until the Scene lands (task 20), stories open in the classic view */}
      <a className="ka-continue__dive" href={href('/classic')}>
        Dive back in
        <Orb size={74} />
      </a>
    </section>
  )
}

/** Friends, stories and places whose words match. */
function Results({ q, items, stories }: { q: string; items: Item[]; stories: StorySummary[] }) {
  const has = (...texts: (string | undefined)[]) => texts.some((t) => t?.toLowerCase().includes(q.toLowerCase()))
  const friends = items.filter((i) => i.kind === 'character' && !i.data.persona && has(i.name, i.description, ...(i.data.aliases ?? []), ...i.tags))
  const chats = stories.filter((s) => has(s.title, s.place?.name, s.last_line?.text, ...s.cast.map((c) => c.name)))
  const places = items.filter((i) => i.kind === 'place' && has(i.name, i.description, ...(i.data.aliases ?? [])))
  const byLib = new Map(items.map((i) => [i.id, i]))
  if (!friends.length && !chats.length && !places.length)
    return <p className="ka-muted">Nothing matches “{q}”.</p>
  return (
    <section className="k-glass ka-results" aria-label="Search results">
      {friends.length > 0 && <h2 className="k-eyebrow ka-eyebrow">Friends</h2>}
      {friends.map((f) => (
        <a key={f.id} className="ka-result" href={href(`/friend/${f.id}`)}>
          <Avatar item={f} size={40} />
          <span className="ka-stack ka-stack--tight"><strong>{f.name}</strong><span className="ka-muted ka-small">{f.description.split('\n')[0]}</span></span>
        </a>
      ))}
      {chats.length > 0 && <h2 className="k-eyebrow ka-eyebrow">Stories</h2>}
      {chats.map((s) => (
        <a key={s.id} className="ka-result" href={href(`/chats/${s.id}`)}>
          <Avatar item={byLib.get(s.cast[0]?.lib_item_id ?? -1)} name={s.cast[0]?.name ?? s.title} size={40} />
          <span className="ka-stack ka-stack--tight"><strong>{s.title}</strong><span className="ka-muted ka-small">{[s.place?.name, s.clock].filter(Boolean).join(' · ')}</span></span>
        </a>
      ))}
      {places.length > 0 && <h2 className="k-eyebrow ka-eyebrow">Places</h2>}
      {places.map((p) => (
        <a key={p.id} className="ka-result" href={href('/places')}>
          <span className="ka-result__room"><Room item={p} minute={1140} /></span>
          <span className="ka-stack ka-stack--tight"><strong>{p.name}</strong><span className="ka-muted ka-small">{p.description.split('\n')[0]}</span></span>
        </a>
      ))}
    </section>
  )
}

export default function Home() {
  const { items, byId } = useLibrary()
  const [settings, reloadSettings, settingsError] = useLoad(() => api<Settings>('/settings'), [])
  const [stories, , storiesError] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [q, setQ] = useState('')
  const [error, setError] = useState('')

  const personas = items.filter((i) => i.kind === 'character' && i.data.persona).sort((a, b) => a.id - b.id)
  const me = personas.find((p) => p.id === settings?.persona)
  const last = [...(stories ?? [])].sort((a, b) => b.last_at.localeCompare(a.last_at))[0]
  const pick = (persona: number | null) =>
    api('/settings', 'PUT', { persona }).then(reloadSettings, (e: Error) => setError(e.message))

  return (
    <>
      <header className="ka-home-head">
        <div className="ka-row ka-row--gap16">
          <PersonaSwitcher current={me} personas={personas} onPick={pick} />
          <span className="ka-stack ka-stack--tight">
            <span className="ka-home-head__hello">{greeting()},</span>
            <span className="k-display ka-home-head__name">{me?.name ?? 'Director'}</span>
          </span>
        </div>
        <div className="ka-row ka-row--gap">
          <label className="k-search k-glass ka-search">
            <Icon name="search" />
            <span className="k-sr">Search</span>
            <input type="search" placeholder="Search friends, stories, places" value={q} onChange={(e) => setQ(e.target.value)} />
          </label>
          <a className="k-btn k-btn--dark k-btn--lg" href={href('/friends/new')}>
            <Icon name="plus" size={17} />
            Add a friend
          </a>
        </div>
      </header>
      <ErrorLine error={error || settingsError || storiesError} />
      {q.trim() ? (
        <Results q={q.trim()} items={items} stories={stories ?? []} />
      ) : (
        <>
          {last && <Continue story={last} byId={byId} />}
          <section className="ka-stack ka-stack--18" aria-label="Friends">
            <Friends section />
          </section>
        </>
      )}
    </>
  )
}
