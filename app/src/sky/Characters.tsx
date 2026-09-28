// Characters (D1–D5): docs/handoff/kataki-handoff/SCREENS.md › /characters.
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { api, sendFile, type Item, type Look, type StorySummary } from '../api'
import { isDraft, isPersona, storiesWith, tagline, type Group } from '../characters'
import { K } from '../ds'
import { face, useLibrary, useLoad, utc } from '../hooks'
import { openMenu, Overlay, toast, withMenu } from '../overlay'
import { relative, t, type Key } from '../strings'
import { characterMenu, DeleteCharacter } from './characterActions'
import Top from './Top'

type Filter = 'all' | 'story' | 'fav' | 'drafts' | 'persona'
type Sort = 'played' | 'written' | 'fav' | 'name' | 'most'
const FILTERS: Filter[] = ['all', 'story', 'fav', 'drafts', 'persona']
const SORTS: Sort[] = ['played', 'written', 'fav', 'name', 'most']
const sortLabel = (s: Sort) => t(`chars.s.${s}` as Key)
const list = (names: string[]) => new Intl.ListFormat('en', { type: 'conjunction' }).format(names)

export default function Characters() {
  const navigate = useNavigate()
  const { items, byId, reload } = useLibrary()
  const [stories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [settings, reloadSettings] = useLoad(() => api<{ persona?: number; groups?: Group[]; 'ui.charactersView'?: string }>('/settings'), [])
  const [filter, setFilter] = useState<Filter>('all')
  const [sort, setSort] = useState<Sort>('played')
  const [view, setView] = useState<'grid' | 'list'>()
  const [hidden, setHidden] = useState<number[]>([])
  const [deleting, setDeleting] = useState<Item>()
  const [params] = useSearchParams()
  const [importing, setImporting] = useState(() => params.has('import')) // first run's "Import cards"
  const [grouping, setGrouping] = useState<Group | 'new'>()
  const shownAs = view ?? (settings?.['ui.charactersView'] === 'list' ? 'list' : 'grid')
  const groups = settings?.groups ?? []

  // everyone but the one you're playing as; another persona is a character too ("Also a persona")
  const people = items.filter((i) => i.kind === 'character' && !hidden.includes(i.id) && i.id !== settings?.persona)
  const lastOf = (c: Item) => storiesWith(c, stories)[0]
  const test: Record<Filter, (c: Item) => boolean> = {
    all: () => true, story: (c) => !!lastOf(c), fav: (c) => !!c.data.favourite, drafts: isDraft, persona: isPersona,
  }
  const order: Record<Sort, (a: Item, b: Item) => number> = {
    played: (a, b) => utc(lastOf(b)?.last_at ?? '1970-01-01 00:00:00') - utc(lastOf(a)?.last_at ?? '1970-01-01 00:00:00'),
    written: (a, b) => utc(b.updated_at ?? b.created_at) - utc(a.updated_at ?? a.created_at),
    fav: (a, b) => Number(!!b.data.favourite) - Number(!!a.data.favourite),
    name: (a, b) => a.name.localeCompare(b.name),
    most: (a, b) => storiesWith(b, stories).length - storiesWith(a, stories).length,
  }
  const shown = people.filter(test[filter]).sort(order[sort])
  const featured = shown.length && sort === 'played' && lastOf(shown[0]) ? shown[0].id : undefined
  const menuFor = (c: Item) => characterMenu(c, stories, navigate, reload, () => setDeleting(c))
  const when = (c: Item) => { const l = lastOf(c); return l ? t('card.when.played', { relative: relative(utc(l.last_at)) }) : t('chars.never') }
  const badge = (c: Item) => (lastOf(c)?.cast.find((x) => x.lib_item_id === c.id)?.present ? t('chars.badge.story') : isPersona(c) ? t('chars.badge.persona') : isDraft(c) ? t('chars.badge.draft') : undefined)
  const pickView = (v: string) => {
    const next = v === t('chars.list') ? 'list' : 'grid'
    setView(next)
    api('/settings', 'PUT', { 'ui.charactersView': next }).catch(() => {})
  }
  const saveGroups = (next: Group[]) => api('/settings', 'PUT', { groups: next }).then(reloadSettings)

  return (
    <main className="app__main" aria-label={t('chars.title')} style={{ gap: 26 }}>
      <Top />
      <div className="pg-head">
        <div>
          <h1 className="pg-title">{t('chars.title')}</h1>
          <p className="pg-sub">{t('chars.sub', { characters: people.length, drafts: people.filter(isDraft).length, groups: groups.length })}</p>
        </div>
        <div className="row" style={{ gap: 12 }}>
          <K.Segmented label={t('chars.showAs')} size="sm" options={[t('chars.grid'), t('chars.list')]} value={t(shownAs === 'list' ? 'chars.list' : 'chars.grid')} onChange={pickView} />
          <K.Button icon="download" onClick={() => setImporting(true)}>{t('chars.import')}</K.Button>
          <K.Button variant="primary" icon="plus" href="/characters/new">{t('chars.new')}</K.Button>
        </div>
      </div>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div className="row row--wrap" style={{ gap: 8 }}>
          {FILTERS.map((f) => (
            <K.Chip key={f} pressed={filter === f} icon={f === 'fav' ? 'star' : undefined} onPress={() => setFilter(f)}
              count={people.filter(test[f]).length}>{t(`chars.f.${f}` as Key)}</K.Chip>
          ))}
        </div>
        <div style={{ width: 220 }}>
          <K.Select label={t('chars.sortBy')} options={SORTS.map(sortLabel)} value={sortLabel(sort)} onChange={(v) => setSort(SORTS.find((s) => sortLabel(s) === v) ?? 'played')} />
        </div>
      </div>

      {!shown.length && items.length > 0 ? (
        <div style={{ maxWidth: 620, paddingTop: 20 }}>
          <K.EmptyState icon={filter === 'fav' ? 'star' : 'users'} title={t(filter === 'fav' ? 'chars.none.fav.title' : 'chars.none.title')}
            actions={[<K.Button key="a" size="sm" onClick={() => setFilter('all')}>{t('chars.none.all')}</K.Button>]}>
            {t(filter === 'fav' ? 'chars.none.fav.body' : 'chars.none.body')}
          </K.EmptyState>
        </div>
      ) : shownAs === 'grid' ? (
        <section aria-label={t('chars.everyone')} className="ch-grid">
          {shown.map((c) => {
            const f = face(c)
            const last = lastOf(c)
            return (
              <div key={c.id} className="ch-card" {...withMenu(() => menuFor(c))}>
                <a href={`/characters/${c.id}`} aria-label={c.name} className="ch-card__link" />
                <K.CharacterCard {...f} focus={c.data.focus} name={c.name} line={tagline(c)} when={when(c)} stories={storiesWith(c, stories).length}
                  featured={c.id === featured} badge={badge(c)} badgeTone={badge(c) === t('chars.badge.story') ? 'warm' : undefined} alt={c.data.alt}
                  continueHref={last ? `/story/${last.id}` : undefined}
                  onMore={() => openMenu(document.activeElement ?? document.body, menuFor(c))} />
              </div>
            )
          })}
          <K.AddCard href="/characters/new" sub={t('home.newCharacterSub')}>{t('chars.new')}</K.AddCard>
        </section>
      ) : (
        <section aria-label={t('chars.everyone')} className="card" style={{ padding: '6px 8px' }}>
          {shown.map((c) => {
            const f = face(c)
            const pill = badge(c)
            return (
              <div key={c.id} className="ch-row" {...withMenu(() => menuFor(c))}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <K.ListRow who={f.who} src={f.src} name={c.name} avatarSize={40} story title={c.name} subtitle={tagline(c)}
                    meta={t('chars.listMeta', { when: when(c), n: storiesWith(c, stories).length })} href={`/characters/${c.id}`} />
                </div>
                {pill && <K.StatePill tone={pill === t('chars.badge.story') ? 'warm' : 'muted'}>{pill}</K.StatePill>}
                <span onClick={(e) => openMenu(e.currentTarget, menuFor(c))}><K.IconButton icon="dots" label={t('chars.more', { name: c.name })} size="sm" /></span>
              </div>
            )
          })}
        </section>
      )}

      <section className="sec" aria-label={t('groups.title')}>
        <div className="sec-head">
          <div className="row" style={{ gap: 14, alignItems: 'baseline' }}><h2 className="sec-title">{t('groups.title')}</h2><span className="t-meta">{t('groups.sub')}</span></div>
        </div>
        <div className="row row--wrap" style={{ gap: 14, alignItems: 'stretch' }}>
          {groups.map((g) => {
            const members = g.members.map((id) => byId.get(id)).filter((m): m is Item => !!m)
            const played = (stories ?? []).filter((s) => g.members.every((id) => s.cast.some((c) => c.lib_item_id === id))).length
            const newStory = () => navigate(`/stories/new?with=${g.members.join(',')}${g.place ? `&place=${g.place}` : ''}`)
            const menu = () => [
              { label: t('menu.groupNewStory'), icon: 'plus' as const, onSelect: newStory },
              { label: t('menu.groupEdit'), icon: 'edit' as const, onSelect: () => setGrouping(g) },
              { label: t('menu.duplicate'), icon: 'layers' as const, onSelect: () => saveGroups([...groups, { ...g, id: Date.now(), name: `${g.name} (2)` }]) },
              { divider: true },
              {
                label: t('menu.groupDelete'), detail: t('menu.groupDeleteDetail'), icon: 'trash' as const, danger: true,
                onSelect: () => { saveGroups(groups.filter((x) => x.id !== g.id)); toast(t('toast.groupDeleted', { name: g.name }), { action: t('toast.undo'), onAction: () => saveGroups(groups) }) },
              },
            ]
            return (
              <article key={g.id} className="card ch-group" {...withMenu(menu)}>
                <K.AvatarStack people={members.map((m) => ({ ...face(m), name: m.name }))} size={36} label={list(members.map((m) => m.name))} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <K.StoryName size="row">{g.name}</K.StoryName>
                  <div className="t-meta">{t('groups.meta', { names: list(members.map((m) => m.name)), n: played })}</div>
                </div>
                <K.Button size="sm" onClick={newStory}>{t('groups.newStory')}</K.Button>
                <span onClick={(e) => openMenu(e.currentTarget, menu())}><K.IconButton icon="dots" label={t('chars.more', { name: g.name })} size="sm" /></span>
              </article>
            )
          })}
          <K.AddCard wide icon="users" onClick={() => setGrouping('new')}>{t('groups.new')}</K.AddCard>
        </div>
      </section>

      {deleting && (
        <DeleteCharacter c={deleting} stories={stories} onClose={() => setDeleting(undefined)}
          onGone={(hide) => { const id = deleting.id; setHidden((h) => (hide ? [...h, id] : h.filter((x) => x !== id))) }} />
      )}
      {importing && <ImportCards names={items.map((i) => i.name)} onClose={() => setImporting(false)} onDone={reload} byName={(n) => items.find((i) => i.name.toLowerCase() === n.toLowerCase())} />}
      {grouping && (
        <GroupDialog group={grouping === 'new' ? undefined : grouping} people={people} places={items.filter((i) => i.kind === 'place' && !i.data.unlisted)}
          onClose={() => setGrouping(undefined)}
          onSave={(g) => { saveGroups(grouping === 'new' ? [...groups, g] : groups.map((x) => (x.id === g.id ? g : x))); setGrouping(undefined) }} />
      )}
    </main>
  )
}

/** D5: a set of characters you start a scene with, kept in settings. */
function GroupDialog({ group, people, places, onClose, onSave }: {
  group?: Group; people: Item[]; places: Item[]; onClose: () => void; onSave: (g: Group) => void
}) {
  const [name, setName] = useState(group?.name ?? '')
  const [members, setMembers] = useState<number[]>(group?.members ?? [])
  const [place, setPlace] = useState<number | null>(group?.place ?? null)
  const chosen = members.map((id) => people.find((p) => p.id === id)).filter((p): p is Item => !!p)
  const placeOptions: [number | null, string][] = [[null, t('group.nowhere')], ...places.map((p) => [p.id, p.name] as [number, string])]
  const ok = name.trim() && members.length >= 2
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="users" title={t(group ? 'group.editTitle' : 'group.title')} onClose={onClose}
        note={chosen.length ? t('group.count', { n: chosen.length, names: list(chosen.map((c) => c.name)) }) : undefined}
        actions={[
          <K.Button key="c" variant="ghost" onClick={onClose}>{t('group.cancel')}</K.Button>,
          <K.Button key="m" variant="primary" disabled={!ok} onClick={() => onSave({ id: group?.id ?? Date.now(), name: name.trim(), members, place })}>{t(group ? 'group.save' : 'group.make')}</K.Button>,
        ]}>
        <K.TextField label={t('group.name')} story required value={name} onChange={setName} max={40} />
        <K.Field label={t('group.who')} hint={t('group.order')}>
          <div className="row row--wrap" style={{ gap: 8 }}>
            {people.map((p) => (
              <K.Chip key={p.id} {...face(p)} pressed={members.includes(p.id)}
                onPress={() => setMembers((m) => (m.includes(p.id) ? m.filter((x) => x !== p.id) : [...m, p.id]))}>{p.name}</K.Chip>
            ))}
          </div>
        </K.Field>
        <K.Select label={t('group.where')} options={placeOptions.map(([, l]) => l)} value={placeOptions.find(([id]) => id === place)?.[1]}
          onChange={(v) => setPlace(placeOptions.find(([, l]) => l === v)?.[0] ?? null)} />
      </K.Dialog>
    </Overlay>
  )
}

type Row = { file: File; look?: Look; bad?: boolean; dupe?: Item; choice: 'both' | 'replace' | 'skip'; done?: boolean }

/** D4: character cards in, read first, added only on Import. */
function ImportCards({ onClose, onDone, byName }: { names: string[]; onClose: () => void; onDone: () => void; byName: (n: string) => Item | undefined }) {
  const [rows, setRows] = useState<Row[]>([])
  const [examples, setExamples] = useState(true)
  const [busy, setBusy] = useState(false)
  const choose = async (files: FileList | null) => {
    const picked = [...(files ?? [])].filter((f) => /\.(png|json|charx)$/i.test(f.name))
    const read: Row[] = []
    for (const file of picked) {
      try {
        const look = await sendFile<Look>('/import/look', file)
        if (look.kind !== 'card') read.push({ file, look, bad: true, choice: 'skip' })
        else { const dupe = byName(look.title); read.push({ file, look, dupe, choice: dupe ? 'skip' : 'both' }) }
      } catch {
        read.push({ file, bad: true, choice: 'skip' })
      }
    }
    setRows(read)
  }
  const going = rows.filter((r) => !r.bad && r.choice !== 'skip')
  const run = async () => {
    setBusy(true)
    for (const r of going) {
      if (r.choice === 'replace' && r.dupe) await api(`/library/${r.dupe.id}`, 'DELETE')
      const made = await sendFile<{ item: Item }>('/import/card', r.file)
      const item = made.item
      const data = { ...item.data, source: 'imported' as const, ...(examples ? {} : { example_dialogue: '' }) }
      await api(`/library/${item.id}`, 'PATCH', { data })
      setRows((all) => all.map((x) => (x === r ? { ...x, done: true } : x)))
    }
    onDone()
    toast(t('toast.imported', { n: going.length }), {}, 5000)
    onClose()
  }
  const choices: [Row['choice'], Key][] = [['both', 'imp.both'], ['replace', 'imp.replace'], ['skip', 'imp.skip']]
  return (
    <Overlay onClose={onClose}>
      <section className="dlg dlg--lg" role="dialog" aria-modal="true" aria-labelledby="imp-title">
        <div className="dlg__head">
          <div className="dlg__titles"><h2 className="dlg__title" id="imp-title">{t('imp.title')}</h2></div>
          <K.IconButton icon="x" label="Close" size="sm" onClick={onClose} />
        </div>
        <div className="dlg__body">
          <div onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); choose(e.dataTransfer.files) }}>
            <K.DropZone icon="download" empty={t('imp.empty')} title={t('imp.drop')} description={t('imp.dropSub')}>
              <label className="k-btn k-btn--secondary k-btn--sm">{t('imp.files')}<input type="file" multiple accept=".png,.json,.charx" hidden onChange={(e) => choose(e.target.files)} /></label>
              <label className="k-btn k-btn--ghost k-btn--sm">{t('imp.folder')}<input type="file" hidden {...{ webkitdirectory: '' }} onChange={(e) => choose(e.target.files)} /></label>
            </K.DropZone>
          </div>
          {rows.length > 0 && (
            <>
              <div className="t-meta">
                {t('imp.found', { found: rows.length })} · {t('imp.summary', { ready: rows.filter((r) => !r.bad && !r.dupe).length, dupes: rows.filter((r) => r.dupe).length, bad: rows.filter((r) => r.bad).length })}
              </div>
              <div className="card find-list">
                {rows.map((r, i) => (
                  <div key={i} className="find-row">
                    <K.Avatar name={r.look?.title ?? r.file.name} size={36} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <b>{r.look?.title ?? r.file.name}</b>
                      <div className="t-meta">{r.bad ? t('imp.bad') : r.dupe ? t('imp.dupe', { file: r.file.name, name: r.dupe.name }) : [r.file.name, ...(r.look?.what ?? [])].join(' · ')}</div>
                    </div>
                    {r.dupe && !r.done && (
                      <div style={{ width: 200 }}>
                        <K.Select label="" options={choices.map(([, k]) => t(k))} value={t(choices.find(([c]) => c === r.choice)![1])}
                          onChange={(v) => setRows((all) => all.map((x) => (x === r ? { ...x, choice: choices.find(([, k]) => t(k) === v)?.[0] ?? 'skip' } : x)))} />
                      </div>
                    )}
                    <K.StatePill tone={r.done ? 'ok' : r.bad || r.choice === 'skip' ? 'muted' : 'accent'}>
                      {t(r.done ? 'imp.done' : r.bad || r.choice === 'skip' ? 'imp.skipped' : 'imp.ready')}
                    </K.StatePill>
                  </div>
                ))}
              </div>
              <K.Checkbox label={t('imp.examples')} checked={examples} onChange={setExamples} />
            </>
          )}
        </div>
        <div className="dlg__foot">
          <span className="dlg__note">{t('imp.note')}</span>
          <div className="k-btngroup">
            <K.Button variant="ghost" onClick={onClose}>{t('imp.cancel')}</K.Button>
            <K.Button variant="primary" disabled={!going.length} loading={busy} onClick={run}>{t('imp.go', { n: going.length })}</K.Button>
          </div>
        </div>
      </section>
    </Overlay>
  )
}
