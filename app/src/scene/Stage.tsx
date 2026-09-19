import type { CastEntity, Story } from '../api'
import { Avatar, Figure, Room } from '../art'
import { useLibrary } from '../hooks'

/** The place, lit by the story's clock, with up to three people in it (the speaker lit in front,
 *  the others softened) and anyone beyond that as a row of avatars. */
export default function Stage({ story, people }: { story: Story; people: CastEntity[] }) {
  const { byId } = useLibrary()
  const item = (e: { lib_item_id: number | null }) => (e.lib_item_id ? byId.get(e.lib_item_id) : undefined)
  const shown = people.slice(0, 3)
  return (
    <div className="k-stage ka-stage" data-count={shown.length}>
      <Room item={story.place ? item(story.place) : undefined} minute={story.minute_of_day} />
      {shown.map((e, i) => (
        <span key={e.id} className="ka-stage__slot" data-slot={i}>
          <Figure item={item(e)} name={e.name} className={`k-stage__char${i ? ' is-softened' : ''}`} />
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
