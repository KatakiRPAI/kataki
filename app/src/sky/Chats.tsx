import { useState } from 'react'
import { api, type ActivityEvent, type Book, type Person, type StorySummary } from '../api'
import { Avatar, AvatarStack, Figure, Orb, Room } from '../art'
import { ago, inline, dive, diveLink, exact, go, href, useAction, useArrivals, useLibrary, useLoad } from '../hooks'
import { Chip, Dialog, ErrorLine, Field, Icon, Menu } from '../ui'
import { EventLink } from './Activity'
import Folders, { onShelf } from './Folders'
import NewChat, { type Preset } from './NewChat'

type Filter = 'all' | 'one' | 'group'

/** The last line as a preview: who said it, without the *actions*. */
function preview(s: StorySummary) {
  if (!s.last_line) return 'The story has not started.'
  const tidy = (t: string) => t.replace(/\s+/g, ' ').trim()
  const text = tidy(s.last_line.text.replace(/\*[^*]+\*/g, ' ')) || tidy(s.last_line.text.replace(/\*/g, '')) // all action: keep it
  return s.last_line.speaker ? `${s.last_line.speaker}: ${text}` : text
}

const playing = (s: StorySummary) => (s.persona ? `as ${s.persona.name}` : 'directing')

export default function Chats({ selected }: { selected?: number }) {
  const { byId } = useLibrary()
  const [stories, reload, error] = useLoad(() => api<StorySummary[]>('/stories'), [])
  useArrivals(reload) // a chat brought in from outside lands here
  const [filter, setFilter] = useState<Filter>('all')
  const [deleting, setDeleting] = useState<StorySummary>()
  const [shelving, setShelving] = useState<StorySummary>()
  const [tagging, setTagging] = useState<StorySummary>()
  const [picked, setPicked] = useState<string[]>([]) // a folder's tags, or the one you clicked
  const [books, reloadBooks] = useLoad(() => api<Book[]>('/books'), [])
  const [newChat, setNewChat] = useState<{ preset?: Preset; n: number }>({ n: 0 }) // n remounts the form fresh
  const startNew = (preset: Preset) => setNewChat((c) => ({ preset, n: c.n + 1 }))
  const [run, actionError, busy, forget] = useAction()

  const all = stories ?? []
  const shown = all
    .filter((s) => filter === 'all' || (filter === 'one' ? s.cast.length === 1 : s.cast.length >= 2))
    .filter((s) => onShelf(s.tags, picked))
  const current = all.find((s) => s.id === selected) ?? all[0]
  // What the reader wrote while you were away; the Scene marks a story seen as you play it.
  const [feed] = useLoad(
    () => (current ? api<ActivityEvent[]>(`/activity?story_id=${current.id}&limit=20`) : Promise.resolve([])),
    [current?.id],
  )
  // by story too: picking another chat keeps the last answer until the new one lands
  const since = (feed ?? []).filter((e) => e.new && e.story_id === current?.id).slice(0, 3)
  const [inStory] = useLoad(
    () => (current ? api<Person[]>(`/stories/${current.id}/people`) : Promise.resolve([])),
    [current?.id],
  )
  /** "remembers 38 things about you", when the reader has filed anything about you at all. */
  const remembers = (id: number) => {
    const n = (inStory ?? []).find((p) => p.id === id)?.about_you?.count
    return n ? `remembers ${n} ${n === 1 ? 'thing' : 'things'} about you` : ''
  }
  const people = (s: StorySummary) => s.cast.map((c) => ({ item: byId.get(c.lib_item_id ?? -1), name: c.name }))

  const pin = (s: StorySummary) =>
    run(async () => {
      await api(`/stories/${s.id}`, 'PATCH', { pinned: !s.pinned })
      reload()
    })
  /** Put a story on a shelf — an existing book, a brand new one, or none. */
  const shelve = (s: StorySummary, book_id: number | null) =>
    run(async () => {
      await api(`/stories/${s.id}`, 'PATCH', { book_id })
      setShelving(undefined)
      reloadBooks() // the picker counts each book's stories
      reload()
    })
  /** What a story wears: the shelves it turns up on. */
  const tag = (s: StorySummary, text: string) =>
    run(async () => {
      const tags = [...new Set(text.split(',').map((t) => t.trim()).filter(Boolean))]
      await api(`/stories/${s.id}`, 'PATCH', { tags })
      setTagging(undefined)
      reload()
    })
  const shelveInNew = (s: StorySummary, title: string) =>
    run(async () => {
      const book = await api<Book>('/books', 'POST', { title: title.trim() })
      await api(`/stories/${s.id}`, 'PATCH', { book_id: book.id })
      setShelving(undefined)
      reloadBooks()
      reload()
    })

  const remove = (s: StorySummary) =>
    run(async () => {
      await api(`/stories/${s.id}`, 'DELETE')
      setDeleting(undefined)
      reload()
      go('/chats')
    })

  const row = (s: StorySummary) => {
    const cast = people(s)
    return (
      <li key={s.id} className="ka-thread">
        <a className="ka-thread__link" href={href(`/chats/${s.id}`)} aria-current={s.id === current?.id ? 'true' : undefined} aria-label={s.title} />
        {cast.length > 1 ? <AvatarStack people={cast} size={40} /> : <Avatar item={cast[0]?.item} name={cast[0]?.name ?? s.title} size={48} className="ka-ringed" />}
        <span className="ka-thread__body">
          <span className="ka-thread__top">
            <span className="ka-thread__title">
              <span className="ka-ellipsis">{s.title}</span>
              {s.pinned && <Icon name="pushpin" size={13} />}
            </span>
            <span className="ka-thread__clock" title={exact(s.last_at)}>{ago(s.last_at)}</span>
          </span>
          <span className="ka-thread__mid">
            <span className="ka-thread__line">{preview(s)}</span>
            {s.new_events > 0 && (
              <span className="ka-mem-badge" aria-label={`${s.new_events} new memory event${s.new_events === 1 ? '' : 's'}`}>
                <Icon name="spark" size={11} />
                {s.new_events}
              </span>
            )}
          </span>
          <span className="ka-thread__as">
            {playing(s)} · {inline(s.date)}
            {s.book && (
              <>
                {' · '}
                <a className="ka-thread__book" href={href(`/books/${s.book.id}`)}>{s.book.title}</a>
              </>
            )}
            {s.tags.map((t) => (
              <button key={t} type="button" className="ka-tag-chip" onClick={() => setPicked([t])}
                aria-label={`Show only stories tagged ${t}`}>
                {t}
              </button>
            ))}
          </span>
        </span>
        <Menu label={`More for ${s.title}`} className="k-btn k-btn--ghost k-btn--sm ka-thread__menu">
          <button type="button" onClick={() => pin(s)}>
            <Icon name="pushpin" />
            {s.pinned ? 'Unpin' : 'Pin to the top'}
          </button>
          <button type="button" onClick={() => setShelving(s)}>
            <Icon name="book" />
            {s.book ? 'Move to another book' : 'Put in a book'}
          </button>
          <button type="button" onClick={() => setTagging(s)}>
            <Icon name="filter" />
            Tags…
          </button>
          <button type="button" onClick={() => setDeleting(s)}>
            <Icon name="x" />
            Delete story
          </button>
        </Menu>
      </li>
    )
  }

  const pinned = shown.filter((s) => s.pinned)
  const rest = shown.filter((s) => !s.pinned)
  const speaker = current?.cast.find((c) => c.name === current.last_line?.speaker) ?? current?.cast.find((c) => c.present) ?? current?.cast[0]
  const lead = speaker?.lib_item_id ? speaker : current?.cast.find((c) => c.lib_item_id) // "Start a fresh story with…"

  return (
    <div className="ka-chats">
      <section className="k-glass ka-chats__list" aria-label="Stories">
        <h1 className="k-display ka-page-title">Chats</h1>
        <div className="ka-row ka-row--gap">
          <button type="button" className="k-btn k-btn--dark" onClick={() => startNew({})}>
            <Icon name="plus" size={17} />
            New chat
          </button>
          <button type="button" className="k-btn" onClick={() => startNew({ group: true })}>
            <Icon name="users" size={17} />
            New group scene
          </button>
        </div>
        <div className="ka-row" role="group" aria-label="Show">
          <Chip pressed={filter === 'all'} onClick={() => setFilter('all')}>All</Chip>
          <Chip pressed={filter === 'one'} onClick={() => setFilter('one')}>One-to-one</Chip>
          <Chip pressed={filter === 'group'} onClick={() => setFilter('group')}>Groups</Chip>
        </div>
        <Folders kind="story" wears={all.flatMap((s) => s.tags)} picked={picked} onPick={setPicked} />
        <ErrorLine error={error || actionError} />
        {pinned.length > 0 && (
          <>
            <h2 className="k-eyebrow ka-eyebrow">Pinned</h2>
            <ul className="ka-threads">{pinned.map(row)}</ul>
          </>
        )}
        {rest.length > 0 && (
          <>
            <h2 className="k-eyebrow ka-eyebrow">All stories</h2>
            <ul className="ka-threads">{rest.map(row)}</ul>
          </>
        )}
        {stories && shown.length === 0 && <p className="ka-muted">No stories here yet.</p>}
      </section>

      {current && (
        <section className="k-glass ka-chats__preview" aria-label={current.title}>
          <div className="ka-still">
            <Room item={byId.get(current.place?.lib_item_id ?? -1)} minute={current.minute_of_day} />
            {speaker && <Figure item={byId.get(speaker.lib_item_id ?? -1)} name={speaker.name} className="ka-still__figure" />}
            <span className="ka-still__scrim" />
            <span className="ka-glass-chip ka-still__chip">
              <Icon name="image" size={13} />
              Last moment
            </span>
            <div className="ka-still__text">
              <span className="ka-still__title">{current.title}</span>
              <span className="ka-still__meta">{[current.place?.name, current.clock, playing(current)].filter(Boolean).join(' · ')}</span>
            </div>
            <a className="ka-still__dive" {...diveLink(`/story/${current.id}`)}>
              Dive in
              <Orb size={70} />
            </a>
          </div>
          <div className="ka-chats__details">
            <div className="ka-stack">
              <h2 className="k-eyebrow ka-eyebrow">In this story</h2>
              {current.cast.map((c) => (
                <div key={c.id} className={`ka-person${c.present ? '' : ' is-away'}`}>
                  <Avatar item={byId.get(c.lib_item_id ?? -1)} name={c.name} size={40} />
                  <span className="ka-person__text">
                    <span className="ka-person__name">{c.name}</span>
                    <span className="ka-person__sub">{[c.present ? 'On stage' : 'Away', remembers(c.id)].filter(Boolean).join(' · ')}</span>
                  </span>
                </div>
              ))}
              {lead?.lib_item_id && (
                <button type="button" className="ka-link" onClick={() => startNew({ friends: [lead.lib_item_id!] })}>
                  Start a fresh story with {lead.name}
                </button>
              )}
            </div>
            {since.length > 0 && (
              <div className="ka-stack ka-stack--tight">
                <h2 className="k-eyebrow ka-eyebrow">New since you left</h2>
                {since.map((e) => <EventLink key={e.key} e={e} sub={e.clock} />)}
              </div>
            )}
          </div>
        </section>
      )}

      <NewChat
        key={`chat-${newChat.n}`}
        open={!!newChat.preset}
        preset={newChat.preset ?? {}}
        onClose={() => setNewChat((c) => ({ n: c.n }))}
        onCreated={(story) => {
          setNewChat((c) => ({ n: c.n }))
          reload()
          dive(`/story/${story.id}`)
        }}
      />
      <Dialog open={!!tagging} onClose={() => { setTagging(undefined); forget() }} title={`Tags for “${tagging?.title ?? ''}”`}>
        <form
          className="ka-form"
          onSubmit={(e) => {
            e.preventDefault()
            const text = String(new FormData(e.currentTarget).get('tags') ?? '')
            if (tagging) tag(tagging, text)
          }}
        >
          <Field label="Tags, separated by commas">
            <input name="tags" className="k-input" defaultValue={(tagging?.tags ?? []).join(', ')}
              maxLength={300} placeholder="docks, slow burn" />
          </Field>
          <p className="ka-muted ka-small">A folder gathers everything wearing the tags it is named by.</p>
          <div className="ka-row ka-row--end">
            <button type="button" className="k-btn" onClick={() => setTagging(undefined)}>Cancel</button>
            <button type="submit" className="k-btn k-btn--dark" disabled={busy}>Save the tags</button>
          </div>
        </form>
      </Dialog>

      <Dialog open={!!shelving} onClose={() => { setShelving(undefined); forget() }} title={`Put “${shelving?.title ?? ''}” in a book`}>
        <ul className="ka-threads ka-pick">
          {(books ?? []).map((b) => (
            <li key={b.id}>
              <button
                type="button" className="ka-pick__row" disabled={busy || b.id === shelving?.book?.id}
                onClick={() => shelving && shelve(shelving, b.id)}
              >
                <span className="ka-booklist__spine" aria-hidden="true"><Icon name="book" size={16} /></span>
                <span className="ka-shelf__text">
                  <span className="ka-ellipsis">{b.title}</span>
                  <span className="ka-muted ka-small">
                    {b.id === shelving?.book?.id ? 'already here' : `${b.stories} ${b.stories === 1 ? 'story' : 'stories'}`}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
        <form
          className="ka-row ka-row--gap"
          onSubmit={(e) => {
            e.preventDefault()
            const field = new FormData(e.currentTarget).get('title')
            const title = String(field ?? '').trim()
            if (title && shelving) shelveInNew(shelving, title)
          }}
        >
          <input name="title" className="k-input" placeholder="Or start a new book…" maxLength={200} aria-label="New book title" />
          <button type="submit" className="k-btn k-btn--dark" disabled={busy}>
            <Icon name="plus" size={16} />
            New book
          </button>
        </form>
        {shelving?.book && (
          <button type="button" className="ka-link" disabled={busy} onClick={() => shelving && shelve(shelving, null)}>
            Take it out of {shelving.book.title}
          </button>
        )}
      </Dialog>

      <Dialog open={!!deleting} onClose={() => { setDeleting(undefined); forget() }} title="Delete this story?">
        <p className="ka-muted">
          “{deleting?.title}” and everything its characters remember of it will be gone. This can't be undone.
        </p>
        <div className="ka-row ka-row--end">
          <button type="button" className="k-btn" onClick={() => setDeleting(undefined)}>Keep it</button>
          <button type="button" className="k-btn k-btn--dark" disabled={busy} onClick={() => deleting && remove(deleting)}>Delete story</button>
        </div>
      </Dialog>
    </div>
  )
}
