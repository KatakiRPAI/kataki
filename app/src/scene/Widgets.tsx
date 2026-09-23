import { useEffect, useRef, useState, type CSSProperties } from 'react'
import type { CastEntity, Expression, Item, Story } from '../api'
import { Figure, MIDDAY, Room, SunArc, timeOfDay, type TimeOfDay } from '../art'

/** The place behind everything, blurred and dimmed under the chat. Relighting crossfades two
 *  stacked rooms over 600 ms, opacity only (1.5). */
export function Place({ item, minute }: { item?: Item; minute: number }) {
  const tod = timeOfDay(minute)
  const [leaving, setLeaving] = useState<TimeOfDay>()
  const lit = useRef(tod)
  useEffect(() => {
    if (lit.current === tod) return
    setLeaving(lit.current)
    lit.current = tod
    const done = setTimeout(() => setLeaving(undefined), 600)
    return () => clearTimeout(done)
  }, [tod])
  return (
    <div className="k-place ka-backdrop">
      <Room item={item} minute={minute} />
      {leaving && <Room key={leaving} item={item} minute={MIDDAY[leaving]} className="ka-room--leaving" />}
      <span className="k-place__vignette" />
    </div>
  )
}

/** The chip under a character's name: the face they last spoke with, coloured by feeling. */
const FACES: Record<Expression, [string, string]> = {
  neutral: ['calm', 'var(--k-scene-sage)'],
  smiling: ['smiling', 'var(--k-scene-sage)'],
  wary: ['wary', 'var(--k-scene-rose)'],
  surprised: ['surprised', 'var(--k-scene-sky)'],
  doubtful: ['doubtful', 'var(--k-scene-lilac)'],
}

/** One character in the scene: their art in the face they last spoke with, the name, and a line
 *  about them. Clicking it opens their card. */
export function CharacterWidget({ entity, item, face, state, joined, onPeek }: {
  entity: CastEntity
  item?: Item
  face?: Expression
  state?: 'thinking' | 'writing' // their reply is on its way
  joined: boolean
  onPeek: (at: { x: number; y: number }) => void
}) {
  const [word, color] = state ? [`${state}…`, 'var(--k-scene-sky)'] : face ? FACES[face] : []
  const line = (item?.description || entity.summary).split('\n')[0]
  return (
    <button type="button" className={`k-widget ka-widget ka-cwidget${joined ? ' is-joined' : ''}`} aria-label={`${entity.name}: open their card`}
      onClick={(e) => {
        const box = e.currentTarget.getBoundingClientRect()
        onPeek({ x: box.left - 448, y: box.top + 120 }) // the card opens beside the widget
      }}>
      <span className="k-widget__art ka-cwidget__art">
        <Figure item={item} name={entity.name} expression={face} />
        {joined && <span className="ka-cwidget__joined">Joined</span>}
      </span>
      <span className="ka-cwidget__body">
        <span className="ka-cwidget__name">
          {entity.name}
          {word && <span className="k-expr" style={{ '--c': color } as CSSProperties}>{word}</span>}
        </span>
        {line && <span className="ka-cwidget__line">{line}</span>}
      </span>
    </button>
  )
}

const twelve = (minute: number) => {
  const h = Math.floor(minute / 60) % 24
  return `${h % 12 || 12}:${String(minute % 60).padStart(2, '0')} ${h < 12 ? 'am' : 'pm'}`
}

/** The story clock: the time big and 12-hour (24-hour and the full date on hover), the chapter or
 *  the day under it, the place and the sun or moon. */
export function ClockWidget({ story, chapter, rolling }: { story: Story; chapter?: string; rolling: boolean }) {
  const day = story.clock.replace(/,?\s*\d{1,2}:\d{2}$/, '') // "Year 7, Day 1, 19:14" -> "Year 7, Day 1"
  return (
    <section className="k-widget ka-widget ka-clock" aria-label="Story clock">
      <span className="ka-clock__top">
        <span key={story.clock} className={`k-clock__time ka-clock__time${rolling ? ' is-rolling' : ''}`} tabIndex={0}
          data-tip={story.clock}>
          {twelve(story.minute_of_day)}
        </span>
        <SunArc minute={story.minute_of_day} />
      </span>
      <strong className="ka-clock__label">{chapter ?? day}</strong>
      <span className="ka-clock__foot">
        {story.place?.name ?? 'Nowhere yet'}
        {chapter && <span>{day}</span>}
      </span>
    </section>
  )
}
