import { useState } from 'react'
import { api, mediaUrl, upload, type Book, type Item, type PictureFailure, type RoleRow, type StorySummary } from '../api'
import { Avatar, AvatarStack, MIDDAY, Room } from '../art'
import { dive, href, useAction, useLibrary, useLoad } from '../hooks'
import { Candy, Dialog, ErrorLine, Field, Icon, Menu, PictureTrouble, pictureFailure, SkyHeader } from '../ui'
import NewChat, { type Preset } from './NewChat'

type Kind = 'place' | 'scenario'

const list = (s: string) => s.split(',').map((x) => x.trim()).filter(Boolean)

/** Add or edit a place or a plot. Deleting leaves stories their own copy. A new one is filed
 *  to the book (or story) the page is filtered by. */
function ItemDialog({ open, kind, item, fileTo = {}, onClose }: { open: boolean; kind: Kind; item?: Item; fileTo?: Filter; onClose: () => void }) {
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
      const filed = item ? {} : { links: { book: fileTo.book, stories: fileTo.story ? [fileTo.story] : undefined } }
      const data = place ? { ...item?.data, ...filed, aliases: list(aliases), image } : { ...item?.data, ...filed, first_message: opening }
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
/** Earlier pictures of a place or a character: every redraw keeps the one it replaced, and one
 *  click goes back to it (free: no model is asked). A character gets back the expressions made
 *  from it too. */
export function EarlierPictures({ item }: { item: Item }) {
  const { reload } = useLibrary()
  const [open, setOpen] = useState(false)
  const [run, error, busy] = useAction()
  const earlier = item.data.history ?? []
  if (!earlier.length) return null
  const pick = (name: string) => run(async () => {
    await api(`/library/${item.id}/picture`, 'POST', { name })
    reload()
    setOpen(false)
  })
  return (
    <>
      <button type="button" className="k-btn k-btn--ghost k-btn--sm" onClick={() => setOpen(true)}>
        <Icon name="undo" size={14} />
        Earlier ({earlier.length})
      </button>
      <Dialog open={open} onClose={() => setOpen(false)} title={`Earlier pictures of ${item.name}`}>
        <p className="ka-muted ka-small">Pick one to use it again. The current one stays here too.</p>
        <div className="ka-earlier">
          {earlier.map((name) => (
            <button key={name} type="button" className="ka-earlier__pick" disabled={busy} onClick={() => pick(name)}
              aria-label={`Use this earlier picture of ${item.name}`}>
              <img src={mediaUrl(name)} alt="" />
            </button>
          ))}
        </div>
        <ErrorLine error={error} />
      </Dialog>
    </>
  )
}

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

type Links = { book?: number; stories?: number[]; characters?: number[] }
type Filter = { book?: number; story?: number; loose?: boolean } // nothing set: everything
type Sort = 'recent' | 'az' | 'most'

/** #/places — Places and Plots: where stories happen and what they start from, filed under the
 *  books and stories that use them (or linked by hand), with the faces of who knows them. */
export default function Places() {
  const { items, byId, error } = useLibrary()
  const [roles] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const [stories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [books] = useLoad(() => api<Book[]>('/books'), [])
  const pictures = !!roles?.find((r) => r.role === 'image')?.effective_model
  // the dialogs stay mounted and open by prop; n gives each opening a fresh form
  const [editing, setEditing] = useState<{ kind: Kind; item?: Item; open: boolean; n: number }>({ kind: 'place', open: false, n: 0 })
  const edit = (kind: Kind, item?: Item) => setEditing((e) => ({ kind, item, open: true, n: e.n + 1 }))
  const [linking, setLinking] = useState<{ item?: Item; n: number }>({ n: 0 })
  const [newChat, setNewChat] = useState<{ preset?: Preset; n: number }>({ n: 0 })
  const startNew = (preset: Preset) => setNewChat((c) => ({ preset, n: c.n + 1 }))
  const [filter, setFilter] = useState<Filter>({})
  const [who, setWho] = useState<number>()
  const [tab, setTab] = useState<'all' | Kind>('all')
  const [sort, setSort] = useState<Sort>('recent')
  const [q, setQ] = useState('')

  const all = items.filter((i) => i.kind === 'place' || i.kind === 'scenario')
  const played = stories ?? []
  const links = (i: Item): Links => i.data.links ?? {}
  // the stories an item is in: used there (a place), started from it (a plot), or linked by hand
  const storiesOf = (i: Item) =>
    played.filter((s) => (i.kind === 'place' ? s.places.includes(i.id) : s.plot_id === i.id) || links(i).stories?.includes(s.id))
  const bookOf = (i: Item) => links(i).book ?? storiesOf(i).find((s) => s.book)?.book?.id
  const facesOf = (i: Item) =>
    [...new Set([...storiesOf(i).flatMap((s) => s.cast.map((c) => c.lib_item_id)), ...(links(i).characters ?? [])])]
      .filter((id): id is number => id !== null && !!byId.get(id))
  const usedAt = (i: Item) => storiesOf(i).reduce((a, s) => (s.last_at > a ? s.last_at : a), '')
  const inStory = (i: Item, id: number) => storiesOf(i).some((s) => s.id === id)
  const shown = all
    .filter((i) => tab === 'all' || i.kind === tab)
    .filter((i) => !q.trim() || `${i.name} ${i.description}`.toLowerCase().includes(q.trim().toLowerCase()))
    .filter((i) => (filter.book ? bookOf(i) === filter.book : filter.story ? inStory(i, filter.story) : filter.loose ? !bookOf(i) : true))
    .filter((i) => who === undefined || facesOf(i).includes(who))
    .sort((a, b) =>
      sort === 'az' ? a.name.localeCompare(b.name)
      : sort === 'most' ? storiesOf(b).length - storiesOf(a).length || a.name.localeCompare(b.name)
      : usedAt(b).localeCompare(usedAt(a)) || b.id - a.id,
    )
  const groups = [
    ...(books ?? []).map((b) => ({ book: b as Book | undefined, items: shown.filter((i) => bookOf(i) === b.id) })),
    { book: undefined, items: shown.filter((i) => !bookOf(i)) },
  ].filter((g) => g.items.length)
  const count = (pick: (i: Item) => boolean) => all.filter(pick).length
  const people = [...new Set(all.flatMap(facesOf))].map((id) => byId.get(id)!).filter((c) => !c.data.persona)
  const whose = who !== undefined ? byId.get(who)?.name : undefined

  const card = (i: Item) => {
    const place = i.kind === 'place'
    const used = storiesOf(i)
    const faces = facesOf(i).map((id) => byId.get(id)!).filter((c) => !c.data.persona).slice(0, 4)
    const chips = (
      <span className="ka-lib__links">
        {used.map((s) => (
          <a key={s.id} className="ka-lib__chip" href={href(`/chats/${s.id}`)}>
            <Icon name="chat" size={12} />
            {s.title}
          </a>
        ))}
        {!used.length && !bookOf(i) && (
          <span className="ka-lib__chip is-loose">
            <Icon name="alert" size={12} />
            Not in a book
          </span>
        )}
        {faces.length > 0 && <AvatarStack people={faces.map((c) => ({ item: c, name: c.name }))} size={26} />}
      </span>
    )
    const more = (
      <Menu label={`More for ${i.name}`} className="ka-lib__more">
        <button type="button" onClick={() => setLinking((l) => ({ item: i, n: l.n + 1 }))}>
          <Icon name="link" size={15} />
          Link to…
        </button>
        <button type="button" onClick={() => edit(i.kind as Kind, i)}>
          <Icon name="edit" size={15} />
          Edit
        </button>
      </Menu>
    )
    return place ? (
      <article key={i.id} className="k-card ka-lib__card">
        <div className="ka-lib__art">
          <Room item={i} minute={1140} />
          <strong className="ka-lib__title">{i.name}</strong>
          {more}
        </div>
        <div className="ka-lib__hours" aria-label="At dawn, by day, at dusk and by night">
          {(['dawn', 'day', 'dusk', 'night'] as const).map((t) => (
            <span key={t}>
              <Room item={i} minute={MIDDAY[t]} />
              <small>{t}</small>
            </span>
          ))}
        </div>
        <div className="ka-lib__body">
          {i.description && <p className="ka-lib__text">{i.description}</p>}
          {chips}
          <span className="ka-row ka-row--gap">
            <button type="button" className="k-btn k-btn--dark ka-lib__go" onClick={() => startNew({ place: i.id, book: bookOf(i) ?? filter.book })}>
              <Icon name="ff" size={15} />
              Start a scene here
            </button>
            <button type="button" className="k-btn" onClick={() => edit('place', i)}>
              <Icon name="edit" size={15} />
              Edit
            </button>
            {pictures && <DrawButton place={i} />}
            <EarlierPictures item={i} />
          </span>
        </div>
      </article>
    ) : (
      <article key={i.id} className="k-card ka-lib__card ka-lib__card--plot">
        <div className="ka-lib__plothead">
          <Candy icon="spark" color="purple" size={40} />
          <strong className="ka-lib__title">{i.name}</strong>
          {more}
        </div>
        <div className="ka-lib__body">
          <p className="ka-lib__premise">“{i.description || 'No premise yet.'}”</p>
          {i.data.first_message && <p className="ka-lib__text ka-lib__opening">Opening narration · {i.data.first_message.replace(/\*/g, '')}</p>}
          {chips}
          <span className="ka-row ka-row--gap">
            <button type="button" className="k-btn k-btn--dark ka-lib__go" onClick={() => startNew({ plot: i.id, book: bookOf(i) ?? filter.book })}>
              <Icon name="arrow" size={15} />
              Start this plot
            </button>
            <button type="button" className="k-btn" onClick={() => edit('scenario', i)}>
              <Icon name="edit" size={15} />
              Edit
            </button>
          </span>
        </div>
      </article>
    )
  }

  const heading = (
    <span className="ka-lib__head">
      Places and Plots
      <small>Where stories happen, and what they start from. Keep them with a book or a story so they stay findable.</small>
    </span>
  )
  return (
    <>
      <SkyHeader title={heading}>
        <label className="k-search k-glass ka-lib__search">
          <Icon name="search" size={17} />
          <input type="search" placeholder="Search" aria-label="Search places and plots" value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
        <button type="button" className="k-btn k-btn--dark k-btn--lg" onClick={() => edit('place')}>
          <Icon name="plus" size={17} />
          New place
        </button>
        <button type="button" className="k-btn k-btn--lg" onClick={() => edit('scenario')}>
          <Icon name="spark" size={17} />
          New plot
        </button>
      </SkyHeader>
      <ErrorLine error={error} />
      <div className="ka-lib">
        <nav className="k-card ka-lib__filters" aria-label="Show">
          <button type="button" className="ka-lib__filter is-top" aria-pressed={!filter.book && !filter.story && !filter.loose} onClick={() => setFilter({})}>
            <Icon name="grid" size={16} />
            Everything
            <span>{all.length}</span>
          </button>
          <span className="k-eyebrow ka-lib__label">Books</span>
          {(books ?? []).map((b) => (
            <div key={b.id} className="ka-stack ka-stack--tight">
              <button type="button" className="ka-lib__filter" aria-pressed={filter.book === b.id} onClick={() => setFilter({ book: b.id })}>
                <Icon name="book" size={16} />
                {b.title}
                <span>{count((i) => bookOf(i) === b.id)}</span>
              </button>
              {played.filter((s) => s.book?.id === b.id).map((s) => (
                <button key={s.id} type="button" className="ka-lib__filter is-story" aria-pressed={filter.story === s.id} onClick={() => setFilter({ story: s.id })}>
                  <Icon name="chat" size={15} />
                  {s.title}
                  <span>{count((i) => inStory(i, s.id))}</span>
                </button>
              ))}
            </div>
          ))}
          <button type="button" className="ka-lib__filter" aria-pressed={!!filter.loose} onClick={() => setFilter({ loose: true })}>
            <Icon name="alert" size={16} />
            Not in a book
            <span>{count((i) => !bookOf(i))}</span>
          </button>
          {people.length > 0 && <span className="k-eyebrow ka-lib__label">Characters</span>}
          <span className="ka-lib__people">
            {people.map((c) => (
              <button key={c.id} type="button" className="ka-lib__person" aria-pressed={who === c.id} onClick={() => setWho((w) => (w === c.id ? undefined : c.id))}>
                <Avatar item={c} size={26} />
                {c.name}
              </button>
            ))}
          </span>
          <a className="ka-lib__newbook" href={href('/books')}>
            <Icon name="plus" size={15} />
            New book
          </a>
        </nav>
        <div className="ka-lib__main">
          <div className="ka-lib__bar">
            <span className="ka-lib__tabs" role="tablist" aria-label="Kind">
              {([['all', 'All', ''], ['place', 'Places', 'map-pin'], ['scenario', 'Plots', 'spark']] as const).map(([k, label, icon]) => (
                <button key={k} type="button" role="tab" className="ka-lib__tab" aria-selected={tab === k} onClick={() => setTab(k)}>
                  {icon && <Icon name={icon} size={14} />}
                  {label}
                </button>
              ))}
            </span>
            <span className="ka-row ka-row--gap">
              {whose && (
                <span className="ka-muted ka-small">
                  Showing <strong>{whose}’s</strong> places and plots
                </span>
              )}
              <select className="k-select ka-lib__sort" value={sort} aria-label="Sort" onChange={(e) => setSort(e.target.value as Sort)}>
                <option value="recent">Recently used</option>
                <option value="az">A–Z</option>
                <option value="most">Most used</option>
              </select>
            </span>
          </div>
          {groups.map((g) => {
            const inside = played.filter((s) => g.book && s.book?.id === g.book.id).length
            const places = g.items.filter((i) => i.kind === 'place').length
            const plots = g.items.length - places
            const sub = [
              g.book ? `Book · ${inside} ${inside === 1 ? 'story' : 'stories'}` : 'Link these to a book or a story to keep them findable',
              `${places} ${places === 1 ? 'place' : 'places'}`,
              `${plots} ${plots === 1 ? 'plot' : 'plots'}`,
            ]
            return (
              <section key={g.book?.id ?? 'loose'} className="ka-lib__group" aria-label={g.book?.title ?? 'Not in a book'}>
                <header className="ka-lib__grouphead">
                  <Candy icon={g.book ? 'book' : 'alert'} color={g.book ? 'blue' : 'orange'} size={40} />
                  <span className="ka-stack ka-stack--tight">
                    <strong>{g.book?.title ?? 'Not in a book'}</strong>
                    <span className="ka-muted ka-small">{sub.join(' · ')}</span>
                  </span>
                </header>
                <div className="ka-lib__grid">{g.items.map(card)}</div>
              </section>
            )
          })}
          {!groups.length && (
            <p className="ka-muted">
              {all.length ? 'Nothing here with those filters.' : 'No places or plots yet. A place is where a story happens; a plot is what it starts from.'}
            </p>
          )}
        </div>
      </div>

      <ItemDialog key={`item-${editing.n}`} open={editing.open} kind={editing.kind} item={editing.item} fileTo={filter} onClose={() => setEditing((e) => ({ ...e, open: false }))} />
      <LinkDialog key={`link-${linking.n}`} item={linking.item} books={books ?? []} stories={played} onClose={() => setLinking((l) => ({ n: l.n }))} />
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

/** Link a place or a plot to a book, to stories, and to the characters who know it, by hand. */
function LinkDialog({ item, books, stories, onClose }: { item?: Item; books: Book[]; stories: StorySummary[]; onClose: () => void }) {
  const { items, reload } = useLibrary()
  const had = item?.data.links ?? {}
  const [book, setBook] = useState(had.book)
  const [picked, setPicked] = useState(had.stories ?? [])
  const [who, setWho] = useState(had.characters ?? [])
  const [run, error, busy] = useAction()
  const toggle = (list: number[], id: number) => (list.includes(id) ? list.filter((x) => x !== id) : [...list, id])
  const characters = items.filter((i) => i.kind === 'character' && !i.data.persona)
  const save = () =>
    run(async () => {
      await api(`/library/${item!.id}`, 'PATCH', { data: { ...item!.data, links: { book, stories: picked, characters: who } } })
      reload()
      onClose()
    })
  return (
    <Dialog open={!!item} onClose={onClose} title={`Link “${item?.name ?? ''}” to…`}>
      <form
        className="ka-form"
        onSubmit={(e) => {
          e.preventDefault()
          save()
        }}
      >
        <Field label="Book">
          <select className="k-select" value={book ?? ''} onChange={(e) => setBook(e.target.value ? Number(e.target.value) : undefined)}>
            <option value="">No book</option>
            {books.map((b) => (
              <option key={b.id} value={b.id}>{b.title}</option>
            ))}
          </select>
        </Field>
        <fieldset className="ka-lib__fieldset">
          <legend>Stories</legend>
          {stories.filter((s) => !book || s.book?.id === book || picked.includes(s.id)).map((s) => (
            <label key={s.id} className="ka-row ka-row--gap">
              <input type="checkbox" checked={picked.includes(s.id)} onChange={() => setPicked((p) => toggle(p, s.id))} />
              {s.title}
            </label>
          ))}
        </fieldset>
        <fieldset className="ka-lib__fieldset">
          <legend>Characters who know it</legend>
          <span className="ka-lib__people">
            {characters.map((c) => (
              <button key={c.id} type="button" className="ka-lib__person" aria-pressed={who.includes(c.id)} onClick={() => setWho((w) => toggle(w, c.id))}>
                <Avatar item={c} size={26} />
                {c.name}
              </button>
            ))}
          </span>
        </fieldset>
        <ErrorLine error={error} />
        <div className="ka-row ka-row--end">
          <button type="button" className="k-btn" onClick={onClose}>Cancel</button>
          <button className="k-btn k-btn--dark" disabled={busy}>
            <Icon name="check" size={16} />
            Link
          </button>
        </div>
      </form>
    </Dialog>
  )
}
