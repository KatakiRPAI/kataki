// A character's profile (E1–E5): docs/handoff/kataki-handoff/SCREENS.md › /characters/:id.
import { useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'
import { api, type Feelings, type Item, type KnownMemory, type Profile as Profiled, type StorySummary } from '../api'
import { pronoun, storiesWith, tagline } from '../characters'
import { K } from '../ds'
import { face, scenery, useLibrary, useLoad, utc } from '../hooks'
import { openMenu, Overlay, toast, type MenuItem } from '../overlay'
import { relative, t, type Key } from '../strings'
import { characterMenu, DeleteCharacter } from './characterActions'

/** A memory as this character holds it, and where it comes from. */
export type Held = KnownMemory & { story: string; storyId: number }
/** 0–100 from the engine's activation: -2 (sharp) reads 73, -4 (hazy) reads 27. */
const clarity = (m: KnownMemory) => Math.round(100 / (1 + Math.exp(-(m.A + 3))))
const doubted = (m: KnownMemory) => m.belief < 0.7
const word = (m: KnownMemory) => t(doubted(m) ? 'mem.word.doubted' : (`mem.word.${m.tier}` as Key))
const tone = (m: KnownMemory) => (doubted(m) ? 'warm' : m.tier === 'sharp' ? 'ok' : 'muted') as 'warm' | 'ok' | 'muted'
const source = (m: KnownMemory) => (m.told_by ? t('mem.told', { name: m.told_by }) : t(m.source === 'witnessed' ? 'mem.seen' : 'mem.heard'))
/** How they talk: their sample lines, without the "Mira:" a card puts before each. */
export const lines = (c: Item) =>
  c.data.lines ??
  (c.data.example_dialogue ?? '').split('\n')
    .map((l) => l.trim())
    .filter((l) => l && !/^(<START>|\{\{user\}\}:|you:)/i.test(l))
    .map((l) => (l.toLowerCase().startsWith(`${c.name.toLowerCase()}:`) ? l.slice(c.name.length + 1) : l.replace(/^\{\{char\}\}:/i, '')).trim())
// ponytail: feelings are counts in the engine (+1 per warm read); a meter shows them around 50
const meter = (n: number) => Math.max(0, Math.min(100, 50 + n * 10))

export default function Profile() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') === 'profile' ? 'profile' : 'story'
  const { byId, reload } = useLibrary()
  const [stories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [profile] = useLoad(() => api<Profiled>(`/library/${id}/profile`), [id])
  const c = byId.get(id)
  const theirs = c ? storiesWith(c, stories) : []
  const latest = theirs[0]
  const here = profile?.stories.find((s) => s.id === latest?.id)?.person ?? null
  const [feelings] = useLoad(
    () => (latest?.persona && here ? api<Feelings>(`/stories/${latest.id}/feelings?who=${here.id}`) : Promise.resolve(null)),
    [latest?.id, here?.id],
  )
  const [held, reloadHeld] = useLoad(async () => {
    const all: Held[] = []
    for (const s of profile?.stories.filter((x) => x.role === 'ai' && x.person) ?? []) {
      const known = await api<KnownMemory[]>(`/stories/${s.id}/memories?knower=${s.person!.id}`)
      all.push(...known.filter((m) => !m.hidden).map((m) => ({ ...m, story: s.title, storyId: s.id })))
    }
    return all.sort((a, b) => b.A - a.A)
  }, [profile])
  const [open, setOpen] = useState<'memories' | 'forget' | 'delete' | null>(null)
  const [forgetting, setForgetting] = useState<number[]>([])

  if (!c) return <main className="app__main"><K.Skeleton /></main>
  const p = pronoun(c)
  const f = face(c)
  const art = f.src ?? (f.who ? (K.ART[f.who]?.src ?? undefined) : undefined)
  const menu = (): MenuItem[] => characterMenu(c, stories, navigate, reload, () => setOpen('delete'))
  const last = feelings?.points.at(-1)
  const top = (held ?? []).filter((m) => m.tier !== 'forgotten').sort((a, b) => b.importance - a.importance).slice(0, 3)
  const placeItems = [...new Map((profile?.places ?? []).map((pl) => [pl.lib_item_id ?? pl.name, pl])).values()]
  const firstPlayed = [...theirs].sort((a, b) => utc(a.created_at) - utc(b.created_at))[0]
  const mood = here?.state.find((s) => /mood|feel/i.test(s.key))?.value
  const fav = () => api(`/library/${c.id}`, 'PATCH', { data: { ...c.data, favourite: !c.data.favourite } }).then(reload)
  const forget = (ids: number[]) => {
    Promise.all(ids.map((m) => api(`/memories/${m}`, 'PATCH', { hidden: true }))).then(reloadHeld)
    toast(t('toast.forgot', { n: ids.length }), {
      action: t('toast.undo'),
      onAction: () => Promise.all(ids.map((m) => api(`/memories/${m}`, 'PATCH', { hidden: false }))).then(reloadHeld),
    })
  }
  const memoryMenu = (m: Held): MenuItem[] => [
    { label: t(m.pinned ? 'mem.m.unpin' : 'mem.m.pin'), icon: 'pin', onSelect: () => api(`/memories/${m.memory_id}`, 'PATCH', { pinned: !m.pinned }).then(reloadHeld) },
    { divider: true },
    { label: t('mem.m.forget'), icon: 'eyeoff', danger: true, onSelect: () => { setForgetting([m.memory_id]); setOpen('forget') } },
  ]

  return (
    <main className="app__main" aria-label={c.name} style={{ gap: 28 }}>
      <K.TopBar back={t('pf.back')} backHref="/characters" />
      <section className="pf-head">
        {art ? <img src={art} alt={c.data.alt ?? c.name} className="pf-portrait" style={{ objectPosition: c.data.focus ?? (f.who ? K.ART[f.who]?.focus : undefined) }} />
          : <div className="pf-portrait pf-portrait--none" aria-hidden="true">{c.name[0]}</div>}
        <div className="col" style={{ flex: 1, gap: 14, paddingBottom: 6 }}>
          {latest && <K.Stamp exact={new Date(utc(latest.last_at)).toLocaleString('en-GB')} detail={latest.title}>{t('card.when.played', { relative: relative(utc(latest.last_at)) })}</K.Stamp>}
          <h1 className="pf-name">{c.name}</h1>
          {tagline(c) && <p className="pf-tagline">{tagline(c)}</p>}
          {c.tags.length > 0 && <div className="row" style={{ gap: 8 }}>{c.tags.map((tg) => <K.Tag key={tg}>{tg}</K.Tag>)}</div>}
          <div className="row" style={{ gap: 12 }}>
            {latest && <K.Button variant="primary" size="lg" href={`/story/${latest.id}`}>{t('pf.continue')}</K.Button>}
            <K.Button size="lg" href={`/stories/new?with=${c.id}`}>{t('pf.newStory')}</K.Button>
            <K.IconButton icon="star" label={t('pf.fav')} pressed={!!c.data.favourite} onClick={fav} />
            <span onClick={(e) => openMenu(e.currentTarget, menu())}><K.IconButton icon="dots" label={t('pf.more', { name: c.name })} /></span>
          </div>
          <K.StatRow stats={[[String(theirs.length), t('pf.stat.stories')], [String(theirs.reduce((n, s) => n + s.messages, 0)), t('pf.stat.lines')], [String(placeItems.length), t('pf.stat.places')]]}>
            {firstPlayed && <K.Stat value={new Date(utc(firstPlayed.created_at)).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} label={t('pf.stat.since')} />}
          </K.StatRow>
        </div>
      </section>
      <K.Tabs label={c.name} tabs={[t('pf.tabs.story'), t('pf.tabs.profile')]} value={t(tab === 'profile' ? 'pf.tabs.profile' : 'pf.tabs.story')}
        onChange={(v) => setParams(v === t('pf.tabs.profile') ? { tab: 'profile' } : {}, { replace: true })} />

      <div className="pf-grid">
        <div className="col" style={{ gap: 30, minWidth: 0 }}>
          {tab === 'story' ? (
            <>
              {lines(c).length > 0 && (
                <section><h2 className="pf-h">{t('pf.talks', { p })}</h2>
                  <div className="col" style={{ gap: 10 }}>{lines(c).slice(0, 4).map((l, i) => <K.Bubble key={i} indent={i % 2 === 1}>{l}</K.Bubble>)}</div>
                </section>
              )}
              {c.private && <K.SecretCard name={c.name} title={t('pf.secret')}>{c.private}</K.SecretCard>}
              {here && here.relationships.length > 0 && (
                <section><h2 className="pf-h">{t('pf.knows', { p })}</h2>
                  <div className="row row--wrap" style={{ gap: 12 }}>
                    {here.relationships.map((r) => {
                      const other = byId.get(latest?.cast.find((x) => x.id === r.other_id)?.lib_item_id ?? -1)
                      return <K.RelationshipCard key={`${r.other_id}-${r.rel}`} {...face(other, r.other)} name={r.other} how={r.note ?? r.rel} />
                    })}
                  </div>
                </section>
              )}
              {placeItems.length > 0 && (
                <section><h2 className="pf-h">{t('pf.moments')}</h2>
                  <div className="pf-moments">
                    {placeItems.slice(0, 4).map((pl) => {
                      const s = scenery(byId.get(pl.lib_item_id ?? -1))
                      return <K.Still key={pl.name} place={s.place} src={s.src} caption={`${pl.name} · ${pl.story}`} height={200} alt={pl.name} />
                    })}
                  </div>
                </section>
              )}
            </>
          ) : (
            <>
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <span className="t-meta">{t('pf.wrote', { p })}</span>
                <K.Button icon="edit" href={`/characters/${c.id}/edit`}>{t('pf.edit')}</K.Button>
              </div>
              <section><h2 className="pf-h">{t('pf.about')}</h2><p className="pf-text">{c.description || t('pf.none')}</p></section>
              <section><h2 className="pf-h">{t('pf.hi', { p })}</h2>{c.data.first_message ? <K.Bubble>{c.data.first_message}</K.Bubble> : <p className="pf-text">{t('pf.none')}</p>}</section>
              {lines(c).length > 0 && (
                <section><h2 className="pf-h">{t('pf.lines', { p })}</h2>
                  <div className="col" style={{ gap: 10 }}>{lines(c).map((l, i) => <K.Bubble key={i} indent={i % 2 === 1}>{l}</K.Bubble>)}</div>
                </section>
              )}
              {c.private && <K.SecretCard name={c.name} title={t('pf.secret')}>{c.private}</K.SecretCard>}
              <section><h2 className="pf-h">{t('pf.details')}</h2>
                <K.Panel flush>
                  <K.SettingsRow title={t('pf.pronouns')} description={t('pf.pronounsSub', { name: c.name, p })}><span className="t-body">{t(`pron.${p}` as Key)}</span></K.SettingsRow>
                  <K.SettingsRow title={t('pf.places', { p })} description={t('pf.placesSub', { p })}>
                    <span className="t-body">{(c.data.places ?? []).map((x) => byId.get(x)?.name).filter(Boolean).join(' · ') || t('pf.none')}</span>
                  </K.SettingsRow>
                  <K.SettingsRow title={t('pf.memory')} description={t('pf.memorySub', { p })}>
                    <span className="t-body">{t(`fade.${c.data.fade ?? 'inherit'}` as Key)}{c.data.doubt !== false ? ` · ${t('fade.doubt')}` : ''}</span>
                  </K.SettingsRow>
                  <K.SettingsRow title={t('pf.made')} description="">
                    <span className="t-body">{t('pf.madeValue', { date: new Date(utc(c.created_at)).toLocaleDateString('en-GB', { dateStyle: 'medium' }), n: c.data.edits ?? 0 })}</span>
                  </K.SettingsRow>
                </K.Panel>
              </section>
            </>
          )}
        </div>

        <aside aria-label={t('pf.rightNow')} className="col" style={{ gap: 18 }}>
          <K.Panel>
            <div className="col" style={{ gap: 18 }}>
              {latest && (
                <div className="col" style={{ gap: 8 }}>
                  <K.Eyebrow>{t('pf.rightNow')}</K.Eyebrow>
                  <div className="row" style={{ gap: 10 }}><K.StoryName size="row">{latest.title}</K.StoryName>{mood && <K.StatePill tone="warm">{mood}</K.StatePill>}</div>
                  <span className="t-meta">{t('pf.at', { where: latest.scene_title ?? latest.place?.name ?? latest.title, when: latest.date })}</span>
                </div>
              )}
              {last && (
                <>
                  <hr className="hair" />
                  <div className="col" style={{ gap: 10 }}>
                    <K.Eyebrow>{t('pf.feels', { p })}</K.Eyebrow>
                    <K.Meter label={t('pf.warmth')} value={meter(last.warmth)} tone="ok" />
                    <K.Meter label={t('pf.trust')} value={meter(last.trust)} />
                    <K.Meter label={t('pf.doubt')} value={Math.min(100, last.doubt * 20)} tone="warm" />
                  </div>
                </>
              )}
              {held && held.length > 0 && (
                <>
                  <hr className="hair" />
                  <div className="col" style={{ gap: 14 }}>
                    <div className="row" style={{ justifyContent: 'space-between' }}><K.Eyebrow>{t('pf.holds', { p })}</K.Eyebrow><span className="t-faint">{t('pf.holding', { shown: top.length, total: held.length })}</span></div>
                    {top.map((m) => <K.MemoryRow key={m.memory_id} word={word(m)} value={clarity(m)} tone={tone(m)}>{m.gist || m.detail}</K.MemoryRow>)}
                    <div className="row" style={{ justifyContent: 'space-between' }}>
                      <button type="button" className="linkbtn" onClick={() => setOpen('memories')}>{t('pf.allMemories', { n: held.length })}</button>
                      {latest && here && <K.TextLink href={`/story/${latest.id}?backstage=${here.id}`} icon="layers" quiet>{t('pf.backstage')}</K.TextLink>}
                    </div>
                  </div>
                </>
              )}
            </div>
          </K.Panel>
          {theirs.length > 0 && (
            <K.Panel flush>
              <div style={{ padding: '14px 16px 4px' }}><K.Eyebrow>{t('pf.storiesTogether')}</K.Eyebrow></div>
              {theirs.map((s) => <K.ListRow key={s.id} story title={s.title} subtitle={s.date} meta={relative(utc(s.last_at))} href={`/story/${s.id}`} />)}
            </K.Panel>
          )}
        </aside>
      </div>

      {open === 'memories' && held && (
        <Memories name={c.name} held={held} onClose={() => setOpen(null)} menu={memoryMenu} />
      )}
      {open === 'forget' && held && (
        <Forget c={c} held={held} picked={forgetting} onClose={() => setOpen(null)} onForget={(ids) => { setOpen(null); forget(ids) }} />
      )}
      {open === 'delete' && (
        <DeleteCharacter c={c} stories={stories} onClose={() => setOpen(null)} onGone={() => {}} onBack={() => navigate('/characters')} />
      )}
    </main>
  )
}

/** E3: every memory, sharpest first, as a side sheet. */
function Memories({ name, held, onClose, menu }: { name: string; held: Held[]; onClose: () => void; menu: (m: Held) => MenuItem[] }) {
  const [q, setQ] = useState('')
  const [kind, setKind] = useState<'all' | 'sharp' | 'hazy' | 'doubted' | 'forgotten'>('all')
  const [story, setStory] = useState(t('mem.every'))
  const titles = [...new Set(held.map((m) => m.story))]
  const test = { all: () => true, sharp: (m: Held) => m.tier === 'sharp', hazy: (m: Held) => m.tier === 'hazy', doubted: doubted, forgotten: (m: Held) => m.tier === 'forgotten' }
  const shown = held.filter(test[kind]).filter((m) => story === t('mem.every') || m.story === story)
    .filter((m) => !q.trim() || `${m.gist} ${m.detail}`.toLowerCase().includes(q.trim().toLowerCase()))
  return (
    <Overlay onClose={onClose}>
      <div className="pf-sheet">
        <section className="dlg" role="dialog" aria-modal="true" aria-labelledby="mem-title">
          <div className="dlg__head">
            <div className="dlg__titles">
              <h2 className="dlg__title" id="mem-title">{t('mem.title', { name })}</h2>
              <p className="dlg__desc">{t('mem.sub', { n: held.length })}</p>
            </div>
            <K.IconButton icon="x" label="Close" size="sm" onClick={onClose} />
          </div>
          <div className="dlg__body pf-sheet__body">
            <K.SearchField placeholder={t('mem.search', { name })} label={t('mem.search', { name })} shortcut={false} value={q} onChange={setQ} />
            <div className="row row--wrap" style={{ gap: 8 }}>
              {(['all', 'sharp', 'hazy', 'doubted', 'forgotten'] as const).map((k) => (
                <K.Chip key={k} size="sm" pressed={kind === k} count={held.filter(test[k]).length} onPress={() => setKind(k)}>{t(`mem.${k}` as Key)}</K.Chip>
              ))}
            </div>
            <div style={{ width: 240 }}><K.Select label={t('mem.story')} options={[t('mem.every'), ...titles]} value={story} onChange={setStory} /></div>
            {!shown.length && <p className="t-meta">{t('mem.none')}</p>}
            {shown.map((m) => (
              <div key={`${m.storyId}-${m.memory_id}`} className="pf-memrow">
                <K.MemoryRow word={word(m)} value={clarity(m)} tone={tone(m)} meta={t('mem.meta', { word: word(m), source: source(m), story: m.story })}>{m.gist || m.detail}</K.MemoryRow>
                <span onClick={(e) => openMenu(e.currentTarget, menu(m))}><K.IconButton icon="dots" label={t('mem.more')} size="sm" /></span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </Overlay>
  )
}

/** E4: forget some memories; the lines stay. */
function Forget({ c, held, picked, onClose, onForget }: { c: Item; held: Held[]; picked: number[]; onClose: () => void; onForget: (ids: number[]) => void }) {
  const [q, setQ] = useState('')
  const [ids, setIds] = useState(picked)
  const shown = held.filter((m) => m.tier !== 'forgotten' && (!q.trim() || `${m.gist} ${m.detail}`.toLowerCase().includes(q.trim().toLowerCase())))
  return (
    <Overlay onClose={onClose}>
      <section className="dlg dlg--lg" role="dialog" aria-modal="true" aria-labelledby="fg-title">
        <div className="dlg__head">
          <span className="dlg__icon" style={{ color: 'var(--warm)' }}><K.Icon name="eyeoff" size={20} /></span>
          <div className="dlg__titles">
            <h2 className="dlg__title" id="fg-title">{t('fg.title', { name: c.name })}</h2>
            <p className="dlg__desc">{t('fg.body', { p: pronoun(c) })}</p>
          </div>
          <K.IconButton icon="x" label="Close" size="sm" onClick={onClose} />
        </div>
        <div className="dlg__body">
          <K.SearchField placeholder={t('fg.find')} label={t('fg.find')} shortcut={false} value={q} onChange={setQ} />
          <div className="card find-list">
            {shown.map((m) => (
              <div key={`${m.storyId}-${m.memory_id}`} className="find-row">
                <K.Checkbox label={m.gist || m.detail} description={t('mem.meta', { word: word(m), source: source(m), story: m.story })}
                  checked={ids.includes(m.memory_id)} onChange={(on) => setIds((x) => (on ? [...x, m.memory_id] : x.filter((y) => y !== m.memory_id)))} />
              </div>
            ))}
          </div>
        </div>
        <div className="dlg__foot">
          <span className="dlg__note">{t('fg.note', { n: ids.length, name: c.name })}</span>
          <div className="k-btngroup">
            <K.Button variant="ghost" onClick={onClose}>{t('fg.cancel')}</K.Button>
            <K.Button variant="danger" disabled={!ids.length} onClick={() => onForget(ids)}>{t('fg.go', { n: ids.length })}</K.Button>
          </div>
        </div>
      </section>
    </Overlay>
  )
}

