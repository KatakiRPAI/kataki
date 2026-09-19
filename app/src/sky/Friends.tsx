import { useState, type CSSProperties } from 'react'
import { api, type Item, type StorySummary } from '../api'
import { Portrait } from '../art'
import { href, useAction, useLibrary, useLoad } from '../hooks'
import { Candy, ErrorLine, Icon, SkyHeader, type CandyColor } from '../ui'
import { completeness } from './Editor'

type Filter = 'all' | 'favourites' | 'in-story' | 'new' | 'groups'

const FILTERS: [Filter, string, string, CandyColor][] = [
  ['all', 'All', 'grid', 'blue'],
  ['favourites', 'Favourites', 'heart', 'pink'],
  ['in-story', 'In a story', 'book', 'purple'],
  ['new', 'New', 'spark', 'green'],
  ['groups', 'Groups', 'users', 'orange'],
]

const WEEK = 7 * 24 * 3600 * 1000
const addedAt = (item: Item) => Date.parse(item.created_at.replace(' ', 'T') + 'Z')

/** The stories a friend is in, most recently played first. */
export const storiesWith = (friend: Item, stories: StorySummary[]) =>
  stories.filter((s) => s.cast.some((c) => c.lib_item_id === friend.id)).sort((a, b) => b.last_at.localeCompare(a.last_at))

/** "At The Gull · Year 7", "Left The Gull · Year 7", "In a story · Day 5", or not in one yet. */
export function status(friend: Item, stories: StorySummary[]): { text: string; idle: boolean } {
  const latest = storiesWith(friend, stories)[0]
  if (!latest) return { text: 'Not in a story yet', idle: true }
  const here = latest.cast.find((c) => c.lib_item_id === friend.id)?.present
  const where = latest.place ? `${here ? 'At' : 'Left'} ${latest.place.name}` : 'In a story'
  return { text: `${where} · ${latest.clock.split(',')[0]}`, idle: false }
}

export default function Friends() {
  const { items, reload, error } = useLibrary()
  const [stories, , storiesError] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [filter, setFilter] = useState<Filter>('all')
  const [run, actionError] = useAction()

  const friends = items.filter((i) => i.kind === 'character' && !i.data.persona).sort((a, b) => a.id - b.id) // oldest friends first
  const shown = friends.filter((f) => {
    const theirs = storiesWith(f, stories ?? [])
    if (filter === 'favourites') return f.data.favourite
    if (filter === 'in-story') return theirs.length > 0
    if (filter === 'new') return Date.now() - addedAt(f) <= WEEK
    if (filter === 'groups') return theirs.some((s) => s.cast.length >= 2)
    return true
  })

  const favourite = (f: Item) =>
    run(async () => {
      await api(`/library/${f.id}`, 'PATCH', { data: { ...f.data, favourite: !f.data.favourite } })
      reload()
    })

  return (
    <>
      <SkyHeader title="Friends">
        <div className="ka-filters" role="group" aria-label="Show">
          {FILTERS.map(([key, label, icon, color]) => (
            <button key={key} type="button" className="k-candy-filter" aria-pressed={filter === key} onClick={() => setFilter(key)}>
              <Candy icon={icon} color={color} />
              {label}
            </button>
          ))}
        </div>
        <a className="k-btn k-btn--dark k-btn--lg" href={href('/friends/new')}>
          <Icon name="plus" size={17} />
          Add a friend
        </a>
      </SkyHeader>
      <ErrorLine error={error || storiesError || actionError} />
      <div className="ka-friends">
        {shown.map((f) => {
          const { text, idle } = status(f, stories ?? [])
          const filled = Math.round(100 * completeness(f))
          return (
            <Portrait key={f.id} item={f} className="k-friend-card ka-friend">
              <a className="ka-friend__link" href={href(`/friend/${f.id}`)} aria-label={`${f.name}: open profile`} />
              <button type="button" className="ka-heart" aria-pressed={!!f.data.favourite} aria-label={`Favourite ${f.name}`} onClick={() => favourite(f)}>
                <Icon name="heart" size={17} />
              </button>
              {filled < 50 && (
                <span className="k-ring ka-friend__ring" style={{ '--p': filled, '--s': '40px' } as CSSProperties} title={`Profile ${filled}% done`}>
                  {filled}
                </span>
              )}
              <div className="k-nameplate">
                <span className="ka-friend__name">{f.name}</span>
                <span className="ka-friend__tagline">{f.description.split('\n')[0] || 'Just added. Finish their profile.'}</span>
                <span className={`ka-friend__status${idle ? ' is-idle' : ''}`}>{text}</span>
              </div>
            </Portrait>
          )
        })}
        {items.length > 0 && shown.length === 0 && filter !== 'all' && <p className="ka-muted">No one here yet.</p>}
        {filter === 'all' && (
          <a className="ka-add-card" href={href('/friends/new')}>
            <Candy icon="plus" size={56} />
            <strong>Add a friend</strong>
            <span>Build a character like a profile, one step at a time</span>
          </a>
        )}
      </div>
    </>
  )
}
