import { useState } from 'react'
import { SKIPS, type Cast, type CastEntity, type Item, type Story } from '../api'
import { Avatar, Room } from '../art'
import { useAction, useLibrary, type Moving } from '../hooks'
import { Dialog, ErrorLine, Field, Icon } from '../ui'

type Candidate = { move: Moving; name: string; item?: Item; status: string }

/** Who could come in: story characters who are away, then library friends not in the story. */
function candidates(cast: Cast, items: Item[], byId: Map<number, Item>): Candidate[] {
  const away = cast.entities
    .filter((e) => e.kind === 'character' && e.is_ai && !e.present)
    .map((e): Candidate => {
      const left = cast.changes.findLast((c) => c.entity_id === e.id && !c.present)
      return {
        move: { kind: 'away', id: e.id },
        name: e.name,
        item: e.lib_item_id ? byId.get(e.lib_item_id) : undefined,
        status: left ? `away · since ${left.clock.slice(0, -7)}` : 'away',
      }
    })
  const inStory = new Set(cast.entities.map((e) => e.lib_item_id))
  const friends = items
    .filter((i) => i.kind === 'character' && !i.data.persona && !inStory.has(i.id))
    .sort((a, b) => Number(!!b.data.favourite) - Number(!!a.data.favourite) || a.id - b.id)
    .map((i): Candidate => ({ move: { kind: 'friend', id: i.id }, name: i.name, item: i, status: 'could join' }))
  return [...away, ...friends]
}

/** Who is nearby, as compact widget rows under the characters: a click brings them in. The rest
 *  are a click further, in "Bring someone in". */
export function Nearby({ cast, busy, onMove }: { cast: Cast; busy: boolean; onMove: (m: Moving) => void }) {
  const { items, byId } = useLibrary()
  const [picking, setPicking] = useState(false)
  const all = candidates(cast, items, byId)
  const row = (c: Candidate, onPick: () => void, widget = true) => (
    <button key={`${c.move.kind}-${c.move.id}`} type="button" disabled={busy} onClick={onPick}
      className={`${widget ? 'k-widget ka-widget ' : ''}k-widget--row is-away ka-nearby`} aria-label={`Bring ${c.name} in (${c.status})`}>
      <Avatar item={c.item} name={c.name} size={40} />
      <span className="ka-nearby__who">
        <strong>{c.name}</strong>
        <span>{c.status}</span>
      </span>
    </button>
  )
  return (
    <>
      {all.slice(0, 2).map((c) => row(c, () => onMove(c.move)))}
      <button type="button" className="ka-nearby__bring" disabled={busy} onClick={() => setPicking(true)}>
        <Icon name="plus" size={14} />
        Bring someone in
      </button>
      <Dialog open={picking} onClose={() => setPicking(false)} title="Bring someone in">
        {all.length ? (
          <div className="ka-pick-grid">
            {all.map((c) => row(c, () => { setPicking(false); onMove(c.move) }, false))}
          </div>
        ) : (
          <p className="ka-muted">Everyone you know is already here.</p>
        )}
      </Dialog>
    </>
  )
}

export type SceneBody = { present: number[]; place_id?: number; library_place_id?: number; title?: string; skip?: string }

/** Cut to a new scene: where, who is there, a title, and time passing first. */
export function NewScene({ open, story, cast, onClose, onCut }: {
  open: boolean
  story: Story
  cast: Cast
  onClose: () => void
  onCut: (body: SceneBody) => Promise<void>
}) {
  return (
    <Dialog open={open} onClose={onClose} title="Where to?" className="ka-newscene">
      <SceneForm story={story} cast={cast} onClose={onClose} onCut={onCut} />
    </Dialog>
  )
}

// mounted fresh each time the dialog opens
function SceneForm({ story, cast, onClose, onCut }: { story: Story; cast: Cast; onClose: () => void; onCut: (body: SceneBody) => Promise<void> }) {
  const { items, byId } = useLibrary()
  const [run, error, busy] = useAction()
  const known = new Set(cast.entities.map((e) => e.lib_item_id))
  const places = [
    ...cast.entities.filter((e) => e.kind === 'place').map((e) => ({ key: `s${e.id}`, name: e.name, item: e.lib_item_id ? byId.get(e.lib_item_id) : undefined, body: { place_id: e.id } })),
    ...items.filter((i) => i.kind === 'place' && !known.has(i.id)).map((i) => ({ key: `l${i.id}`, name: i.name, item: i, body: { library_place_id: i.id } })),
  ]
  const people = cast.entities.filter((e) => e.kind === 'character')
  const [where, setWhere] = useState(places.find((p) => p.name !== story.place?.name)?.key ?? places[0]?.key)
  const [who, setWho] = useState(people.filter((e) => e.present || e.persona).map((e) => e.id))
  const [title, setTitle] = useState('')
  const [when, setWhen] = useState('')
  const [years, setYears] = useState(6)
  const place = places.find((p) => p.key === where)
  const cut = () =>
    run(async () => {
      const skip = when === 'years' ? `${years} years later` : when
      await onCut({ present: who, ...place?.body, ...(title.trim() ? { title: title.trim() } : {}), ...(skip ? { skip } : {}) })
      onClose()
    })
  const toggle = (e: CastEntity) => setWho((w) => (w.includes(e.id) ? w.filter((id) => id !== e.id) : [...w, e.id]))
  return (
    <form className="ka-stack" onSubmit={(e) => { e.preventDefault(); cut() }}>
      <div className="ka-film" role="group" aria-label="Places">
        {places.map((p) => (
          <button key={p.key} type="button" className="ka-film__place" aria-pressed={p.key === where} onClick={() => setWhere(p.key)}>
            <span className="ka-film__room"><Room item={p.item} minute={story.minute_of_day} /></span>
            {p.name}
          </button>
        ))}
        {!places.length && <p className="ka-muted">No places yet. Add one in Places, or cut without one.</p>}
      </div>
      <div className="ka-row" role="group" aria-label="Who is there">
        {people.map((e) => (
          <button key={e.id} type="button" className="k-sbtn ka-pick" aria-pressed={who.includes(e.id)} onClick={() => toggle(e)}>
            <Avatar item={e.lib_item_id ? byId.get(e.lib_item_id) : undefined} name={e.name} size={22} />
            {e.name}
          </button>
        ))}
      </div>
      <Field label="Title (optional)">
        <input className="k-input" value={title} placeholder={place?.name ?? 'A new scene'} onChange={(e) => setTitle(e.target.value)} />
      </Field>
      <div className="ka-row">
        <Field label="When">
          <select className="k-select" value={when} onChange={(e) => setWhen(e.target.value)}>
            <option value="">Straight after</option>
            {SKIPS.map(([words, label]) => <option key={words} value={words}>{label}</option>)}
            <option value="years">Years later…</option>
          </select>
        </Field>
        {when === 'years' && (
          <Field label="Years">
            <input className="k-input ka-years__n" type="number" min={1} max={99} value={years}
              onChange={(e) => setYears(Math.max(1, Math.min(99, Number(e.target.value) || 1)))} />
          </Field>
        )}
      </div>
      <ErrorLine error={error} />
      <div className="ka-row ka-row--end">
        <button type="button" className="k-sbtn" onClick={onClose}>Stay here</button>
        <button type="submit" className="k-sbtn ka-sbtn--primary" disabled={busy}>Cut to {place?.name ?? 'the new scene'}</button>
      </div>
    </form>
  )
}
