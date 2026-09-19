import { useState, type CSSProperties } from 'react'
import { api, type ActivityEvent, type StorySummary } from '../api'
import { Avatar } from '../art'
import { diveLink, useAction, useLibrary, useLoad } from '../hooks'
import { Chip, ErrorLine, Glass, Icon, Prose } from '../ui'

type Kind = ActivityEvent['kind']

// Each kind: the icon on the corner of the face, and the word the filter uses.
const KINDS: [Kind, string, string][] = [
  ['memory', 'spark', 'Memories'],
  ['feeling', 'heart', 'Feelings'],
  ['belief', 'help', 'Beliefs'],
  ['time', 'clock', 'Time'],
]

const iconOf = (kind: Kind) => KINDS.find(([k]) => k === kind)![1]

/** What it was about and when: "Heard by Mira · Tobin wasn't there · Day 1, 19:12". A time skip
 *  already ends on the clock it moved to, and doesn't want it twice. */
const meta = (e: ActivityEvent) => (e.sub.endsWith(e.clock) ? e.sub : [e.sub, e.clock].filter(Boolean).join(' · '))

/** Whoever it happened to, with the kind on the corner. Time happens to no one, so it wears a clock. */
function Face({ e, size }: { e: ActivityEvent; size: number }) {
  const { byId } = useLibrary()
  const who = e.who[0]
  return (
    <span className="ka-event__face">
      {who ? (
        <Avatar item={byId.get(who.lib_item_id ?? -1)} name={who.name} size={size} />
      ) : (
        <span className="ka-event__tile" style={{ '--s': `${size}px` } as CSSProperties}>
          <Icon name="clock" size={Math.round(size * 0.45)} />
        </span>
      )}
      <span className="k-event__kind"><Icon name={iconOf(e.kind)} size={12} /></span>
    </span>
  )
}

/** Where it happened: "The Third Floorboard · Year 7", the feed's group head and Home's sub. */
const where = (e: ActivityEvent) => `${e.story} · ${e.clock.split(',')[0]}`

/** An event as a link straight into the line it came from: Home's preview and the Chats panel,
 *  which names the story or not depending on whether the page already has. */
export function EventLink({ e, size = 44, sub }: { e: ActivityEvent; size?: number; sub?: string }) {
  return (
    <a className={`k-event k-event--${e.kind} ka-event`} {...diveLink(`/story/${e.story_id}/line/${e.message_id}`)}>
      <Face e={e} size={size} />
      <span className="ka-event__text">
        <span className="ka-event__what">{e.text}</span>
        <span className="ka-event__sub">{sub ?? where(e)}</span>
      </span>
    </a>
  )
}

/** An event in the feed: it opens onto the line that caused it, which you can dive into. */
function Event({ e }: { e: ActivityEvent }) {
  const [open, setOpen] = useState(false)
  return (
    <li className={`ka-event-card${open ? ' is-open' : ''}`}>
      <button type="button" className={`k-event k-event--${e.kind} ka-event`} aria-expanded={open} onClick={() => setOpen(!open)}>
        <Face e={e} size={52} />
        <span className="ka-event__text">
          <span className="ka-event__what">
            {e.text}
            {e.new && <span className="ka-event__new">New</span>}
          </span>
          <span className="ka-event__sub">{meta(e)}</span>
        </span>
        <Icon name="right" size={18} />
      </button>
      {open && (
        <div className="ka-quote">
          <span className="ka-quote__who">{[e.line.speaker ?? 'You', e.clock].join(' · ')}</span>
          <Prose text={e.line.text} />
          <a className="ka-quote__open" {...diveLink(`/story/${e.story_id}/line/${e.message_id}`)}>
            Open the line
            <Icon name="arrow" size={14} />
          </a>
        </div>
      )}
    </li>
  )
}

/** Runs of events that share a story and a stretch of story time: "THE THIRD FLOORBOARD · YEAR 7". */
function group(events: ActivityEvent[]): [string, ActivityEvent[]][] {
  const out: [string, ActivityEvent[]][] = []
  for (const e of events) {
    const label = where(e)
    const last = out[out.length - 1]
    if (last && last[0] === label) last[1].push(e)
    else out.push([label, [e]])
  }
  return out
}

export default function Activity() {
  const { items } = useLibrary()
  const [kind, setKind] = useState<Kind | 'all'>('all')
  const [events, reload, error] = useLoad(
    () => api<ActivityEvent[]>(`/activity?limit=100${kind === 'all' ? '' : `&kind=${kind}`}`),
    [kind],
  )
  const [stories, reloadStories, storiesError] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [run, actionError, busy] = useAction()

  const waiting = (stories ?? []).filter((s) => s.waiting > 0)
  const readNow = () =>
    run(async () => {
      await Promise.all(waiting.map((s) => api(`/stories/${s.id}/extract`, 'POST')))
      reloadStories()
      reload()
    })
  const sample = items.find((i) => i.kind === 'character' && !i.data.persona)

  return (
    <div className="ka-activity">
      <section className="ka-activity__main" aria-label="Activity">
        <div className="ka-activity__head">
          <h1 className="k-display ka-page-title">Activity</h1>
          <div className="ka-row ka-row--gap6" role="group" aria-label="Show">
            <Chip pressed={kind === 'all'} onClick={() => setKind('all')}>All</Chip>
            {KINDS.map(([k, icon, label]) => (
              <Chip key={k} pressed={kind === k} icon={icon} onClick={() => setKind(k)}>{label}</Chip>
            ))}
          </div>
        </div>
        <ErrorLine error={error || actionError} />
        {group(events ?? []).map(([label, stretch]) => (
          <div key={label + stretch[0].key} className="ka-stack ka-stack--tight">
            <h2 className="k-eyebrow ka-eyebrow">{label}</h2>
            <ul className="ka-activity__feed">
              {stretch.map((e) => <Event key={e.key} e={e} />)}
            </ul>
          </div>
        ))}
        {events && events.length === 0 && (
          <p className="ka-muted">
            {kind === 'all' ? 'Nothing yet. Play a scene, and what your friends make of it lands here.' : 'Nothing of that kind yet.'}
          </p>
        )}
      </section>

      <aside className="ka-activity__side">
        <Glass title="Still being read">
          <ErrorLine error={storiesError} />
          <p className="ka-muted ka-m0">
            The memory reader files new lines every few turns. These will show up here, and on the lines they belong
            to, once it has.
          </p>
          {waiting.map((s) => (
            <div key={s.id} className="ka-row ka-row--gap">
              <Avatar item={items.find((i) => i.id === s.cast[0]?.lib_item_id)} name={s.cast[0]?.name ?? s.title} size={36} />
              <strong className="ka-grow">{s.waiting === 1 ? '1 line' : `${s.waiting} lines`} in {s.title}</strong>
            </div>
          ))}
          {waiting.length > 0 ? (
            <button type="button" className="k-btn" disabled={busy} onClick={readNow}>
              <Icon name="refresh" size={17} />
              Read now
            </button>
          ) : (
            <p className="ka-muted ka-m0">Every line has been read.</p>
          )}
        </Glass>
        <Glass title="How receipts fade">
          <div className="ka-legend">
            <span className="ka-legend__row">
              <Avatar item={sample} size={28} className="ka-legend__face is-sharp" />
              <span><b>Sharp</b> · the detail comes back</span>
            </span>
            <span className="ka-legend__row">
              <Avatar item={sample} size={28} className="ka-legend__face is-hazy" />
              <span><b>Hazy</b> · only the gist</span>
            </span>
            <span className="ka-legend__row">
              <span className="ka-legend__face is-gone" />
              <span><b>Forgotten</b></span>
            </span>
            <span className="ka-legend__row">
              <span className="ka-legend__face is-absent">{sample ? sample.name[0] : 'T'}</span>
              <span><b>Wasn't there</b> · never heard it</span>
            </span>
          </div>
        </Glass>
      </aside>
    </div>
  )
}
