import { useState } from 'react'
import { api, type StorySummary } from '../api'
import { Avatar, AvatarStack, Figure, Orb, Room } from '../art'
import { go, href, useAction, useLibrary, useLoad } from '../hooks'
import { Chip, Dialog, ErrorLine, Icon, Menu } from '../ui'

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
  const [filter, setFilter] = useState<Filter>('all')
  const [deleting, setDeleting] = useState<StorySummary>()
  const [run, actionError, busy] = useAction()

  const all = stories ?? []
  const shown = all.filter((s) => filter === 'all' || (filter === 'one' ? s.cast.length === 1 : s.cast.length >= 2))
  const current = all.find((s) => s.id === selected) ?? all[0]
  const people = (s: StorySummary) => s.cast.map((c) => ({ item: byId.get(c.lib_item_id ?? -1), name: c.name }))

  const pin = (s: StorySummary) =>
    run(async () => {
      await api(`/stories/${s.id}`, 'PATCH', { pinned: !s.pinned })
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
            <span className="ka-thread__clock">{s.clock}</span>
          </span>
          <span className="ka-thread__line">{preview(s)}</span>
          <span className="ka-thread__as">{playing(s)}</span>
        </span>
        <Menu label={`More for ${s.title}`} className="k-btn k-btn--ghost k-btn--sm ka-thread__menu">
          <button type="button" onClick={() => pin(s)}>
            <Icon name="pushpin" />
            {s.pinned ? 'Unpin' : 'Pin to the top'}
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

  return (
    <div className="ka-chats">
      <section className="k-glass ka-chats__list" aria-label="Stories">
        <h1 className="k-display ka-page-title">Chats</h1>
        <div className="ka-row" role="group" aria-label="Show">
          <Chip pressed={filter === 'all'} onClick={() => setFilter('all')}>All</Chip>
          <Chip pressed={filter === 'one'} onClick={() => setFilter('one')}>One-to-one</Chip>
          <Chip pressed={filter === 'group'} onClick={() => setFilter('group')}>Groups</Chip>
        </div>
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
            {/* until the Scene lands (task 20), stories open in the classic view */}
            <a className="ka-still__dive" href={href('/classic')}>
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
                    <span className="ka-person__sub">{c.present ? 'On stage' : 'Away'}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      <Dialog open={!!deleting} onClose={() => setDeleting(undefined)} title="Delete this story?">
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
