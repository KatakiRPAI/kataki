import { useState } from 'react'
import { api, upload, type Item, type PictureFailure, type RoleRow } from '../api'
import { Room } from '../art'
import { dive, useAction, useLibrary, useLoad } from '../hooks'
import { Dialog, ErrorLine, Field, Icon, PictureTrouble, pictureFailure, Prose, SkyHeader } from '../ui'
import NewChat, { type Preset } from './NewChat'

type Kind = 'place' | 'scenario'

const list = (s: string) => s.split(',').map((x) => x.trim()).filter(Boolean)

/** Add or edit a place or a plot. Deleting leaves stories their own copy. */
function ItemDialog({ open, kind, item, onClose }: { open: boolean; kind: Kind; item?: Item; onClose: () => void }) {
  const { reload } = useLibrary()
  const [name, setName] = useState(item?.name ?? '')
  const [description, setDescription] = useState(item?.description ?? '')
  const [opening, setOpening] = useState(item?.data.first_message ?? '')
  const [aliases, setAliases] = useState((item?.data.aliases ?? []).join(', '))
  const [tags, setTags] = useState((item?.tags ?? []).join(', '))
  const [image, setImage] = useState(item?.data.image)
  const [confirming, setConfirming] = useState(false)
  const [run, error, busy] = useAction()
  const place = kind === 'place'
  const noun = place ? 'place' : 'plot'

  const save = () =>
    run(async () => {
      const data = place ? { ...item?.data, aliases: list(aliases), image } : { ...item?.data, first_message: opening }
      const body = { name: name.trim(), description, tags: list(tags), data }
      await (item ? api(`/library/${item.id}`, 'PATCH', body) : api('/library', 'POST', { kind, ...body }))
      reload()
      onClose()
    })
  const remove = () =>
    run(async () => {
      await api(`/library/${item!.id}`, 'DELETE')
      reload()
      onClose()
    })

  return (
    <Dialog open={open} onClose={onClose} title={item ? `Edit ${item.name}` : `Add a ${noun}`}>
      <form
        className="ka-form"
        onSubmit={(e) => {
          e.preventDefault()
          save()
        }}
      >
        <Field label="Name">
          <input className="k-input" value={name} autoFocus placeholder={place ? 'The Gull' : 'The Missing Ledger'} onChange={(e) => setName(e.target.value)} />
        </Field>
        {place ? (
          <>
            <Field label="What anyone there can see">
              <textarea className="k-input ka-textarea-sm" rows={3} value={description} placeholder="A smoky dockside tavern. Rain on the windows, a harbour bell far off." onChange={(e) => setDescription(e.target.value)} />
            </Field>
            <div className="ka-upload">
              <span className="ka-upload__place"><Room item={{ data: { image } } as Item} minute={1140} /></span>
              <div className="ka-stack">
                <label className="k-btn">
                  <Icon name="image" size={17} />
                  {image ? 'Change the picture' : 'Add a picture'}
                  <input type="file" className="k-sr" accept="image/png,image/jpeg,image/gif,image/webp" onChange={(e) => {
                    const file = e.target.files?.[0]
                    e.target.value = ''
                    if (file) run(async () => setImage((await upload(file)).name))
                  }} />
                </label>
                {image && <button type="button" className="k-btn k-btn--ghost k-btn--sm" onClick={() => setImage(undefined)}>Remove the picture</button>}
              </div>
            </div>
            <Field label="Other names">
              <input className="k-input" value={aliases} placeholder="the tavern" onChange={(e) => setAliases(e.target.value)} />
            </Field>
          </>
        ) : (
          <>
            <Field label="Premise: every character knows this">
              <textarea className="k-input ka-textarea-sm" rows={3} value={description} placeholder="The guild's ledger vanished the night of the storm." onChange={(e) => setDescription(e.target.value)} />
            </Field>
            <Field label="Opening narration">
              <textarea className="k-input ka-textarea-sm" rows={3} value={opening} placeholder="*Rain hammers the shutters of the guild hall.*" onChange={(e) => setOpening(e.target.value)} />
            </Field>
          </>
        )}
        <Field label="Tags">
          <input className="k-input" value={tags} placeholder={place ? 'Tavern, Docks' : 'Mystery'} onChange={(e) => setTags(e.target.value)} />
        </Field>
        <ErrorLine error={error} />
        {confirming ? (
          <div className="ka-confirm">
            <span>Delete {item!.name}? Stories that use it keep their own copy.</span>
            <button type="button" className="k-btn k-btn--sm" onClick={() => setConfirming(false)}>Keep it</button>
            <button type="button" className="k-btn k-btn--dark k-btn--sm" disabled={busy} onClick={remove}>Delete</button>
          </div>
        ) : (
          <div className="ka-row ka-row--end">
            {item && <button type="button" className="k-btn k-btn--danger ka-push-left" onClick={() => setConfirming(true)}>Delete</button>}
            <button type="button" className="k-btn" onClick={onClose}>Cancel</button>
            <button className="k-btn k-btn--dark" disabled={busy || !name.trim()}>{item ? 'Save' : `Add the ${noun}`}</button>
          </div>
        )}
      </form>
    </Dialog>
  )
}

/** Draw a place's background through the Pictures job: one click, one paid picture, no retries. */
function DrawButton({ place }: { place: Item }) {
  const { reload } = useLibrary()
  const [run, error, busy] = useAction()
  const [failure, setFailure] = useState<PictureFailure>()
  const draw = (provider?: string) => run(async () => {
    setFailure(undefined)
    try {
      await api(`/library/${place.id}/draw`, 'POST', { provider })
    } catch (e) {
      const failed = pictureFailure(e)
      if (!failed) throw e
      return setFailure(failed)
    }
    reload()
  })
  return (
    <>
      <button type="button" className="k-btn k-btn--ghost k-btn--sm" disabled={busy} onClick={() => draw()}>
        <Icon name="image" size={14} />
        {busy ? 'Drawing…' : place.data.image ? 'Draw again' : 'Draw background'}
      </button>
      {error && <span className="ka-error ka-place__error" role="alert">{error}</span>}
      {failure && <span className="ka-place__error"><PictureTrouble failure={failure} busy={busy} onRetry={draw} /></span>}
    </>
  )
}

/** #/places — places to set a story, and plots to start one from. */
export default function Places() {
  const { items, error } = useLibrary()
  const [roles] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const pictures = !!roles?.find((r) => r.role === 'image')?.effective_model
  // the dialog stays mounted and opens by prop; n gives each opening a fresh form
  const [editing, setEditing] = useState<{ kind: Kind; item?: Item; open: boolean; n: number }>({ kind: 'place', open: false, n: 0 })
  const edit = (kind: Kind, item?: Item) => setEditing((e) => ({ kind, item, open: true, n: e.n + 1 }))
  const [newChat, setNewChat] = useState<{ preset?: Preset; n: number }>({ n: 0 })
  const places = items.filter((i) => i.kind === 'place').sort((a, b) => a.id - b.id)
  const plots = items.filter((i) => i.kind === 'scenario').sort((a, b) => a.id - b.id)
  const startNew = (preset: Preset) => setNewChat((c) => ({ preset, n: c.n + 1 }))

  return (
    <>
      <SkyHeader title="Places & Plots">
        <button type="button" className="k-btn" onClick={() => edit('scenario')}>
          <Icon name="book" size={17} />
          Add a plot
        </button>
        <button type="button" className="k-btn k-btn--dark k-btn--lg" onClick={() => edit('place')}>
          <Icon name="plus" size={17} />
          Add a place
        </button>
      </SkyHeader>
      <ErrorLine error={error} />
      <div className="ka-places">
        {places.map((p) => (
          <article key={p.id} className="ka-place">
            <Room item={p} minute={1140} />
            <div className="k-nameplate">
              <strong className="ka-place__name">{p.name}</strong>
              {p.description && <span className="ka-muted ka-small ka-clamp2">{p.description}</span>}
              <span className="ka-row ka-row--gap">
                <button type="button" className="k-btn k-btn--dark k-btn--sm" onClick={() => startNew({ place: p.id })}>Start a scene here</button>
                <button type="button" className="k-btn k-btn--ghost k-btn--sm" onClick={() => edit('place', p)}>
                  <Icon name="edit" size={14} />
                  Edit
                </button>
                {pictures && <DrawButton place={p} />}
              </span>
            </div>
          </article>
        ))}
        {places.length === 0 && <p className="ka-muted">No places yet. Add one: a tavern, a ship, a whole city.</p>}
      </div>

      <div className="ka-section-head">
        <h2>Plots</h2>
      </div>
      <div className="ka-plots">
        {plots.map((p) => (
          <article key={p.id} className="k-card ka-plot">
            <h3>{p.name}</h3>
            <div className="ka-stack ka-stack--tight">
              <span className="k-eyebrow ka-eyebrow">Every character knows</span>
              <span className="ka-plot__premise">{p.description || 'No premise yet.'}</span>
            </div>
            {p.data.first_message && (
              <div className="ka-plot__opening"><Prose text={p.data.first_message} /></div>
            )}
            <span className="ka-row ka-row--gap ka-plot__actions">
              <button type="button" className="k-btn k-btn--dark k-btn--sm" onClick={() => startNew({ plot: p.id })}>Start this plot</button>
              <button type="button" className="k-btn k-btn--ghost k-btn--sm" onClick={() => edit('scenario', p)}>
                <Icon name="edit" size={14} />
                Edit
              </button>
            </span>
          </article>
        ))}
        {plots.length === 0 && <p className="ka-muted">No plots yet. A plot is a premise every character knows, and how the story opens.</p>}
      </div>

      <ItemDialog key={`item-${editing.n}`} open={editing.open} kind={editing.kind} item={editing.item} onClose={() => setEditing((e) => ({ ...e, open: false }))} />
      <NewChat
        key={`chat-${newChat.n}`}
        open={!!newChat.preset}
        preset={newChat.preset ?? {}}
        onClose={() => setNewChat((c) => ({ n: c.n }))}
        onCreated={(story) => {
          setNewChat((c) => ({ n: c.n }))
          dive(`/story/${story.id}`)
        }}
      />
    </>
  )
}
