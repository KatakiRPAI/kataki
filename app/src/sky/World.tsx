// World (I1–I8): places and plots, filed under books and stories.
import { useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router'
import { api, mediaUrl, upload, type Book, type Item, type StorySummary } from '../api'
import { isCharacter } from '../characters'
import { K } from '../ds'
import { face, scenery, useLibrary, useLoad, utc } from '../hooks'
import { openMenu, Overlay, toast, withMenu, type MenuItem } from '../overlay'
import { t, type Key } from '../strings'
import Top from './Top'

type Time = 'dawn' | 'day' | 'dusk' | 'night'
const TIMES: Time[] = ['dawn', 'day', 'dusk', 'night']
type Show = 'all' | 'places' | 'plots'
type Sort = 'used' | 'made' | 'name'
type Where = 'all' | 'none' | `book:${number}` | `story:${number}`
const unstar = (s = '') => s.replace(/\*/g, '').trim()

export default function World() {
  const navigate = useNavigate()
  const { items, byId, reload } = useLibrary()
  const [stories, reloadStories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [books, reloadBooks] = useLoad(() => api<Book[]>('/books'), [])
  const [where, setWhere] = useState<Where>('all')
  const [who, setWho] = useState<number>()
  const [show, setShow] = useState<Show>('all')
  const [sort, setSort] = useState<Sort>('used')
  const [open, setOpen] = useState<{ kind: 'place' | 'plot' | 'newPlace' | 'newPlot' | 'newBook' | 'file'; item?: Item } | null>(null)

  const places = items.filter((i) => i.kind === 'place' && !i.data.unlisted)
  const plots = items.filter((i) => i.kind === 'scenario')
  const usedIn = (i: Item) => (stories ?? []).filter((s) => (i.kind === 'place' ? s.places.includes(i.id) || s.place?.lib_item_id === i.id : s.plot_id === i.id))
  const bookOf = (i: Item) => i.data.links?.book ?? usedIn(i).find((s) => s.book)?.book?.id
  const storiesOf = (i: Item) => [...new Set([...(i.data.links?.stories ?? []), ...usedIn(i).map((s) => s.id)])]
  const knownBy = (i: Item) => items.filter((c) => isCharacter(c) && (c.data.places?.includes(i.id) || usedIn(i).some((s) => s.cast.some((x) => x.lib_item_id === c.id))))
  const inWhere = (i: Item) => where === 'all' ? true : where === 'none' ? !bookOf(i) : where.startsWith('book:') ? bookOf(i) === Number(where.slice(5)) : storiesOf(i).includes(Number(where.slice(6)))
  const order: Record<Sort, (a: Item, b: Item) => number> = {
    used: (a, b) => Math.max(0, ...usedIn(b).map((s) => utc(s.last_at))) - Math.max(0, ...usedIn(a).map((s) => utc(s.last_at))),
    made: (a, b) => utc(b.created_at) - utc(a.created_at),
    name: (a, b) => a.name.localeCompare(b.name),
  }
  const pool = [...(show !== 'plots' ? places : []), ...(show !== 'places' ? plots : [])]
  const shown = pool.filter(inWhere).filter((i) => !who || knownBy(i).some((c) => c.id === who)).sort(order[sort])
  const groups: [string, number | undefined, Item[]][] = [
    ...(books ?? []).map((b) => [b.title, b.id, shown.filter((i) => bookOf(i) === b.id)] as [string, number, Item[]]),
    [t('w.elsewhere'), undefined, shown.filter((i) => !bookOf(i))] as [string, undefined, Item[]],
  ].filter(([, , list]) => list.length > 0)
  const bookStories = (b: Book) => (stories ?? []).filter((s) => s.book?.id === b.id)
  const count = (w: Where) => [...places, ...plots].filter((i) => (w === 'all' ? true : w === 'none' ? !bookOf(i) : w.startsWith('book:') ? bookOf(i) === Number(w.slice(5)) : storiesOf(i).includes(Number(w.slice(6))))).length
  const crumbs = [t('w.title'), ...(where.startsWith('book:') ? [books?.find((b) => b.id === Number(where.slice(5)))?.title ?? ''] : where.startsWith('story:') ? [stories?.find((s) => s.id === Number(where.slice(6)))?.title ?? ''] : where === 'none' ? [t('w.noBook')] : [])]
  const done = () => { reload(); reloadBooks(); reloadStories() }
  const placeMenu = (p: Item): MenuItem[] => [
    { label: t('pl.newStory'), icon: 'plus', onSelect: () => navigate(`/stories/new?place=${p.id}`) },
    { label: t('pl.edit'), icon: 'edit', onSelect: () => setOpen({ kind: 'newPlace', item: p }) },
    { label: t('w.fileIt'), icon: 'book', onSelect: () => setOpen({ kind: 'file', item: p }) },
    { label: t('pl.duplicate'), icon: 'layers', onSelect: () => api('/library', 'POST', { kind: p.kind, name: `${p.name} (2)`, description: p.description, private: p.private, data: p.data, tags: p.tags }).then(reload) },
    { divider: true },
    { label: t(p.kind === 'place' ? 'pl.delete' : 'pt.delete'), detail: t('pl.deleteDetail'), icon: 'trash', danger: true, onSelect: () => remove(p) },
  ]
  const [gone, setGone] = useState<number[]>([])
  const remove = (p: Item) => {
    setGone((g) => [...g, p.id])
    toast(t('toast.placeDeleted', { name: p.name }), { action: t('toast.undo'), onAction: () => setGone((g) => g.filter((x) => x !== p.id)), onDone: () => api(`/library/${p.id}`, 'DELETE').then(reload) })
  }

  const head = (
    <div className="pg-head">
      <div><h1 className="pg-title">{t('w.title')}</h1><p className="pg-sub">{t('w.sub')}</p></div>
      <div className="row" style={{ gap: 10 }}>
        <K.Button icon="book" onClick={() => setOpen({ kind: 'newBook' })}>{t('w.newBook')}</K.Button>
        <K.Button icon="plus" onClick={() => setOpen({ kind: 'newPlot' })}>{t('w.newPlot')}</K.Button>
        <K.Button variant="primary" icon="map-pin" onClick={() => setOpen({ kind: 'newPlace' })}>{t('w.newPlace')}</K.Button>
      </div>
    </div>
  )
  const dialogs = (
    <>
      {open?.kind === 'place' && open.item && <PlaceDetail p={open.item} stories={usedIn(open.item)} knownBy={knownBy(open.item)} onClose={() => setOpen(null)} menu={() => placeMenu(open.item!)} />}
      {open?.kind === 'plot' && open.item && <PlotDetail p={open.item} book={books?.find((b) => b.id === bookOf(open.item!))?.title} stories={usedIn(open.item)} onClose={() => setOpen(null)} menu={() => placeMenu(open.item!)} />}
      {open?.kind === 'newPlace' && <NewPlace item={open.item} books={books ?? []} onClose={() => setOpen(null)} onDone={done} />}
      {open?.kind === 'newPlot' && <NewPlot item={open.item} books={books ?? []} places={places} onClose={() => setOpen(null)} onDone={done} />}
      {open?.kind === 'newBook' && <NewBook stories={(stories ?? []).filter((s) => !s.book)} loose={[...places, ...plots].filter((i) => !bookOf(i))} onClose={() => setOpen(null)} onDone={done} />}
      {open?.kind === 'file' && open.item && <FileIt item={open.item} books={books ?? []} stories={stories ?? []} people={items.filter(isCharacter)} onClose={() => setOpen(null)} onDone={done} />}
    </>
  )

  if (!places.length && !plots.length) {
    return (
      <main className="app__main" aria-label={t('w.title')} style={{ gap: 24 }}>
        {head}
        <div style={{ maxWidth: 680, paddingTop: 40 }}>
          <K.EmptyState icon="map" eyebrow={t('w.title')} title={t('w.empty.title')} actions={[
            <K.Button key="p" size="sm" variant="primary" icon="map-pin" onClick={() => setOpen({ kind: 'newPlace' })}>{t('w.newPlace')}</K.Button>,
            <K.Button key="t" size="sm" icon="plus" onClick={() => setOpen({ kind: 'newPlot' })}>{t('w.newPlot')}</K.Button>,
            <K.Button key="l" size="sm" variant="ghost" onClick={() => navigate('/characters')}>{t('w.empty.lorebook')}</K.Button>,
          ]}>{t('w.empty.body')}</K.EmptyState>
        </div>
        {dialogs}
      </main>
    )
  }

  return (
    <main className="app__main" aria-label={t('w.title')} style={{ gap: 24 }}>
      <Top />
      {head}
      <div className="w-grid">
        <nav aria-label={t('w.books')} className="tree">
          <button type="button" aria-current={where === 'all' ? 'page' : undefined} onClick={() => setWhere('all')}><K.Icon name="globe" size={16} />{t('w.everything')}<span className="tree__n">{count('all')}</span></button>
          {(books ?? []).length > 0 && <div className="tree__h">{t('w.books')}</div>}
          {(books ?? []).map((b) => (
            <div key={b.id}>
              <button type="button" className="tree__book" aria-current={where === `book:${b.id}` ? 'page' : undefined} onClick={() => setWhere(`book:${b.id}`)}>
                <K.Icon name="book" size={16} />{b.title}<span className="tree__n">{count(`book:${b.id}`)}</span>
              </button>
              {bookStories(b).map((s) => (
                <button key={s.id} type="button" className="tree__l2" aria-current={where === `story:${s.id}` ? 'page' : undefined} onClick={() => setWhere(`story:${s.id}`)}>
                  {s.title}<span className="tree__n">{count(`story:${s.id}`)}</span>
                </button>
              ))}
            </div>
          ))}
          <button type="button" aria-current={where === 'none' ? 'page' : undefined} onClick={() => setWhere('none')}><K.Icon name="layers" size={16} />{t('w.noBook')}<span className="tree__n">{count('none')}</span></button>
          <div className="tree__h">{t('w.whoKnows')}</div>
          <div className="row row--wrap" style={{ gap: 6, padding: '0 6px' }}>
            {items.filter(isCharacter).map((c) => <K.Chip key={c.id} {...face(c)} size="sm" pressed={who === c.id} onPress={() => setWho(who === c.id ? undefined : c.id)}>{c.name}</K.Chip>)}
          </div>
        </nav>
        <div className="col" style={{ gap: 22, minWidth: 0 }}>
          <K.Breadcrumbs items={crumbs} />
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <K.Tabs label={t('w.show')} size="sm" tabs={[t('w.all'), t('w.places'), t('w.plots')]} value={t(`w.${show}` as Key)}
              counts={{ [t('w.all')]: places.length + plots.length, [t('w.places')]: places.length, [t('w.plots')]: plots.length }}
              onChange={(v) => setShow(v === t('w.places') ? 'places' : v === t('w.plots') ? 'plots' : 'all')} />
            <div style={{ width: 190 }}>
              <K.Select label="" options={(['used', 'made', 'name'] as Sort[]).map((s) => t(`w.sort.${s}` as Key))} value={t(`w.sort.${sort}` as Key)}
                onChange={(v) => setSort((['used', 'made', 'name'] as Sort[]).find((s) => t(`w.sort.${s}` as Key) === v) ?? 'used')} />
            </div>
          </div>
          {!groups.length && <p className="t-meta">{t('w.nothingHere')}</p>}
          {groups.map(([title, bookId, list]) => (
            <section key={title} className="sec" aria-label={title}>
              <div className="row" style={{ gap: 10 }}><K.Icon name={bookId ? 'book' : 'layers'} size={16} color="var(--faint)" /><K.StoryName size="row">{title}</K.StoryName></div>
              <div className="wgrid">
                {list.filter((i) => !gone.includes(i.id)).map((i) => {
                  const s = scenery(i)
                  const people = knownBy(i).map((c) => ({ ...face(c) }))
                  const n = usedIn(i).length
                  return (
                    <div key={i.id} className="w-card" {...withMenu(() => placeMenu(i))}>
                      <button type="button" className="w-card__open" aria-label={i.name} onClick={() => setOpen({ kind: i.kind === 'place' ? 'place' : 'plot', item: i })} />
                      {i.kind === 'place'
                        ? <K.PlaceCard place={s.place} src={s.src} name={i.name} blurb={i.description} time={i.data.time as Time | undefined} people={people} links={t('w.usedIn', { n })} alt={i.data.alt ?? i.name} />
                        : <K.PlotCard quote={`“${unstar(i.description)}”`} opening={t('w.opens', { line: unstar(i.data.first_message) })} people={people} book={t('w.usedIn', { n })} />}
                      {!bookOf(i) && i.kind === 'place' && <div className="w-card__file"><K.Button size="sm" variant="ghost" icon="book" onClick={() => setOpen({ kind: 'file', item: i })}>{t('w.fileIt')}</K.Button></div>}
                      <span className="w-card__more" onClick={(e) => openMenu(e.currentTarget, placeMenu(i))}><K.IconButton icon="dots" label={t('chars.more', { name: i.name })} size="sm" variant="glass" /></span>
                    </div>
                  )
                })}
              </div>
            </section>
          ))}
        </div>
      </div>
      {dialogs}
    </main>
  )
}

function Sheet({ onClose, children }: { onClose: () => void; children: ReactNode }) {
  return <Overlay onClose={onClose}><div className="pf-sheet"><section className="dlg" role="dialog" aria-modal="true">{children}</section></div></Overlay>
}

/** I3: a place, and everything that has happened there. */
function PlaceDetail({ p, stories, knownBy, onClose, menu }: { p: Item; stories: StorySummary[]; knownBy: Item[]; onClose: () => void; menu: () => MenuItem[] }) {
  const navigate = useNavigate()
  const s = scenery(p)
  return (
    <Sheet onClose={onClose}>
      <div className="dlg__head"><div className="dlg__titles"><h2 className="dlg__title">{p.name}</h2></div><K.IconButton icon="x" label="Close" size="sm" onClick={onClose} /></div>
      <div className="dlg__body pf-sheet__body">
        {(s.src || s.place) && <K.Still place={s.place} src={s.src} caption={p.name} height={220} alt={p.data.alt ?? p.name} />}
        {p.data.time && <K.TimeStrip value={p.data.time as Time} />}
        {p.description && <p className="pf-text">{p.description}</p>}
        {!!p.data.exits?.length && <dl className="pdl"><dt>{t('pl.exits')}</dt><dd>{p.data.exits.join(' · ')}</dd></dl>}
        {knownBy.length > 0 && <dl className="pdl"><dt>{t('pl.who')}</dt><dd><K.AvatarStack people={knownBy.map((c) => ({ ...face(c) }))} size={28} /></dd></dl>}
        {stories.length > 0 && (
          <dl className="pdl"><dt>{t('pl.stories')}</dt>
            <dd>{stories.map((st) => <K.ListRow key={st.id} story title={st.title} subtitle={st.date} href={`/story/${st.id}`} />)}</dd>
          </dl>
        )}
        <div className="row" style={{ gap: 8 }}>
          <K.Button variant="primary" icon="plus" onClick={() => navigate(`/stories/new?place=${p.id}`)}>{t('pl.newStory')}</K.Button>
          <span onClick={(e) => openMenu(e.currentTarget, menu())}><K.IconButton icon="dots" label={t('chars.more', { name: p.name })} /></span>
        </div>
      </div>
    </Sheet>
  )
}

/** I4: a plot: its hook, how it opens, what only the narrator knows. */
function PlotDetail({ p, book, stories, onClose, menu }: { p: Item; book?: string; stories: StorySummary[]; onClose: () => void; menu: () => MenuItem[] }) {
  const navigate = useNavigate()
  const { byId } = useLibrary()
  const where = p.data.links?.characters ? undefined : byId.get((p.data as { place?: number }).place ?? -1)
  return (
    <Sheet onClose={onClose}>
      <div className="dlg__head">
        <div className="dlg__titles"><h2 className="dlg__title">{p.name}</h2><p className="dlg__desc">{t('pt.meta', { book: book ?? t('w.noBook'), n: stories.length })}</p></div>
        <K.IconButton icon="x" label="Close" size="sm" onClick={onClose} />
      </div>
      <div className="dlg__body pf-sheet__body">
        <p className="plotpick__quote">“{unstar(p.description)}”</p>
        {p.data.first_message && <dl className="pdl"><dt>{t('pt.opens')}</dt><dd>{unstar(p.data.first_message)}</dd></dl>}
        {where && <dl className="pdl"><dt>{t('pt.where')}</dt><dd>{where.name}</dd></dl>}
        {p.private && <K.SecretCard title={t('pt.narrator')}>{p.private}</K.SecretCard>}
        {stories.length > 0 && <dl className="pdl"><dt>{t('pt.usedIn')}</dt><dd>{stories.map((s) => <K.ListRow key={s.id} story title={s.title} href={`/story/${s.id}`} />)}</dd></dl>}
        <div className="row" style={{ gap: 8 }}>
          <K.Button variant="primary" icon="plus" onClick={() => navigate(`/stories/new?plot=${p.id}${where ? `&place=${where.id}` : ''}`)}>{t('pt.newStory')}</K.Button>
          <span onClick={(e) => openMenu(e.currentTarget, menu())}><K.IconButton icon="dots" label={t('chars.more', { name: p.name })} /></span>
        </div>
      </div>
    </Sheet>
  )
}

function BookSelect({ books, value, onChange }: { books: Book[]; value?: number; onChange: (id?: number) => void }) {
  const options: [number | undefined, string][] = [[undefined, t('w.noBook')], ...books.map((b) => [b.id, b.title] as [number, string])]
  return <K.Select label={t('np.file')} icon="book" options={options.map(([, l]) => l)} value={options.find(([id]) => id === value)?.[1]} onChange={(v) => onChange(options.find(([, l]) => l === v)?.[0])} />
}

/** I5: a place: its picture, what it's like, when it's usually seen, the ways out. */
function NewPlace({ item, books, onClose, onDone }: { item?: Item; books: Book[]; onClose: () => void; onDone: () => void }) {
  const [name, setName] = useState(item?.name ?? '')
  const [like, setLike] = useState(item?.description ?? '')
  const [time, setTime] = useState<Time>((item?.data.time as Time) ?? 'dusk')
  const [exits, setExits] = useState((item?.data.exits ?? []).join(', '))
  const [image, setImage] = useState(item?.data.image)
  const [book, setBook] = useState<number | undefined>(item?.data.links?.book)
  const save = async () => {
    const data = { ...(item?.data ?? {}), image, time, exits: exits.split(',').map((x) => x.trim()).filter(Boolean), links: { ...(item?.data.links ?? {}), book } }
    if (item) await api(`/library/${item.id}`, 'PATCH', { name: name.trim(), description: like.trim(), data })
    else await api('/library', 'POST', { kind: 'place', name: name.trim(), description: like.trim(), data })
    onDone()
    onClose()
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="map-pin" size="lg" title={item ? t('np.editTitle', { name: item.name }) : t('np.title')} onClose={onClose}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('np.cancel')}</K.Button>, <K.Button key="m" variant="primary" disabled={!name.trim()} onClick={save}>{t(item ? 'np.save' : 'np.make')}</K.Button>]}>
        <K.TextField label={t('np.name')} required story value={name} onChange={setName} max={60} />
        <div className="row" style={{ gap: 14, alignItems: 'center' }}>
          {image ? <img src={mediaUrl(image)} alt="" className="w-thumb" /> : null}
          <div className="col" style={{ gap: 6, flex: 1 }}>
            <b style={{ fontSize: 13.5 }}>{t('np.picture')}</b><span className="t-meta">{t('np.pictureSub')}</span>
            <div className="row" style={{ gap: 8 }}>
              <label className="k-btn k-btn--secondary k-btn--sm">{t('np.choose')}<input type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={async (e) => { const f = e.target.files?.[0]; if (f) setImage((await upload(f)).name) }} /></label>
              {image && <K.Button size="sm" variant="ghost" onClick={() => setImage(undefined)}>{t('np.remove')}</K.Button>}
            </div>
          </div>
        </div>
        <K.TextArea label={t('np.like')} hint={t('np.likeHint')} story rows={3} value={like} onChange={setLike} />
        <K.Segmented label={t('np.time')} size="sm" options={TIMES.map((x) => t(`ns.time.${x}` as Key))} value={t(`ns.time.${time}` as Key)} onChange={(v) => setTime(TIMES.find((x) => t(`ns.time.${x}` as Key) === v) ?? 'dusk')} />
        <K.TextField label={t('np.exits')} hint={t('np.exitsHint')} value={exits} onChange={setExits} />
        <BookSelect books={books} value={book} onChange={setBook} />
      </K.Dialog>
    </Overlay>
  )
}

/** I6: a plot: the hook, how it opens, and what only the narrator knows. */
function NewPlot({ item, books, places, onClose, onDone }: { item?: Item; books: Book[]; places: Item[]; onClose: () => void; onDone: () => void }) {
  const [name, setName] = useState(item?.name ?? '')
  const [hook, setHook] = useState(item?.description ?? '')
  const [opens, setOpens] = useState(item?.data.first_message ?? '')
  const [secret, setSecret] = useState(item?.private ?? '')
  const [place, setPlace] = useState<number | undefined>((item?.data as { place?: number } | undefined)?.place)
  const [book, setBook] = useState<number | undefined>(item?.data.links?.book)
  const placeOptions: [number | undefined, string][] = [[undefined, t('npl.anywhere')], ...places.map((p) => [p.id, p.name] as [number, string])]
  const save = async () => {
    const data = { ...(item?.data ?? {}), first_message: opens.trim(), place, links: { ...(item?.data.links ?? {}), book } }
    const body = { name: name.trim(), description: hook.trim(), private: secret.trim(), data }
    if (item) await api(`/library/${item.id}`, 'PATCH', body)
    else await api('/library', 'POST', { kind: 'scenario', ...body })
    onDone()
    onClose()
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="quote" size="lg" title={item ? t('np.editTitle', { name: item.name }) : t('npl.title')} onClose={onClose} note={t('npl.note')}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('np.cancel')}</K.Button>, <K.Button key="m" variant="primary" disabled={!name.trim() || !hook.trim()} onClick={save}>{t(item ? 'np.save' : 'npl.make')}</K.Button>]}>
        <K.TextField label={t('npl.name')} required story value={name} onChange={setName} max={60} />
        <K.TextField label={t('npl.hook')} required hint={t('npl.hookHint')} story value={hook} onChange={setHook} max={160} />
        <K.TextArea label={t('npl.opens')} hint={t('npl.opensHint')} story rows={3} value={opens} onChange={setOpens} />
        <K.TextArea label={t('npl.secret')} hint={t('npl.secretHint')} placeholder={t('npl.secretPlaceholder')} rows={3} value={secret} onChange={setSecret} />
        <K.Select label={t('npl.where')} options={placeOptions.map(([, l]) => l)} value={placeOptions.find(([id]) => id === place)?.[1]} onChange={(v) => setPlace(placeOptions.find(([, l]) => l === v)?.[0])} />
        <BookSelect books={books} value={book} onChange={setBook} />
      </K.Dialog>
    </Overlay>
  )
}

/** I7: a book, with the loose stories, places and plots moved in. */
function NewBook({ stories, loose, onClose, onDone }: { stories: StorySummary[]; loose: Item[]; onClose: () => void; onDone: () => void }) {
  const [name, setName] = useState('')
  const [about, setAbout] = useState('')
  const [picked, setPicked] = useState<string[]>([])
  const toggle = (k: string) => setPicked((p) => (p.includes(k) ? p.filter((x) => x !== k) : [...p, k]))
  const make = async () => {
    const book = await api<Book>('/books', 'POST', { title: name.trim(), blurb: about.trim() })
    for (const k of picked) {
      const [kind, id] = k.split(':')
      if (kind === 's') await api(`/stories/${id}`, 'PATCH', { book_id: book.id })
      else { const i = loose.find((x) => x.id === Number(id)); if (i) await api(`/library/${i.id}`, 'PATCH', { data: { ...i.data, links: { ...(i.data.links ?? {}), book: book.id } } }) }
    }
    onDone()
    onClose()
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="book" title={t('nb.title')} onClose={onClose}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('np.cancel')}</K.Button>, <K.Button key="m" variant="primary" disabled={!name.trim()} onClick={make}>{t('nb.make')}</K.Button>]}>
        <K.TextField label={t('nb.name')} required story value={name} onChange={setName} max={60} />
        <K.TextArea label={t('nb.about')} placeholder={t('nb.aboutPlaceholder')} rows={2} value={about} onChange={setAbout} />
        {(stories.length > 0 || loose.length > 0) && (
          <K.Field label={t('nb.move')} hint={t('nb.moveHint')}>
            <div className="card find-list">
              {stories.map((s) => <div key={`s${s.id}`} className="find-row"><K.Checkbox label={s.title} description={t('nb.story')} checked={picked.includes(`s:${s.id}`)} onChange={() => toggle(`s:${s.id}`)} /></div>)}
              {loose.map((i) => <div key={`i${i.id}`} className="find-row"><K.Checkbox label={i.name} description={t(i.kind === 'place' ? 'nb.place' : 'nb.plot')} checked={picked.includes(`i:${i.id}`)} onChange={() => toggle(`i:${i.id}`)} /></div>)}
            </div>
          </K.Field>
        )}
      </K.Dialog>
    </Overlay>
  )
}

/** I8: file a place under a book and stories, and say who knows it. */
function FileIt({ item, books, stories, people, onClose, onDone }: { item: Item; books: Book[]; stories: StorySummary[]; people: Item[]; onClose: () => void; onDone: () => void }) {
  const [book, setBook] = useState<number | undefined>(item.data.links?.book)
  const [story, setStory] = useState<number | undefined>(item.data.links?.stories?.[0])
  const [who, setWho] = useState<number[]>(people.filter((c) => c.data.places?.includes(item.id)).map((c) => c.id))
  const options: [number | undefined, string][] = [[undefined, t('fi.noStory')], ...stories.map((s) => [s.id, s.title] as [number, string])]
  const go = async () => {
    await api(`/library/${item.id}`, 'PATCH', { data: { ...item.data, links: { ...(item.data.links ?? {}), book, stories: story ? [story] : [] } } })
    for (const c of people) {
      const knows = c.data.places?.includes(item.id) ?? false
      if (knows !== who.includes(c.id)) await api(`/library/${c.id}`, 'PATCH', { data: { ...c.data, places: who.includes(c.id) ? [...(c.data.places ?? []), item.id] : (c.data.places ?? []).filter((x) => x !== item.id) } })
    }
    onDone()
    onClose()
  }
  return (
    <Overlay onClose={onClose}>
      <K.Popover title={t('fi.title', { name: item.name })} description={t('fi.body')} width={420} onClose={onClose}
        actions={[<K.Button key="c" size="sm" variant="ghost" onClick={onClose}>{t('np.cancel')}</K.Button>, <K.Button key="f" size="sm" variant="primary" onClick={go}>{t('fi.go')}</K.Button>]}>
        <div className="col" style={{ gap: 12 }}>
          <BookSelect books={books} value={book} onChange={setBook} />
          <K.Select label={t('fi.story')} options={options.map(([, l]) => l)} value={options.find(([id]) => id === story)?.[1]} onChange={(v) => setStory(options.find(([, l]) => l === v)?.[0])} />
          <K.Field label={t('fi.who')}>
            <div className="row row--wrap" style={{ gap: 6 }}>
              {people.map((c) => <K.Chip key={c.id} size="sm" {...face(c)} pressed={who.includes(c.id)} onPress={() => setWho((w) => (w.includes(c.id) ? w.filter((x) => x !== c.id) : [...w, c.id]))}>{c.name}</K.Chip>)}
            </div>
          </K.Field>
        </div>
      </K.Popover>
    </Overlay>
  )
}
