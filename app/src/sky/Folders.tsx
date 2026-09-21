import { useState } from 'react'
import { api, type Folder } from '../api'
import { useAction, useLoad } from '../hooks'
import { Chip, Dialog, ErrorLine, Field, Icon } from '../ui'

/** Two shelves hold the same things when they hold the same tags, in any order. */
const same = (a: string[], b: string[]) => a.length === b.length && a.every((t) => b.includes(t))

/** Does this thing belong on a shelf? Only if it wears every tag the shelf is named by. */
export const onShelf = (wears: string[], tags: string[]) =>
  tags.every((t) => wears.some((w) => w.toLowerCase() === t.toLowerCase()))

/** The folder rail: the shelves you saved, over the tags in your library. A folder is nothing but
 *  a name over a set of tags, so it costs the engine nothing — it lives in settings. */
export default function Folders({ kind, wears, picked, onPick }: {
  kind: Folder['kind']
  wears: string[] // every tag worn by the things this screen shows — the only ones it can shelve
  picked: string[]
  onPick: (tags: string[]) => void
}) {
  const [settings, reloadSettings, settingsError] = useLoad(
    () => api<{ folders?: Folder[] }>('/settings'),
    [],
  )
  const [run, actionError, busy] = useAction()
  const [open, setOpen] = useState(false)
  const [chosen, setChosen] = useState<string[]>([])

  const saved = settings?.folders ?? []
  const mine = saved.filter((f) => f.kind === kind)
  const on = mine.find((f) => same(f.tags, picked))
  // Only what is here can be shelved here: a tag on a place is no folder of friends, and a tag
  // added a moment ago is already in this list, because the screen is the list.
  const offered = [...new Set(wears)].sort((a, b) => a.localeCompare(b))

  /** Settings keeps one list for every kind, so the other kinds' folders travel with every save. */
  const keep = (folders: Folder[]) =>
    run(async () => {
      await api('/settings', 'PUT', { folders: [...saved.filter((f) => f.kind !== kind), ...folders] })
      reloadSettings()
    })

  const make = (form: HTMLFormElement) => {
    const name = String(new FormData(form).get('name') ?? '').trim()
    if (!name || !chosen.length) return
    keep([...mine.filter((f) => f.name !== name), { name, kind, tags: chosen }])
    setChosen([])
    form.reset()
  }

  return (
    <>
      <div className="ka-row ka-row--gap ka-folders" role="group" aria-label="Folders">
        <Chip pressed={picked.length === 0} onClick={() => onPick([])}>
          Everything
        </Chip>
        {mine.map((f) => (
          <Chip key={f.name} icon="filter" pressed={on?.name === f.name} onClick={() => onPick(f.tags)}>
            {f.name}
          </Chip>
        ))}
        {picked.length > 0 && !on && (
          <Chip pressed onClick={() => onPick([])}>
            {picked.join(' + ')}
            <Icon name="x" size={13} />
          </Chip>
        )}
        <Chip icon="plus" onClick={() => setOpen(true)}>
          Folders
        </Chip>
      </div>
      <ErrorLine error={settingsError || actionError} />

      <Dialog open={open} onClose={() => setOpen(false)} title="Folders">
        <p className="ka-muted">
          A folder is a name over a set of tags. Nothing moves into it — anything wearing every tag
          is on the shelf, and leaves it when the tag comes off.
        </p>
        {mine.length > 0 && (
          <ul className="ka-folderlist">
            {mine.map((f) => (
              <li key={f.name} className="ka-folderlist__row">
                <span className="ka-shelf__text">
                  <span className="ka-ellipsis">{f.name}</span>
                  <span className="ka-muted ka-small">{f.tags.join(' + ')}</span>
                </span>
                <button
                  type="button" className="k-btn k-btn--sm" disabled={busy}
                  onClick={() => keep(mine.filter((x) => x.name !== f.name))}
                >
                  <Icon name="x" size={14} />
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}

        <form
          className="ka-form"
          onSubmit={(e) => {
            e.preventDefault()
            make(e.currentTarget)
          }}
        >
          <Field label="What to call it">
            <input name="name" className="k-input" required maxLength={60} placeholder="The docks" />
          </Field>
          <span className="k-field">
            <span>Everything wearing</span>
            {offered.length === 0 ? (
              <span className="ka-muted ka-small">
                No tags yet. Tag a few things first, and they can be shelved.
              </span>
            ) : (
              <span className="ka-row ka-row--gap">
                {offered.map((t) => (
                  <Chip
                    key={t}
                    pressed={chosen.includes(t)}
                    onClick={() =>
                      setChosen((was) => (was.includes(t) ? was.filter((x) => x !== t) : [...was, t]))
                    }
                  >
                    {t}
                  </Chip>
                ))}
              </span>
            )}
          </span>
          <div className="ka-row ka-row--end">
            <button type="button" className="k-btn" onClick={() => setOpen(false)}>Done</button>
            <button type="submit" className="k-btn k-btn--dark" disabled={busy || !chosen.length}>
              Make the folder
            </button>
          </div>
        </form>
      </Dialog>
    </>
  )
}
