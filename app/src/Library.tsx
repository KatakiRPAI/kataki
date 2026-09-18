import { useState } from 'react'
import { api, type Item, type ItemKind } from './api'
import { ErrorLine, useAction, useLoad } from './ui'

const KINDS: { kind: ItemKind; label: string }[] = [
  { kind: 'character', label: 'Characters' },
  { kind: 'place', label: 'Places' },
  { kind: 'scenario', label: 'Scenarios' },
]

const split = (s: string) => s.split(',').map((x) => x.trim()).filter(Boolean)

export default function Library() {
  const [kind, setKind] = useState<ItemKind>('character')
  const [items, reload, error] = useLoad(() => api<Item[]>(`/library?kind=${kind}`), [kind])
  const [editing, setEditing] = useState<Item | 'new' | null>(null)

  return (
    <div className="stack" style={{ maxWidth: 900 }}>
      <h1>Library</h1>
      <p className="muted">
        Characters you play or play with, places, and scenarios. A story takes a copy of each, so editing here never
        rewrites a story in progress.
      </p>
      <div className="tabs" role="tablist">
        {KINDS.map((k) => (
          <button
            key={k.kind}
            role="tab"
            aria-selected={kind === k.kind}
            className={kind === k.kind ? 'active' : ''}
            onClick={() => {
              setKind(k.kind)
              setEditing(null)
            }}
          >
            {k.label}
          </button>
        ))}
      </div>
      <ErrorLine error={error} />
      {editing ? (
        <Editor
          key={editing === 'new' ? 'new' : editing.id}
          kind={kind}
          item={editing === 'new' ? null : editing}
          onDone={() => {
            setEditing(null)
            reload()
          }}
        />
      ) : (
        <>
          <div>
            <button className="primary" onClick={() => setEditing('new')}>New {kind}</button>
          </div>
          {items?.length === 0 && <p className="muted">Nothing here yet.</p>}
          {items?.map((item) => (
            <button key={item.id} className="card" style={{ textAlign: 'left' }} onClick={() => setEditing(item)}>
              <strong>{item.name}</strong>
              {item.tags.map((t) => <span key={t} className="badge" style={{ marginLeft: '0.4em' }}>{t}</span>)}
              <div className="muted">{item.description.slice(0, 160) || 'No description yet.'}</div>
            </button>
          ))}
        </>
      )}
    </div>
  )
}

function Editor({ kind, item, onDone }: { kind: ItemKind; item: Item | null; onDone: () => void }) {
  const [run, error, busy] = useAction()
  const [name, setName] = useState(item?.name ?? '')
  const [description, setDescription] = useState(item?.description ?? '')
  const [secret, setSecret] = useState(item?.private ?? '')
  const [first, setFirst] = useState(item?.data.first_message ?? '')
  const [aliases, setAliases] = useState((item?.data.aliases ?? []).join(', '))
  const [tags, setTags] = useState((item?.tags ?? []).join(', '))

  const save = () =>
    run(async () => {
      const body = {
        name: name.trim(),
        description,
        private: secret,
        data: { ...item?.data, aliases: split(aliases), first_message: first || undefined },
        tags: split(tags),
      }
      await (item ? api(`/library/${item.id}`, 'PATCH', body) : api('/library', 'POST', { kind, ...body }))
      onDone()
    })

  return (
    <form
      className="card stack"
      onSubmit={(e) => {
        e.preventDefault()
        save()
      }}
    >
      <h2>{item ? `Edit ${item.name}` : `New ${kind}`}</h2>
      <label>Name<input value={name} required onChange={(e) => setName(e.target.value)} /></label>
      <label>
        {kind === 'scenario' ? 'Premise (every character knows this)' : 'Description (what anyone in the scene can see or know)'}
        <textarea rows={5} value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>
      {kind === 'character' && (
        <label>
          Private (only this character knows it; it reaches the prompt only when they speak)
          <textarea rows={3} value={secret} onChange={(e) => setSecret(e.target.value)} />
        </label>
      )}
      {kind !== 'place' && (
        <label>
          {kind === 'scenario' ? 'Opening narration' : 'Opening line (when a story starts with them)'}
          <textarea rows={3} value={first} onChange={(e) => setFirst(e.target.value)} />
        </label>
      )}
      {kind !== 'scenario' && (
        <label>
          Other names, comma-separated (mentioning any of them brings up their memories)
          <input value={aliases} placeholder="the courier, Mir" onChange={(e) => setAliases(e.target.value)} />
        </label>
      )}
      <label>Tags, comma-separated<input value={tags} onChange={(e) => setTags(e.target.value)} /></label>
      <div className="row">
        <button className="primary" disabled={busy}>Save</button>
        <button type="button" onClick={onDone}>Cancel</button>
        <span className="spacer" />
        {item && (
          <button
            type="button"
            className="danger"
            disabled={busy}
            onClick={() => {
              if (confirm(`Delete ${item.name} from the library? Stories that use it keep their copy.`))
                run(async () => { await api(`/library/${item.id}`, 'DELETE'); onDone() })
            }}
          >
            Delete
          </button>
        )}
      </div>
      <ErrorLine error={error} />
    </form>
  )
}
