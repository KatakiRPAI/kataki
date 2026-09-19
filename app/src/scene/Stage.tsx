import { useState, type CSSProperties } from 'react'
import type { CastEntity, Story } from '../api'
import { Avatar, Figure, paletteOf, Room } from '../art'
import { DRAG, useLibrary, type Moving } from '../hooks'
import { Icon } from '../ui'

/** The place, lit by the story's clock, with up to three people in it (the speaker lit in front,
 *  the others softened) and anyone beyond that as a row of avatars. Drop someone from the tray
 *  here to bring them in; drag a figure off to the tray, or use its button, to send them away.
 *  `arriving` steps in with a name card. */
export default function Stage({ story, people, arriving, busy, onMove }: {
  story: Story
  people: CastEntity[]
  arriving?: number
  busy: boolean
  onMove: (m: Moving) => void
}) {
  const { byId } = useLibrary()
  const [target, setTarget] = useState(false)
  const item = (e: { lib_item_id: number | null }) => (e.lib_item_id ? byId.get(e.lib_item_id) : undefined)
  const shown = people.slice(0, 3)
  return (
    <div
      className={`k-stage ka-stage${target ? ' is-target' : ''}`}
      data-count={shown.length}
      onDragOver={(e) => {
        if (!e.dataTransfer.types.includes(DRAG)) return
        e.preventDefault()
        setTarget(true)
      }}
      onDragLeave={(e) => e.currentTarget.contains(e.relatedTarget as Node) || setTarget(false)}
      onDrop={(e) => {
        setTarget(false)
        const m: Moving = JSON.parse(e.dataTransfer.getData(DRAG) || 'null')
        if (m && m.kind !== 'here') onMove(m)
      }}
    >
      <Room item={story.place ? item(story.place) : undefined} minute={story.minute_of_day} />
      {shown.map((e, i) => (
        <span key={e.id} className="ka-stage__slot" data-slot={i} draggable
          onDragStart={(d) => d.dataTransfer.setData(DRAG, JSON.stringify({ kind: 'here', id: e.id }))}>
          <Figure item={item(e)} name={e.name} className={`k-stage__char${i ? ' is-softened' : ''}${e.id === arriving ? ' is-entering' : ''}`} />
          <button type="button" className="k-sbtn ka-stage__away" disabled={busy} onClick={() => onMove({ kind: 'here', id: e.id })}>
            <Icon name="arrow" size={14} />
            Send {e.name} away
          </button>
          {e.id === arriving && (
            <span className="ka-namecard k-sglass" role="status">
              <Avatar item={item(e)} name={e.name} size={40} className="ka-namecard__face" />
              <span className="ka-namecard__text">
                <span className="ka-namecard__title" style={{ '--ink': paletteOf(item(e), e.name).ink } as CSSProperties}>{e.name} joins</span>
                <span className="ka-namecard__line">{(item(e)?.description || e.summary).split('\n')[0]}</span>
              </span>
            </span>
          )}
        </span>
      ))}
      <span className="k-stage__vignette" />
      {people.length > 3 && (
        <div className="ka-stage__row">
          {people.slice(3).map((e) => (
            <span key={e.id} title={e.name}>
              <Avatar item={item(e)} name={e.name} size={40} />
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
