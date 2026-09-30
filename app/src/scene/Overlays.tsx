// The Scene's own overlays (SCENE.md › Other overlays): Pass time (P11), Scene and place (P17),
// Story settings (P18), a character's card (P15) and Find in story.
import { useEffect, useRef, useState } from 'react'
import { api, later as words, UNITS, type Book, type BondDim, type CastEntity, type Provider, type Item, type KnownMemory, type Person, type Story, type Unit } from '../api'
import { K } from '../ds'
import { scenery, twelve, useLibrary, useLoad } from '../hooks'
import { Overlay, toast } from '../overlay'
import { t, type Key } from '../strings'

// what the engine's clock reads, and what the button says
const PRESETS: [string, Key][] = [['5 minutes later', 'pass.moment'], ['1 hour later', 'pass.hour'], ['the next morning', 'pass.morning'], ['a week later', 'pass.week']]

export type Pass = { skip: string; place?: number }

type Time = 'dawn' | 'day' | 'dusk' | 'night'
const TIMES: Time[] = ['dawn', 'day', 'dusk', 'night']
const AT: Record<Time, number> = { dawn: 390, day: 720, dusk: 1110, night: 1320 } // minutes into a day
/** The time that passes until the next dawn, day, dusk or night, in words the clock reads. */
export const untilTime = (minuteOfDay: number, to: Time) => words(((AT[to] - minuteOfDay + 1440) % 1440) || 1440, 'minutes')

export function PassTime({ story, onClose, onPass }: { story: Story; onClose: () => void; onPass: (p: Pass) => void }) {
  const { items } = useLibrary()
  const [pick, setPick] = useState<string>(PRESETS[0][0])
  const [count, setCount] = useState(3)
  const [unit, setUnit] = useState<Unit>('weeks')
  const [where, setWhere] = useState<'stay' | 'else'>('stay')
  const places = items.filter((i) => i.kind === 'place' && !i.data.unlisted && i.id !== story.place?.lib_item_id)
  const [place, setPlace] = useState<number | undefined>(places[0]?.id)
  const skip = pick === 'choose' ? words(count, unit) : pick
  return (
    <Overlay onClose={onClose}>
      <div className="scene-card spop" role="dialog" aria-label={t('pass.title')} style={{ width: 360 }}>
        <h3>{t('pass.title')}</h3>
        <span className="scene-t">{t('pass.from', { time: twelve(story.clock), when: story.date })}</span>
        <div className="col" style={{ gap: 6 }}>
          {PRESETS.map(([k, label]) => (
            <button key={k} type="button" className="opt2" aria-pressed={pick === k} onClick={() => setPick(k)}>{t(label)}</button>
          ))}
          <button type="button" className="opt2" aria-pressed={pick === 'choose'} onClick={() => setPick('choose')}>{t('pass.choose')}</button>
          {pick === 'choose' && (
            <div className="row" style={{ gap: 8 }}>
              <input className="spop__num" type="number" min={1} max={999} value={count} aria-label={t('pass.count')}
                onChange={(e) => setCount(Math.max(1, Math.min(999, Number(e.target.value) || 1)))} />
              <select className="spop__sel" value={unit} aria-label={t('pass.unit')} onChange={(e) => setUnit(e.target.value as Unit)}>
                {UNITS.map((u) => <option key={u} value={u}>{t(`unit.${u}` as Key)}</option>)}
              </select>
            </div>
          )}
        </div>
        <K.Segmented tone="scene" size="sm" label={t('pass.where')} options={[t('pass.stay'), t('pass.elsewhere')]}
          value={t(where === 'stay' ? 'pass.stay' : 'pass.elsewhere')} onChange={(v) => setWhere(v === t('pass.stay') ? 'stay' : 'else')} />
        {where === 'else' && (
          <select className="spop__sel" value={place} aria-label={t('pass.place')} onChange={(e) => setPlace(Number(e.target.value))}>
            {places.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        )}
        <div className="row" style={{ gap: 8, justifyContent: 'flex-end' }}>
          <button type="button" className="k-btn k-btn--scene-ghost" onClick={onClose}>{t('pass.cancel')}</button>
          <button type="button" className="k-btn k-btn--scene-send" onClick={() => onPass({ skip, place: where === 'else' ? place : undefined })}>{t('pass.go')}</button>
        </div>
      </div>
    </Overlay>
  )
}

/** P17: move the scene, and say who is here. */
export function ScenePlace({ story, characters, onClose, onChange }: {
  story: Story; characters: CastEntity[]; onClose: () => void; onChange: (body: { present: number[]; library_place_id?: number; skip?: string }) => void
}) {
  const { items, byId } = useLibrary()
  const places = items.filter((i) => i.kind === 'place' && !i.data.unlisted)
  const [to, setTo] = useState<number | 'stay'>('stay')
  const [here, setHere] = useState(() => Object.fromEntries(characters.map((e) => [e.id, e.present])))
  const [time, setTime] = useState<Time | 'now'>('now')
  const now = byId.get(story.place?.lib_item_id ?? -1)
  const s = scenery(now)
  return (
    <Overlay onClose={onClose}>
      <section className="scene-card spop" role="dialog" aria-label={t('place.title')} style={{ width: 520 }}>
        <h3>{t('place.title')}</h3>
        <div className="row" style={{ gap: 14 }}>
          {(s.src || s.place) && <K.SceneStage place={s.place} src={s.src} height={90} alt={now?.name} />}
          <span className="scene-t">{t('place.now', { place: story.place?.name ?? t('place.nowhere'), when: story.date })}</span>
        </div>
        <div className="col" style={{ gap: 6 }}>
          <b style={{ fontSize: 13.5 }}>{t('place.move')}</b>
          <div className="row row--wrap" style={{ gap: 6 }}>
            <button type="button" className="opt2 opt2--chip" aria-pressed={to === 'stay'} onClick={() => setTo('stay')}>{t('place.here')}</button>
            {places.filter((p) => p.id !== now?.id).map((p) => (
              <button key={p.id} type="button" className="opt2 opt2--chip" aria-pressed={to === p.id} onClick={() => setTo(p.id)}>{p.name}</button>
            ))}
          </div>
          <span className="scene-t">{t('place.moveNote')}</span>
        </div>
        <K.Segmented tone="scene" size="sm" label={t('place.time')} options={(['now', ...TIMES] as const).map((x) => t(`place.t.${x}` as Key))} value={t(`place.t.${time}` as Key)}
          onChange={(v) => setTime((['now', ...TIMES] as const).find((x) => t(`place.t.${x}` as Key) === v) ?? 'now')} />
        <div className="col" style={{ gap: 6 }}>
          <b style={{ fontSize: 13.5 }}>{t('place.who')}</b>
          {characters.map((e) => (
            <div key={e.id} className="row" style={{ justifyContent: 'space-between' }}>
              <span>{e.name}</span>
              <K.Segmented tone="scene" size="sm" label={e.name} options={[t('place.present'), t('place.away')]}
                value={t(here[e.id] ? 'place.present' : 'place.away')} onChange={(v) => setHere((h) => ({ ...h, [e.id]: v === t('place.present') }))} />
            </div>
          ))}
        </div>
        <div className="row" style={{ gap: 8, justifyContent: 'flex-end' }}>
          <button type="button" className="k-btn k-btn--scene-ghost" onClick={onClose}>{t('place.cancel')}</button>
          <button type="button" className="k-btn k-btn--scene-send"
            onClick={() => onChange({ present: characters.filter((e) => here[e.id]).map((e) => e.id), ...(to === 'stay' ? {} : { library_place_id: to }), ...(time === 'now' ? {} : { skip: untilTime(story.minute_of_day, time) }) })}>
            {t('place.go')}
          </button>
        </div>
      </section>
    </Overlay>
  )
}

/** P18: the story's own settings, saved as they change. */
export function StorySettings({ story, advanced, onAdvanced, onClose, onChange }: {
  story: Story; advanced: boolean; onAdvanced: (v: boolean) => void; onClose: () => void; onChange: () => void
}) {
  const [books] = useLoad(() => api<Book[]>('/books'), [])
  const [title, setTitle] = useState(story.title)
  const patch = (body: object) => api(`/stories/${story.id}`, 'PATCH', body).then(onChange)
  const bookOptions: [number | null, string][] = [[null, t('set.noBook')], ...(books ?? []).map((b) => [b.id, b.title] as [number, string])]
  const { items } = useLibrary()
  const personaOptions: [number | null, string][] = [...items.filter((i) => i.kind === 'character' && i.data.persona).map((p) => [p.id, p.name] as [number, string]), [null, t('pm.director')]]
  // a model for this story alone: any model a connection offers, or the default (Settings › Models)
  const [models] = useLoad(async () => {
    const providers = await api<Provider[]>('/providers')
    const all = await Promise.all(providers.map((p) => api<{ models: string[] }>(`/providers/${p.id}/models`).then((m) => m.models.map((x) => [`${p.id}:${x}`, `${p.name} · ${x}`] as [string, string]), () => [])))
    return all.flat()
  }, [])
  const own = (story.roles as { rp?: { provider_id?: number; model?: string } }).rp
  const currentModel = own?.model ? `${own.provider_id}:${own.model}` : ''
  const modelOptions: [string, string][] = [['', t('set.modelDefault')], ...(models ?? []), ...(currentModel && !(models ?? []).some(([k]) => k === currentModel) ? [[currentModel, own!.model!] as [string, string]] : [])]
  return (
    <Overlay onClose={onClose}>
      <div className="scene-sheet">
        <K.Sheet tone="scene" title={t('set.title')} onClose={() => { if (title.trim() && title !== story.title) patch({ title: title.trim() }); onClose() }}>
          <div className="col" style={{ gap: 18 }}>
            <K.TextField label={t('set.name')} story max={60} value={title} onChange={setTitle} />
            <K.Select label={t('set.book')} options={bookOptions.map(([, l]) => l)} value={bookOptions.find(([id]) => id === (story.book?.id ?? null))?.[1]}
              onChange={(v) => patch({ book_id: bookOptions.find(([, l]) => l === v)?.[0] ?? null })} />
            <K.Select label={t('set.you')} hint={t('set.youHint')} options={personaOptions.map(([, l]) => l)}
              value={personaOptions.find(([id]) => id === (story.persona?.lib_item_id ?? null))?.[1] ?? personaOptions.at(-1)?.[1]}
              onChange={(v) => { patch({ persona_id: personaOptions.find(([, l]) => l === v)?.[0] ?? null }); toast(t('toast.personaSwitched', { name: v }), { icon: 'user' }, 3000) }} />
            <K.Select label={t('set.model')} hint={t('set.modelHint')} options={modelOptions.map(([, l]) => l)}
              value={modelOptions.find(([k]) => k === currentModel)?.[1] ?? modelOptions[0][1]}
              onChange={(v) => {
                const key = modelOptions.find(([, l]) => l === v)?.[0] ?? ''
                const [pid, ...rest] = key.split(':')
                patch({ roles: key ? { rp: { provider_id: Number(pid), model: rest.join(':'), kind: 'auto', params: {} } } : {} })
              }} />
            <K.SettingsRow title={t('talk.label')} description={t('talk.sub')}>
              <K.Segmented tone="scene" size="sm" label={t('talk.label')} options={[t('talk.person'), t('talk.text')]} value={t(story.talk === 'text' ? 'talk.text' : 'talk.person')}
                onChange={(v) => patch({ talk: v === t('talk.text') ? 'text' : 'person' })} />
            </K.SettingsRow>
            <K.SettingsRow title={t('set.hears')} description={t('set.hearsSub')}><K.Toggle label={t('set.hears')} on={advanced} onToggle={onAdvanced} /></K.SettingsRow>
            <K.SettingsRow title={t('set.minutes')} description={t('set.minutesSub')}>
              <input className="spop__num" type="number" min={1} max={1440} defaultValue={story.minutes_per_turn} aria-label={t('set.minutes')}
                onBlur={(e) => { const n = Math.max(1, Math.round(Number(e.target.value))); if (n !== story.minutes_per_turn) patch({ minutes_per_turn: n }) }} />
            </K.SettingsRow>
            <span className="scene-t">{t('set.saved')}</span>
            <K.Button onClick={() => { if (title.trim() && title !== story.title) patch({ title: title.trim() }); onClose() }}>{t('w.done')}</K.Button>
          </div>
        </K.Sheet>
      </div>
    </Overlay>
  )
}

const DIMS: BondDim[] = ['closeness', 'trust', 'respect', 'attraction']
const NEGATIVE = new Set(['anxious', 'afraid', 'sad', 'hurt', 'annoyed', 'angry', 'ashamed', 'bored']) // inner.NEGATIVE
/** A ledger move (roughly -100..100, a few points per event) as a bar centred on "as they met". */
const bar = (n: number) => Math.max(0, Math.min(100, 50 + n * 1.5))
const signed = (n: number) => { const r = Math.round(n); return r > 0 ? `+${r}` : r < 0 ? `−${-r}` : '0' }

/** P15: a character's card, from their widget: what anyone could see, how they stand with you
 * and why, and (on a tap: the author's peek) what they feel inside, think, need and want. */
export function CharacterCard({ story, entity, item, onClose, onAnswer, onMove, onWidget }: {
  story: Story; entity: CastEntity; item?: Item; onClose: () => void; onAnswer: () => void; onMove: () => void; onWidget?: () => void
}) {
  const [people] = useLoad(() => api<Person[]>(`/stories/${story.id}/people`), [story.id])
  const [known] = useLoad(() => api<KnownMemory[]>(`/stories/${story.id}/memories?knower=${entity.id}`), [story.id, entity.id])
  const [inside, setInside] = useState(false)
  const person = people?.find((p) => p.id === entity.id)
  const p = item?.data.pronouns ?? 'they'
  const held = (known ?? []).filter((m) => m.tier !== 'forgotten' && !m.hidden)
  const top = held[0]
  const flag = person?.state.find((s) => /mood|feel/i.test(s.key))?.value
  const mood = person?.mood
  const bond = person?.bonds?.find((b) => b.you)
  return (
    <Overlay onClose={onClose}>
      <div className="scene-sheet">
        <K.Sheet tone="scene" title={entity.name} onClose={onClose}>
          <div className="col" style={{ gap: 16 }}>
            {(mood || flag) && (
              <div className="row row--wrap" style={{ gap: 6 }}>
                {mood && <K.StatePill tone={NEGATIVE.has(mood.shows) ? 'bad' : 'warm'}>{mood.shows}</K.StatePill>}
                {mood?.word && <K.StatePill tone="muted">{mood.word}</K.StatePill>}
                {!mood && flag && <K.StatePill tone="warm">{flag}</K.StatePill>}
                {mood?.tell && <span className="scene-t">{t('cc.tell', { tell: mood.tell })}</span>}
              </div>
            )}
            <div className="col" style={{ gap: 6 }}>
              <K.Eyebrow>{t('cc.rightNow')}</K.Eyebrow>
              <K.KeyValue label={t('cc.where')}>{person?.where ?? story.place?.name ?? t('place.nowhere')}</K.KeyValue>
              {story.scene_title && <K.KeyValue label={t('cc.scene')}>{story.scene_title}</K.KeyValue>}
              {person?.since && <K.KeyValue label={t('cc.since')}>{person.since}</K.KeyValue>}
            </div>
            {bond && (
              <div className="col" style={{ gap: 8 }}>
                <K.Eyebrow>{t('cc.feels', { p })}</K.Eyebrow>
                {DIMS.map((d) => <K.Meter key={d} label={t(`cc.dim.${d}` as Key)} value={bar(bond[d] ?? 0)} word={signed(bond[d] ?? 0)} tone={(bond[d] ?? 0) < 0 ? 'bad' : 'ok'} />)}
                {bond.grudge && (
                  <div className="row" style={{ gap: 6 }}>
                    <K.StatePill tone="bad">{t('cc.grudge')}</K.StatePill>
                    <span className="scene-t">{bond.grudge.cause}</span>
                  </div>
                )}
                {(bond.recent ?? bond.causes).length > 0 && (
                  <div className="col" style={{ gap: 4 }}>
                    <b style={{ fontSize: 12.5 }}>{t('cc.why')}</b>
                    {(bond.recent ?? bond.causes).slice(0, 3).map((c) => (
                      <span key={`${c.event}${c.since}`} className="scene-t">
                        {c.cause} · {Object.entries(c.moves ?? {}).map(([d, v]) => `${t(`cc.dim.${d}` as Key)} ${signed(v ?? 0)}`).join(', ')}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
            {mood || person?.thought || person?.goals?.length || person?.needs ? (
              inside ? (
                <div className="col" style={{ gap: 8 }}>
                  <K.Eyebrow tone="accent">{t('cc.inside', { p })}</K.Eyebrow>
                  {(mood?.emotions ?? []).map((e) => <K.Meter key={e.label} label={e.label} value={Math.round(e.i * 100)} tone={NEGATIVE.has(e.label) ? 'bad' : 'warm'} />)}
                  {mood?.emotions?.[0] && <span className="scene-t">{t('cc.because', { why: mood.emotions[0].why })}</span>}
                  {mood?.label && mood.shows !== mood.label && <span className="scene-t">{t('cc.masks', { shows: mood.shows, feels: mood.label })}</span>}
                  {person?.thought && <span className="scene-t">{t('cc.thinks', { thinks: person.thought.thinks })}</span>}
                  {person?.needs && <K.Meter label={t('cc.energy')} value={Math.round(person.needs.energy * 100)} tone="muted" />}
                  {person?.needs?.pressing && <span className="scene-t">{t('cc.needs', { need: t(`cc.need.${person.needs.pressing}` as Key) })}</span>}
                  {person?.goals?.filter((g) => g.status === 'active').slice(0, 2).map((g) => <K.KeyValue key={g.id} label={t('cc.wants')}>{g.text}</K.KeyValue>)}
                  <button type="button" className="k-btn k-btn--scene-ghost" onClick={() => setInside(false)}>{t('cc.hideInside')}</button>
                </div>
              ) : <button type="button" className="k-btn k-btn--scene-ghost" onClick={() => setInside(true)}>{t('cc.peekInside', { p })}</button>
            ) : null}
            {top && (
              <div className="col" style={{ gap: 8 }}>
                <K.Eyebrow>{t('cc.holding', { shown: 1, total: held.length })}</K.Eyebrow>
                <K.MemoryRow word={top.belief < 0.7 ? t('cc.doubted') : t(`mem.word.${top.tier}` as Key)} value={Math.round(100 / (1 + Math.exp(-(top.A + 3))))}
                  tone={top.belief < 0.7 ? 'warm' : 'ok'}>{top.gist || top.detail}</K.MemoryRow>
              </div>
            )}
            {person && person.relationships.length > 0 && (
              <div className="row row--wrap" style={{ gap: 6 }}>
                {person.relationships.map((r) => <span key={`${r.other_id}${r.rel}`} className="heard">{r.you ? r.rel : `${r.rel} · ${r.other}`}</span>)}
              </div>
            )}
            <div className="col" style={{ gap: 8 }}>
              {onWidget && <button type="button" className="k-btn k-btn--scene-ghost" onClick={onWidget}>{t('cc.addWidget')}</button>}
              {entity.present && <button type="button" className="k-btn k-btn--scene-ghost" onClick={onAnswer}>{t('cc.answer', { p })}</button>}
              <button type="button" className="k-btn k-btn--scene-ghost" onClick={onMove}>{t(entity.present ? 'cc.away' : 'cc.back', { p })}</button>
              {item && <a className="k-btn k-btn--scene-ghost" href={`/characters/${item.id}`}>{t('cc.profile')}</a>}
            </div>
          </div>
        </K.Sheet>
      </div>
    </Overlay>
  )
}

/** Find in story (Ctrl F): Enter goes to the next line that has it. */
export function FindBar({ ids, onFind, onClose }: { ids: (q: string) => number[]; onFind: (id?: number) => void; onClose: () => void }) {
  const [q, setQ] = useState('')
  const [i, setI] = useState(0)
  const box = useRef<HTMLInputElement>(null)
  const hits = q.trim() ? ids(q.trim().toLowerCase()) : []
  useEffect(() => box.current?.focus(), [])
  useEffect(() => onFind(hits[i]), [q, i]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div className="findbar" role="search">
      <K.Icon name="search" size={15} />
      <input ref={box} value={q} placeholder={t('find.label')} aria-label={t('find.label')}
        onChange={(e) => { setQ(e.target.value); setI(0) }}
        onKeyDown={(e) => {
          if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onFind(undefined); onClose() }
          if (e.key === 'Enter' && hits.length) setI((x) => (x + (e.shiftKey ? hits.length - 1 : 1)) % hits.length)
        }} />
      <span className="scene-t">{q.trim() ? (hits.length ? t('find.count', { i: i + 1, n: hits.length }) : t('find.none')) : ''}</span>
      <button type="button" className="k-scenebtn" aria-label="Close" onClick={() => { onFind(undefined); onClose() }}><K.Icon name="x" size={15} /></button>
    </div>
  )
}

