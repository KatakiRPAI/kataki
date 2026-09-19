import { useState } from 'react'
import { api, type Item, type Story } from '../api'
import { Avatar, type TimeOfDay } from '../art'
import { useAction, useLibrary, useLoad } from '../hooks'
import { Dialog, ErrorLine, Field, Seg } from '../ui'

export type Preset = { friends?: number[]; place?: number; plot?: number; group?: boolean }

// the story clock at the start of each time of day (minutes after midnight)
const STARTS: Record<TimeOfDay, number> = { dawn: 360, day: 720, dusk: 1140, night: 1320 }

const joined = (names: string[]) =>
  names.length < 2 ? (names[0] ?? '') : `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`

/** Start a story: who is in it, where, which plot, when, and who you play. */
export default function NewChat({ open, preset, onClose, onCreated }: {
  open: boolean
  preset: Preset
  onClose: () => void
  onCreated: (story: Story) => void
}) {
  const { items } = useLibrary()
  const [settings] = useLoad(() => api<{ persona?: number | null }>('/settings'), [])
  const [friends, setFriends] = useState<number[]>(preset.friends ?? [])
  const [place, setPlace] = useState<number | null>(preset.place ?? null)
  const [plot, setPlot] = useState<number | null>(preset.plot ?? null)
  const [when, setWhen] = useState<TimeOfDay>('day')
  const [persona, setPersona] = useState<number | null>() // undefined: whoever you are in Settings
  const [title, setTitle] = useState('')
  const [run, error, busy] = useAction()

  const of = (kind: Item['kind']) => items.filter((i) => i.kind === kind)
  const personas = of('character').filter((i) => i.data.persona)
  const people = of('character').filter((i) => !i.data.persona).sort((a, b) => a.id - b.id)
  const name = (id: number | null) => items.find((i) => i.id === id)?.name
  const you = persona !== undefined ? persona : personas.some((p) => p.id === settings?.persona) ? settings!.persona! : null

  const pick = (id: number) =>
    setFriends((f) => (f.includes(id) ? f.filter((x) => x !== id) : preset.group ? [...f, id] : [id]))
  const cast = joined(friends.map((id) => name(id) ?? ''))
  const auto = name(plot) ?? (place && cast ? `${cast} at ${name(place)}` : cast) ?? ''

  const start = () =>
    run(async () => {
      const story = await api<Story>('/stories', 'POST', {
        title: title.trim() || auto || 'A new story',
        character_ids: friends,
        place_id: place,
        scenario_id: plot,
        persona_id: you,
        epoch_offset_min: STARTS[when],
      })
      onCreated(story)
    })

  return (
    <Dialog open={open} onClose={onClose} title={preset.group ? 'New group scene' : 'New chat'}>
      <form
        className="ka-form"
        onSubmit={(e) => {
          e.preventDefault()
          start()
        }}
      >
        <fieldset className="ka-fieldset">
          <legend>{preset.group ? 'Who is in it' : 'Who with'}</legend>
          <div className="ka-row">
            {people.map((f) => (
              <button key={f.id} type="button" className="k-chip ka-chip-person" aria-pressed={friends.includes(f.id)} onClick={() => pick(f.id)}>
                <Avatar item={f} size={26} />
                {f.name}
              </button>
            ))}
          </div>
        </fieldset>
        <div className="ka-grid2">
          <Field label="Where">
            <select className="k-select" value={place ?? ''} onChange={(e) => setPlace(e.target.value ? Number(e.target.value) : null)}>
              <option value="">Nowhere in particular</option>
              {of('place').map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </Field>
          <Field label="Plot">
            <select className="k-select" value={plot ?? ''} onChange={(e) => setPlot(e.target.value ? Number(e.target.value) : null)}>
              <option value="">None: see where it goes</option>
              {of('scenario').map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </Field>
        </div>
        <div className="k-field">
          <span>Time of day</span>
          <Seg label="Time of day" value={when} onChange={setWhen} options={[['dawn', 'Dawn'], ['day', 'Day'], ['dusk', 'Dusk'], ['night', 'Night']]} />
        </div>
        <div className="ka-grid2">
          <Field label="You play">
            <select className="k-select" value={you ?? ''} onChange={(e) => setPersona(e.target.value ? Number(e.target.value) : null)}>
              {personas.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              <option value="">No one: I direct the story</option>
            </select>
          </Field>
          <Field label="Title">
            <input className="k-input" value={title} placeholder={auto || 'A new story'} onChange={(e) => setTitle(e.target.value)} />
          </Field>
        </div>
        <ErrorLine error={error} />
        <div className="ka-row ka-row--end">
          <button type="button" className="k-btn" onClick={onClose}>Cancel</button>
          <button className="k-btn k-btn--dark" disabled={busy || friends.length === 0}>Start the story</button>
        </div>
      </form>
    </Dialog>
  )
}
