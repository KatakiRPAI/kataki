import { useState } from 'react'
import { api, type Item } from '../api'
import { useAction, useLoad } from '../hooks'
import { ErrorLine } from '../ui'

export function NewStory({ onCreated }: { onCreated: (id: number) => void }) {
  const [items, , error] = useLoad(() => api<Item[]>('/library'), [])
  const [run, actionError, busy] = useAction()
  const [title, setTitle] = useState('')
  const [cast, setCast] = useState<number[]>([])
  const [persona, setPersona] = useState<number | ''>('')
  const [place, setPlace] = useState<number | ''>('')
  const [scenario, setScenario] = useState<number | ''>('')

  const of = (kind: Item['kind']) => items?.filter((i) => i.kind === kind) ?? []
  const characters = of('character')
  const toggle = (id: number) => setCast((c) => (c.includes(id) ? c.filter((x) => x !== id) : [...c, id]))

  const create = () =>
    run(async () => {
      const story = await api<{ id: number }>('/stories', 'POST', {
        title: title.trim() || 'Untitled story',
        character_ids: cast,
        persona_id: persona || null,
        place_id: place || null,
        scenario_id: scenario || null,
      })
      onCreated(story.id)
    })

  if (items && !characters.length)
    return (
      <div className="card" style={{ maxWidth: 700 }}>
        <h1>New story</h1>
        <p>Create at least one character in the Library first.</p>
      </div>
    )

  return (
    <form
      className="card stack"
      style={{ maxWidth: 700 }}
      onSubmit={(e) => {
        e.preventDefault()
        create()
      }}
    >
      <h1>New story</h1>
      <ErrorLine error={error} />
      <label>Title<input value={title} placeholder="Untitled story" onChange={(e) => setTitle(e.target.value)} /></label>
      <fieldset className="stack" style={{ border: 'none', padding: 0, margin: 0 }}>
        <legend className="muted">Characters the AI plays</legend>
        {characters.map((c) => (
          <label key={c.id} className="check">
            <input type="checkbox" checked={cast.includes(c.id)} disabled={c.id === persona} onChange={() => toggle(c.id)} />
            {c.name}
          </label>
        ))}
      </fieldset>
      <label>
        You play
        <select value={persona} onChange={(e) => setPersona(e.target.value ? Number(e.target.value) : '')}>
          <option value="">No one: I direct the story</option>
          {characters.filter((c) => !cast.includes(c.id)).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </label>
      <div className="grid2">
        <label>
          Where it begins
          <select value={place} onChange={(e) => setPlace(e.target.value ? Number(e.target.value) : '')}>
            <option value="">Nowhere in particular</option>
            {of('place').map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </label>
        <label>
          Scenario
          <select value={scenario} onChange={(e) => setScenario(e.target.value ? Number(e.target.value) : '')}>
            <option value="">None</option>
            {of('scenario').map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </label>
      </div>
      <div className="row">
        <button className="primary" disabled={busy || !cast.length}>Start</button>
        {!cast.length && <small>Pick at least one character for the AI to play.</small>}
      </div>
      <ErrorLine error={actionError} />
    </form>
  )
}
