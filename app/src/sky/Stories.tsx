// Stories (H1–H6): docs/handoff/kataki-handoff/SCREENS.md › /stories.
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { api, download, type ActivityEvent, type Person, type StorySummary } from '../api'
import { said } from '../characters'
import { K } from '../ds'
import { face, scenery, useLibrary, useLoad, utc } from '../hooks'
import { Overlay, toast } from '../overlay'
import { relative, t, type Key } from '../strings'

type Sort = 'played' | 'written' | 'time' | 'name'
const SORTS: Sort[] = ['played', 'written', 'time', 'name']
const sortLabel = (s: Sort) => t(`stories.sort.${s}` as Key)
const ORDER: Record<Sort, (a: StorySummary, b: StorySummary) => number> = {
  played: (a, b) => utc(b.last_at) - utc(a.last_at),
  written: (a, b) => utc(b.created_at) - utc(a.created_at),
  time: (a, b) => b.story_time - a.story_time,
  name: (a, b) => a.title.localeCompare(b.title),
}
const quoted = said

export default function Stories() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const by = params.get('by') === 'character' ? 'character' : 'story'
  const { byId } = useLibrary()
  const [stories, reload] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [settings] = useLoad(() => api<{ persona?: number }>('/settings'), [])
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [sort, setSort] = useState<Sort>('played')
  const [picked, setPicked] = useState<number>()
  const [gone, setGone] = useState<number[]>([]) // deleted, still inside their Undo
  const [open, setOpen] = useState<'rename' | 'delete' | 'export' | null>(null)

  const all = (stories ?? []).filter((s) => !gone.includes(s.id))
  const books = [...new Map(all.flatMap((s) => (s.book ? [[s.book.id, s.book.title] as const] : []))).entries()]
  const personas = [...new Map(all.flatMap((s) => (s.persona?.lib_item_id && s.persona.lib_item_id !== settings?.persona ? [[s.persona.lib_item_id, s.persona.name] as const] : []))).entries()]
  // unfinished: your line is the last one, still waiting for its answer
  const unfinished = (s: StorySummary) => !!s.last_line && !!s.persona && s.last_line.speaker === s.persona.name
  const chips: [string, string, number][] = [
    ['all', t('stories.all'), all.length],
    ['pinned', t('stories.pinned'), all.filter((s) => s.pinned).length],
    ...books.map(([id, title]) => [`book:${id}`, title, all.filter((s) => s.book?.id === id).length] as [string, string, number]),
    ...personas.map(([id, name]) => [`as:${id}`, t('stories.as', { name }), all.filter((s) => s.persona?.lib_item_id === id).length] as [string, string, number]),
    ['unfinished', t('stories.unfinished'), all.filter(unfinished).length],
  ]
  const q = query.trim().toLowerCase()
  const shown = all
    .filter((s) => filter === 'all' ? true : filter === 'pinned' ? s.pinned : filter === 'unfinished' ? unfinished(s)
      : filter.startsWith('book:') ? s.book?.id === Number(filter.slice(5)) : s.persona?.lib_item_id === Number(filter.slice(3)))
    .filter((s) => !q || [s.title, s.book?.title, s.last_line?.text, ...s.cast.map((c) => c.name)].some((x) => x?.toLowerCase().includes(q)))
    .sort(ORDER[sort])
  const current = shown.find((s) => s.id === picked) ?? shown[0]

  const head = (
    <div className="pg-head">
      <div className="row" style={{ gap: 20, alignItems: 'center' }}>
        <h1 className="pg-title">{t('stories.title')}</h1>
        <K.Segmented label={t('stories.by')} size="sm" options={[t('stories.byStory'), t('stories.byCharacter')]}
          value={by === 'character' ? t('stories.byCharacter') : t('stories.byStory')}
          onChange={(v) => setParams(v === t('stories.byCharacter') ? { by: 'character' } : {}, { replace: true })} />
      </div>
      <div className="row" style={{ gap: 12 }}>
        <div style={{ width: 300 }}><K.SearchField placeholder={t('stories.find')} label={t('stories.find')} shortcut="/" value={query} onChange={setQuery} /></div>
        <K.Button variant="primary" icon="plus" href="/stories/new">{t('stories.new')}</K.Button>
      </div>
    </div>
  )

  if (stories && !all.length) {
    return (
      <main className="app__main" aria-label={t('stories.title')} style={{ gap: 20 }}>
        {head}
        <div style={{ maxWidth: 640, paddingTop: 60 }}>
          <K.EmptyState icon="chat" eyebrow={t('stories.title')} title={t('stories.empty.title')}
            actions={[<K.Button key="n" variant="primary" size="sm" icon="plus" href="/stories/new">{t('stories.new')}</K.Button>]}>
            {t('stories.empty.body')}
          </K.EmptyState>
        </div>
      </main>
    )
  }

  const card = (s: StorySummary, compact = false) => (
    <div key={s.id} role="listitem" onClick={() => setPicked(s.id)} onDoubleClick={() => navigate(`/story/${s.id}`)}
      onKeyDown={(e) => e.key === 'Enter' && setPicked(s.id)} tabIndex={0} style={{ cursor: 'pointer' }}>
      <K.StoryCard title={s.title} book={s.book?.title ?? t('home.noBook')} pinned={s.pinned} selected={s.id === current?.id} compact={compact}
        people={s.cast.map((c) => { const f = face(byId.get(c.lib_item_id ?? -1), c.name); return { who: f.who, src: f.src, name: c.name } })}
        quote={s.last_line ? quoted(s.last_line.text) : t('home.noLine')} when={relative(utc(s.last_at))} storyTime={s.date} />
    </div>
  )
  // By character: everyone who is in a story, with their stories under them
  const people = [...new Map(shown.flatMap((s) => s.cast.map((c) => [c.lib_item_id ?? -c.id, c] as const))).values()]

  return (
    <main className="app__main" aria-label={t('stories.title')} style={{ gap: 20 }}>
      {head}
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div className="row row--wrap" style={{ gap: 8 }}>
          {chips.map(([id, label, n]) => (
            <K.Chip key={id} size="sm" count={n} icon={id === 'pinned' ? 'pushpin' : undefined} pressed={filter === id} onPress={() => setFilter(id)}>{label}</K.Chip>
          ))}
        </div>
        <div style={{ width: 200 }}>
          <K.Select label="" options={SORTS.map(sortLabel)} value={sortLabel(sort)} onChange={(v) => setSort(SORTS.find((s) => sortLabel(s) === v) ?? 'played')} />
        </div>
      </div>
      <div className="st-grid">
        <div className="st-list" role="list" aria-label={t('stories.title')}>
          {!shown.length && <p className="t-meta">{t('stories.none')}</p>}
          {by === 'story' ? shown.map((s) => card(s)) : people.map((c) => {
            const theirs = shown.filter((s) => s.cast.some((x) => x.id === c.id || (c.lib_item_id && x.lib_item_id === c.lib_item_id)))
            const f = face(byId.get(c.lib_item_id ?? -1), c.name)
            return (
              <div key={c.id} className="col" style={{ gap: 10 }}>
                <div className="st-who"><K.Avatar who={f.who} src={f.src} name={c.name} size={30} /><K.StoryName size="row">{c.name}</K.StoryName>
                  <span className="t-meta">{t('stories.count', { n: theirs.length })}</span></div>
                {theirs.map((s) => card(s, true))}
              </div>
            )
          })}
        </div>
        {current && <Preview key={current.id} story={current} onRename={() => setOpen('rename')} onExport={() => setOpen('export')} onDelete={() => setOpen('delete')}
          onPin={() => api(`/stories/${current.id}`, 'PATCH', { pinned: !current.pinned }).then(reload)} />}
      </div>

      {current && open === 'rename' && <Rename story={current} onClose={() => setOpen(null)} onDone={reload} />}
      {current && open === 'export' && <Export story={current} onClose={() => setOpen(null)} />}
      {current && open === 'delete' && (
        <Delete story={current} onClose={() => setOpen(null)} onExport={() => setOpen('export')}
          onDelete={() => {
            const s = current
            setOpen(null)
            setGone((g) => [...g, s.id])
            // soft for the length of its Undo, then real (DATA.md › Rules 2)
            toast(t('toast.deleted', { story: s.title }), {
              action: t('toast.undo'),
              onAction: () => setGone((g) => g.filter((x) => x !== s.id)),
              onDone: () => api(`/stories/${s.id}`, 'DELETE').then(reload),
            })
          }} />
      )}
    </main>
  )
}

function Preview({ story, onRename, onExport, onDelete, onPin }: {
  story: StorySummary; onRename: () => void; onExport: () => void; onDelete: () => void; onPin: () => void
}) {
  const { byId } = useLibrary()
  const [people] = useLoad(() => api<Person[]>(`/stories/${story.id}/people`), [story.id])
  const [events] = useLoad(() => api<ActivityEvent[]>(`/activity?story_id=${story.id}&limit=6`), [story.id])
  const place = byId.get(story.place?.lib_item_id ?? -1)
  const art = scenery(place)
  const fresh = (events ?? []).filter((e) => e.new).slice(0, 2)
  const places = story.places.map((id) => byId.get(id)).filter((p) => !!p)
  return (
    <div className="st-preview">
      <K.StoryPreview title={story.title} placeAlt={story.place?.name} place={art.place} placeSrc={art.src}
        meta={t('stories.meta', { book: story.book?.title ?? t('home.noBook'), time: story.date, place: story.place?.name ?? 'none' })}
        lastPlayed={t('stories.lastPlayed', { relative: relative(utc(story.last_at)) })} continueHref={`/story/${story.id}`}
        cast={story.cast.map((c) => {
          const p = people?.find((x) => x.id === c.id)
          const f = face(byId.get(c.lib_item_id ?? -1), c.name)
          return { who: f.who, src: f.src, name: c.name, memories: t('stories.memoriesHere', { n: p?.remembers ?? 0 }), pill: c.present ? undefined : t('stories.away') }
        })}>
        <div className="col" style={{ gap: 10 }}>
          {fresh.length > 0 && <K.Eyebrow>{t('stories.newSince')}</K.Eyebrow>}
          {fresh.map((e) => {
            const who = e.who[0]
            const f = face(byId.get(who?.lib_item_id ?? -1), who?.name)
            return <K.EventCard key={e.key} who={f.who} avatarSrc={f.src} name={who?.name ?? ''} event={t(`event.${e.kind}` as Key)} tone="warm" memory={`“${e.text}”`} meta={e.sub} />
          })}
          {places.length > 0 && <K.Eyebrow>{t('stories.where')}</K.Eyebrow>}
          {places.length > 0 && <div className="row row--wrap" style={{ gap: 8 }}>{places.map((p) => <K.Chip key={p.id} icon="map-pin" size="sm">{p.name}</K.Chip>)}</div>}
          <div className="row" style={{ gap: 8, paddingTop: 6 }}>
            <span data-rename><K.Button size="sm" variant="ghost" icon="edit" onClick={onRename}>{t('stories.rename')}</K.Button></span>
            <K.Button size="sm" variant="ghost" icon="download" onClick={onExport}>{t('stories.export')}</K.Button>
            <K.Button size="sm" variant="ghost" icon="pushpin" onClick={onPin}>{t(story.pinned ? 'stories.unpin' : 'stories.pin')}</K.Button>
            <K.Button size="sm" variant="ghost" icon="trash" onClick={onDelete}>{t('stories.delete')}</K.Button>
          </div>
        </div>
      </K.StoryPreview>
    </div>
  )
}

function Rename({ story, onClose, onDone }: { story: StorySummary; onClose: () => void; onDone: () => void }) {
  const [name, setName] = useState(story.title)
  const save = () => {
    if (!name.trim()) return
    api(`/stories/${story.id}`, 'PATCH', { title: name.trim() }).then(() => { onDone(); onClose() })
  }
  return (
    <Overlay onClose={onClose} at={document.querySelector('[data-rename]')}>
      <form onSubmit={(e) => { e.preventDefault(); save() }}>
        <K.Popover title={t('rename.title')} onClose={onClose} actions={[
          <K.Button key="c" size="sm" variant="ghost" onClick={onClose}>{t('rename.cancel')}</K.Button>,
          <K.Button key="s" size="sm" variant="primary" disabled={!name.trim()} onClick={save}>{t('rename.save')}</K.Button>,
        ]}>
          <K.TextField label={t('rename.name')} story max={60} value={name} onChange={setName} hint={t('rename.hint')} />
        </K.Popover>
      </form>
    </Overlay>
  )
}

export function Delete({ story, onClose, onExport, onDelete }: { story: Pick<StorySummary, 'id' | 'title' | 'cast'>; onClose: () => void; onExport: () => void; onDelete: () => void }) {
  const names = new Intl.ListFormat('en', { type: 'conjunction' }).format(story.cast.map((c) => c.name))
  const [lines] = useLoad(() => api<unknown[]>(`/stories/${story.id}/messages`).then((m) => m.length), [story.id])
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="trash" tone="bad" title={t('delete.title', { story: story.title })} onClose={onClose}
        description={t('delete.body', { lines: lines ?? 0, names })} note={t('delete.note')}
        actions={[
          <K.Button key="k" variant="ghost" onClick={onClose}>{t('delete.keep')}</K.Button>,
          <K.Button key="e" variant="secondary" icon="download" onClick={onExport}>{t('delete.exportFirst')}</K.Button>,
          <K.Button key="d" variant="danger" onClick={onDelete}>{t('delete.confirm')}</K.Button>,
        ]} />
    </Overlay>
  )
}

export function Export({ story, onClose }: { story: Pick<StorySummary, 'id' | 'title'>; onClose: () => void }) {
  const [as, setAs] = useState('markdown')
  const [busy, setBusy] = useState(false)
  const go = async () => {
    setBusy(true)
    try {
      const name = await download(`/stories/${story.id}/export?as=${as}`)
      toast(t('toast.exported', { name }), {}, 5000)
      onClose()
    } finally {
      setBusy(false)
    }
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="download" title={t('export.title', { story: story.title })} description={t('export.body')} onClose={onClose}
        note={t('export.note')} actions={[
          <K.Button key="c" variant="ghost" onClick={onClose}>{t('export.cancel')}</K.Button>,
          <K.Button key="e" variant="primary" loading={busy} onClick={go}>{t('export.go')}</K.Button>,
        ]}>
        <K.RadioGroup label={t('export.as')} value={as} onChange={setAs} options={[
          { value: 'markdown', label: t('export.md'), description: t('export.mdSub') },
          { value: 'jsonl', label: t('export.jsonl'), description: t('export.jsonlSub') },
        ]} />
      </K.Dialog>
    </Overlay>
  )
}
