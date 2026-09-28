// Making and editing a character (F1–F7): docs/handoff/kataki-handoff/SCREENS.md › /characters/new.
import { useEffect, useRef, useState } from 'react'
import { useBlocker, useNavigate, useParams } from 'react-router'
import { api, mediaUrl, upload, type Item, type Pronouns, type Provider, type RoleRow, type StorySummary } from '../api'
import { storiesWith } from '../characters'
import { K } from '../ds'
import { useLibrary, useLoad, utc, useTitle } from '../hooks'
import { Overlay } from '../overlay'
import { t, type Key } from '../strings'
import { lines as linesOf } from './Profile'
import liv from '../ds/art/liv.png'
import mike from '../ds/art/mike.png'
import theo from '../ds/art/theo.png'
import nico from '../ds/art/nico.png'
import jae from '../ds/art/jae.png'
import cas from '../ds/art/cas.png'

const SET: [string, string][] = [[liv, '52% 24%'], [mike, '50% 26%'], [theo, '50% 30%'], [jae, '50% 32%'], [nico, '52% 30%'], [cas, '50% 20%']]
const MOODS = ['warm', 'guarded', 'hurry', 'argue'] as const
const PRONOUNS: Pronouns[] = ['she', 'he', 'they']
const RELS = ['friend', 'fond', 'wary', 'rival', 'family', 'never'] as const
const FADES = ['inherit', 'fast', 'lifelike', 'slow', 'never'] as const
type Section = 'about' | 'talk' | 'secret' | 'rels' | 'places' | 'model'
const SECTIONS: [Section, Key, Key, import('../ds/kataki').IconName][] = [
  ['about', 'ed.about', 'ed.aboutSub', 'user'], ['talk', 'ed.talk', 'ed.talkSub', 'quote'], ['secret', 'ed.secret', 'ed.secretSub', 'lock'],
  ['rels', 'ed.rels', 'ed.relsSub', 'users'], ['places', 'ed.places', 'ed.placesSub', 'map-pin'], ['model', 'ed.model', 'ed.modelSub', 'cpu'],
]

type Form = {
  name: string; greeting: string; about: string; tagline: string; tags: string; pronouns: Pronouns
  lines: string[]; secret: string; relationships: { id: number; feels: string }[]; places: number[]
  fade: (typeof FADES)[number]; doubt: boolean; portrait?: string; focus?: string; alt?: string; model: string // "providerId:model", or '' for the default
}

function formOf(c?: Item): Form {
  return {
    name: c?.name ?? '', greeting: c?.data.first_message ?? '', about: c?.description ?? '', tagline: c?.data.tagline ?? '',
    tags: (c?.tags ?? []).join(', '), pronouns: c?.data.pronouns ?? 'they', lines: c ? linesOf(c) : ['', ''], secret: c?.private ?? '',
    relationships: c?.data.relationships ?? [], places: c?.data.places ?? [], fade: c?.data.fade ?? 'inherit', doubt: c?.data.doubt !== false, model: c?.data.model?.model ? `${c.data.model.provider_id}:${c.data.model.model}` : '',
    portrait: c?.data.portrait, focus: c?.data.focus, alt: c?.data.alt,
  }
}
const filled: Record<Section, (f: Form) => boolean> = {
  about: (f) => !!(f.about.trim() || f.tagline.trim()), talk: (f) => f.lines.some((l) => l.trim()), secret: (f) => !!f.secret.trim(),
  rels: (f) => f.relationships.length > 0, places: (f) => f.places.length > 0, model: (f) => f.fade !== 'inherit' || !f.doubt || !!f.model,
}
const changed = (a: Form, b: Form): Section[] => {
  const s: Section[] = []
  if (a.about !== b.about || a.tagline !== b.tagline || a.tags !== b.tags || a.pronouns !== b.pronouns) s.push('about')
  if (JSON.stringify(a.lines) !== JSON.stringify(b.lines)) s.push('talk')
  if (a.secret !== b.secret) s.push('secret')
  if (JSON.stringify(a.relationships) !== JSON.stringify(b.relationships)) s.push('rels')
  if (JSON.stringify(a.places) !== JSON.stringify(b.places)) s.push('places')
  if (a.fade !== b.fade || a.doubt !== b.doubt || a.model !== b.model) s.push('model')
  return s
}

export default function Editor() {
  const param = useParams().id
  const id = param ? Number(param) : undefined
  const navigate = useNavigate()
  const { items, byId, reload } = useLibrary()
  const [stories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [roles] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const item = id ? byId.get(id) : undefined
  useTitle(item ? t('title.edit', { name: item.name }) : undefined)
  const [base, setBase] = useState<Form>()
  const [f, setF] = useState<Form>(() => ({ ...formOf(), name: new URLSearchParams(location.search).get('name') ?? '' }))
  const [open, setOpen] = useState<Section[]>([])
  const [tried, setTried] = useState(false)
  const [saving, setSaving] = useState(false)
  const [picking, setPicking] = useState(false)
  const [focusing, setFocusing] = useState<{ src: string; name?: string; bad?: boolean }>()
  const fileRef = useRef<HTMLInputElement>(null)
  useEffect(() => {
    if (base || (id && !item)) return
    const start = formOf(item)
    setBase(start)
    if (item) setF(start)
    if (item) setOpen(SECTIONS.map(([s]) => s).filter((s) => filled[s](start)))
  }, [item, id, base])

  const edit = !!id
  const firstLoad = base ?? formOf()
  const nameOk = !!f.name.trim()
  const hiOk = !!f.greeting.trim()
  const diff = changed(f, firstLoad).concat(f.name !== firstLoad.name || f.greeting !== firstLoad.greeting || f.portrait !== firstLoad.portrait || f.focus !== firstLoad.focus || f.alt !== firstLoad.alt ? (['about'] as Section[]) : [])
  const sections = [...new Set(diff)]
  const dirty = sections.length > 0
  const blocker = useBlocker(({ currentLocation, nextLocation }) => dirty && !saving && currentLocation.pathname !== nextLocation.pathname)
  useEffect(() => {
    if (!dirty) return
    const warn = (e: BeforeUnloadEvent) => e.preventDefault()
    addEventListener('beforeunload', warn)
    return () => removeEventListener('beforeunload', warn)
  }, [dirty])

  const set = <K extends keyof Form>(k: K, v: Form[K]) => setF((x) => ({ ...x, [k]: v }))
  const p = f.pronouns
  const taken = !!f.name.trim() && items.some((i) => i.id !== id && i.kind === 'character' && i.name.toLowerCase() === f.name.trim().toLowerCase())
  const others = items.filter((i) => i.kind === 'character' && i.id !== id)
  const places = items.filter((i) => i.kind === 'place' && !i.data.unlisted)
  const rp = roles?.find((r) => r.role === 'rp')?.effective_model
  // every model a connection offers now ("Only models that are connected now are listed.")
  const [models] = useLoad(async () => {
    const providers = await api<Provider[]>('/providers')
    const all = await Promise.all(providers.map((p) => api<{ models: string[] }>(`/providers/${p.id}/models`).then((m) => m.models.map((x) => [`${p.id}:${x}`, `${p.name} · ${x}`] as [string, string]), () => [])))
    return all.flat()
  }, [])
  const modelOptions: [string, string][] = [['', rp ? t('ed.modelDefault', { model: rp }) : t('ed.modelNone')], ...(models ?? []), ...(f.model && !(models ?? []).some(([k]) => k === f.model) ? [[f.model, f.model.split(':').slice(1).join(':')] as [string, string]] : [])]
  const theirs = item ? storiesWith(item, stories) : []

  const save = async (draftOnly = false) => {
    setTried(true)
    if (!nameOk || (!hiOk && !draftOnly)) {
      document.querySelector<HTMLElement>(nameOk ? '#ed-hi textarea' : '#ed-name input')?.focus()
      return false
    }
    setSaving(true)
    const lines = f.lines.map((l) => l.trim()).filter(Boolean)
    const body = {
      name: f.name.trim(), description: f.about.trim(), private: f.secret.trim(),
      tags: f.tags.split(',').map((x) => x.trim()).filter(Boolean).slice(0, 3),
      data: {
        ...(item?.data ?? { source: 'made' }), tagline: f.tagline.trim() || undefined, pronouns: f.pronouns, first_message: f.greeting.trim(),
        lines, example_dialogue: lines.map((l) => `${f.name.trim()}: ${l}`).join('\n'),
        portrait: f.portrait, focus: f.focus, alt: f.alt, places: f.places, relationships: f.relationships, fade: f.fade, doubt: f.doubt,
        model: f.model ? { provider_id: Number(f.model.split(':')[0]), model: f.model.split(':').slice(1).join(':') } : undefined,
        edits: item ? (item.data.edits ?? 0) + 1 : 0,
      },
    }
    try {
      const saved = item ? await api<Item>(`/library/${item.id}`, 'PATCH', body) : await api<Item>('/library', 'POST', { kind: 'character', ...body })
      setBase(formOf(saved))
      reload()
      return saved
    } finally {
      setSaving(false)
    }
  }
  const saveAndGo = async (draftOnly = false) => {
    const saved = await save(draftOnly)
    if (saved) setTimeout(() => navigate(`/characters/${saved.id}`), 0) // after the form is clean
  }
  const choose = async (file: File | undefined) => {
    if (!file) return
    const ok = /^image\/(png|jpeg|webp)$/.test(file.type) && file.size <= 20 * 1024 * 1024
    if (!ok) return setFocusing({ src: '', bad: true })
    const made = await upload(file)
    setFocusing({ src: mediaUrl(made.name), name: made.name })
  }

  const ready = nameOk && hiOk
  const readyTone = edit ? 'info' : ready ? 'ok' : 'bad'
  const readyTitle = edit ? t('ed.ready.edit', { p }) : ready ? t('ed.ready.ok') : t('ed.ready.no')
  const readyText = edit ? t('ed.ready.editBody', { p }) : !ready ? t('ed.ready.noBody') : f.secret.trim() ? t('ed.ready.full', { name: f.name }) : t('ed.ready.draft', { name: f.name, p })
  const portraitSrc = f.portrait ? mediaUrl(f.portrait) : undefined

  if (id && !item) return <main className="app__main"><K.Skeleton /></main>
  return (
    <main className="app__main" aria-label={edit ? t('ed.editTitle', { name: firstLoad.name }) : t('ed.newTitle')} style={{ gap: 26 }}
      onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); choose(e.dataTransfer.files[0]) }}>
      <K.TopBar back={t('pf.back')} backHref={edit ? `/characters/${id}` : '/characters'} />
      <div className="pg-head">
        <div>
          <h1 className="pg-title">{edit ? t('ed.editTitle', { name: firstLoad.name }) : t('ed.newTitle')}</h1>
          <p className="pg-sub">{edit ? t('ed.editSub', { date: new Date(utc(item!.created_at)).toLocaleDateString('en-GB', { dateStyle: 'medium' }), stories: theirs.length }) : t('ed.newSub')}</p>
        </div>
        {!edit && <K.Button icon="download" href="/characters">{t('ed.import')}</K.Button>}
      </div>
      {tried && !ready && !edit && <K.Callout tone="bad" title={t('ed.missing')}>{t('ed.missingBody')}</K.Callout>}
      {edit && <K.Callout title={t('ed.editNote')}>{t('ed.editNoteBody', { name: firstLoad.name, p })}</K.Callout>}

      <div className="ed-grid">
        <div className="col" style={{ gap: 26, minWidth: 0 }}>
          <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={(e) => choose(e.target.files?.[0])} />
          {!f.portrait ? (
            <K.DropZone title={t('ed.face')} description={t('ed.faceSub')} empty={t('ed.noFace')}>
              <K.Button size="sm" onClick={() => fileRef.current?.click()}>{t('ed.chooseFile')}</K.Button>
              <K.Button size="sm" variant="ghost" onClick={() => setPicking(true)}>{t('ed.pickSet')}</K.Button>
            </K.DropZone>
          ) : (
            <div className="card ed-face">
              <img src={portraitSrc} alt={f.alt ?? ''} style={{ objectPosition: f.focus }} />
              <div className="col" style={{ gap: 6, flex: 1 }}>
                <span style={{ fontSize: 14.5, fontWeight: 700 }}>{t('ed.portrait')}</span>
                <span className="t-meta">{t('ed.portraitMeta', { focus: f.focus ?? '50% 40%' })}</span>
              </div>
              <K.ButtonGroup>
                <K.Button size="sm" onClick={() => setFocusing({ src: portraitSrc!, name: f.portrait })}>{t('ed.cropFocus')}</K.Button>
                <K.Button size="sm" variant="ghost" onClick={() => fileRef.current?.click()}>{t('ed.replace')}</K.Button>
                <K.Button size="sm" variant="ghost" onClick={() => setF((x) => ({ ...x, portrait: undefined, focus: undefined, alt: undefined }))}>{t('ed.remove')}</K.Button>
              </K.ButtonGroup>
            </div>
          )}

          <section className="col" style={{ gap: 16 }}>
            <K.Eyebrow tone="accent">{t('ed.required')}</K.Eyebrow>
            <div id="ed-name">
              <K.TextField label={t('ed.name')} required max={40} value={f.name} onChange={(v) => set('name', v)}
                hint={taken ? t('ed.nameTaken', { name: f.name.trim() }) : t('ed.nameHint')} error={tried && !nameOk ? t('ed.nameErr') : undefined} />
            </div>
            <div id="ed-hi">
              <K.TextArea label={t('ed.hi')} required story rows={3} value={f.greeting} onChange={(v) => set('greeting', v)} placeholder={t('ed.hiPlaceholder')}
                hint={t('ed.hiHint')} error={tried && !hiOk ? t('ed.hiErr') : undefined} />
            </div>
            <K.ChoiceChips label={t('ed.stuck')} options={MOODS.map((m) => t(`ed.m.${m}` as Key))}
              onPick={(o) => { const m = MOODS.find((x) => t(`ed.m.${x}` as Key) === o); if (m) set('greeting', t(`ed.g.${m}` as Key)) }} />
          </section>

          <section className="col" style={{ gap: 12 }}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <K.Eyebrow>{t('ed.optional')}</K.Eyebrow>
              <span className="t-faint">{t('ed.written', { n: SECTIONS.filter(([s]) => filled[s](f)).length })}</span>
            </div>
            <div className="card" style={{ overflow: 'hidden' }}>
              {SECTIONS.map(([s, title, sub, icon]) => {
                const on = open.includes(s)
                return (
                  <div key={s}>
                    <button type="button" className="opt" aria-expanded={on} onClick={() => setOpen((o) => (on ? o.filter((x) => x !== s) : [...o, s]))}>
                      <K.Icon name={icon} size={18} />
                      <span><span className="opt__t">{t(title)}</span><span className="opt__d">{t(sub)}</span></span>
                      <span className="opt__s">{t(filled[s](f) ? 'ed.s.written' : s === 'model' ? 'ed.s.default' : 'ed.s.empty')}</span>
                    </button>
                    {on && (
                      <div className="optbody">
                        {s === 'about' && (
                          <>
                            <K.TextField label={t('ed.tagline')} max={120} value={f.tagline} onChange={(v) => set('tagline', v)} hint={t('ed.taglineHint')} />
                            <K.TextArea label={t('ed.about')} story rows={4} value={f.about} onChange={(v) => set('about', v)} hint={t('ed.aboutHint')} />
                            <K.TextField label={t('ed.tags')} value={f.tags} onChange={(v) => set('tags', v)} hint={t('ed.tagsHint')} />
                            <K.Segmented label={t('ed.pronouns')} size="sm" options={PRONOUNS.map((x) => t(`pron.${x}` as Key))} value={t(`pron.${f.pronouns}` as Key)}
                              onChange={(v) => set('pronouns', PRONOUNS.find((x) => t(`pron.${x}` as Key) === v) ?? 'they')} />
                          </>
                        )}
                        {s === 'talk' && (
                          <>
                            {f.lines.map((l, i) => (
                              <K.TextArea key={i} label={t('ed.line', { n: i + 1 })} story rows={2} value={l} onChange={(v) => set('lines', f.lines.map((x, j) => (j === i ? v : x)))} />
                            ))}
                            {f.lines.length < 6 && <div><K.Button size="sm" variant="ghost" icon="plus" onClick={() => set('lines', [...f.lines, ''])}>{t('ed.addLine')}</K.Button></div>}
                          </>
                        )}
                        {s === 'secret' && <K.TextArea label={t('ed.secret')} story rows={3} value={f.secret} onChange={(v) => set('secret', v)} hint={t('ed.secretHint')} />}
                        {s === 'rels' && (
                          <>
                            {f.relationships.map((r, i) => {
                              const who: [number, string][] = others.map((o) => [o.id, o.name])
                              return (
                                <div key={i} className="ed-rel">
                                  <K.Select label={t('ed.relWho')} options={who.map(([, n]) => n)} value={byId.get(r.id)?.name}
                                    onChange={(v) => set('relationships', f.relationships.map((x, j) => (j === i ? { ...x, id: who.find(([, n]) => n === v)?.[0] ?? x.id } : x)))} />
                                  <K.Select label={t('ed.relFeels')} options={RELS.map((x) => t(`rel.${x}` as Key, { p: 'other' }))} value={t(`rel.${r.feels}` as Key, { p: 'other' })}
                                    onChange={(v) => set('relationships', f.relationships.map((x, j) => (j === i ? { ...x, feels: RELS.find((q) => t(`rel.${q}` as Key, { p: 'other' }) === v) ?? 'friend' } : x)))} />
                                  <K.IconButton icon="x" label={t('ed.relRemove')} size="sm" onClick={() => set('relationships', f.relationships.filter((_, j) => j !== i))} />
                                </div>
                              )
                            })}
                            {others.length > 0 && <div><K.Button size="sm" variant="ghost" icon="plus" onClick={() => set('relationships', [...f.relationships, { id: others[0].id, feels: 'friend' }])}>{t('ed.relAdd')}</K.Button></div>}
                          </>
                        )}
                        {s === 'places' && (
                          <div className="row row--wrap" style={{ gap: 8 }}>
                            {places.map((pl) => (
                              <K.Chip key={pl.id} icon="map-pin" pressed={f.places.includes(pl.id)}
                                onPress={() => set('places', f.places.includes(pl.id) ? f.places.filter((x) => x !== pl.id) : [...f.places, pl.id])}>{pl.name}</K.Chip>
                            ))}
                          </div>
                        )}
                        {s === 'model' && (
                          <>
                            <K.Select label={t('ed.modelLabel')} hint={t('ed.modelHint')} options={modelOptions.map(([, l]) => l)} value={modelOptions.find(([k]) => k === f.model)?.[1]}
                              onChange={(v) => set('model', modelOptions.find(([, l]) => l === v)?.[0] ?? '')} />
                            <K.Segmented label={t('ed.fade')} size="sm" options={FADES.map((x) => (x === 'inherit' ? t('ed.fadeInherit') : t(`fade.${x}` as Key)))}
                              value={f.fade === 'inherit' ? t('ed.fadeInherit') : t(`fade.${f.fade}` as Key)}
                              onChange={(v) => set('fade', FADES.find((x) => (x === 'inherit' ? t('ed.fadeInherit') : t(`fade.${x}` as Key)) === v) ?? 'inherit')} />
                            <div className="row" style={{ gap: 12 }}><K.Toggle label={t('ed.canDoubt')} on={f.doubt} onToggle={(v) => set('doubt', v)} /><span className="t-body">{t('ed.canDoubt')}</span></div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        </div>

        <aside aria-label={t('ed.look')} className="col ed-aside">
          <K.Eyebrow>{t('ed.look')}</K.Eyebrow>
          <div className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 14, alignItems: 'flex-start' }}>
            <K.CharacterCard src={portraitSrc} focus={f.focus} name={f.name.trim() || '?'} line={f.tagline || f.about.split(/(?<=[.!?])\s/)[0]} when={t('ed.previewWhen')}
              badge={!f.secret.trim() ? t('chars.badge.draft') : undefined} alt={f.alt} />
            {hiOk && <K.Bubble>{f.greeting}</K.Bubble>}
          </div>
          <K.Callout tone={readyTone} title={readyTitle}>{readyText}</K.Callout>
          {edit ? (
            <>
              {dirty && <span className="t-meta">{t('ed.unsaved', { n: sections.length })} · {sections.map((s) => t(SECTIONS.find(([x]) => x === s)![1])).join(', ')}</span>}
              <K.Button variant="primary" size="lg" full disabled={!dirty || !nameOk || !hiOk} loading={saving} onClick={() => saveAndGo()}>{t('ed.save')}</K.Button>
              <K.Button variant="ghost" disabled={!dirty} onClick={() => setF(firstLoad)}>{t('ed.discard')}</K.Button>
            </>
          ) : (
            <>
              <K.Button variant="primary" size="lg" full loading={saving} onClick={() => saveAndGo()}>{nameOk ? t('ed.create', { name: f.name.trim() }) : t('ed.createBare')}</K.Button>
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <K.Button variant="ghost" disabled={!nameOk} onClick={() => saveAndGo(true)}>{t('ed.draft')}</K.Button>
                <K.Button variant="ghost" onClick={() => navigate(-1)}>{t('ed.cancel')}</K.Button>
              </div>
            </>
          )}
          <div className="privacy"><K.Icon name="lock" size={16} /><span>{t('ed.saved')}</span></div>
        </aside>
      </div>

      {picking && (
        <Picker onClose={() => setPicking(false)} onPick={async (src, focus) => {
          setPicking(false)
          const made = await upload(await (await fetch(src)).blob())
          setF((x) => ({ ...x, portrait: made.name, focus }))
        }} />
      )}
      {focusing && (
        <Focus src={focusing.src} bad={focusing.bad} focus={f.focus} alt={f.alt} name={f.name} onClose={() => setFocusing(undefined)} onChoose={() => fileRef.current?.click()}
          onUse={(focus, alt) => { setF((x) => ({ ...x, portrait: focusing.name ?? x.portrait, focus, alt })); setFocusing(undefined) }} />
      )}
      {blocker.state === 'blocked' && (
        <Overlay onClose={() => blocker.reset()}>
          <K.Dialog icon="alert" tone="warm" size="sm" title={t('leave.title')} onClose={() => blocker.reset()}
            description={t('leave.body', { sections: new Intl.ListFormat('en').format(sections.map((s) => t(SECTIONS.find(([x]) => x === s)![1]).toLowerCase())) })}
            actions={[
              <K.Button key="k" variant="ghost" onClick={() => blocker.reset()}>{t('leave.keep')}</K.Button>,
              <K.Button key="d" variant="danger" onClick={() => blocker.proceed()}>{t('leave.discard')}</K.Button>,
              <K.Button key="s" variant="primary" onClick={async () => ((await save()) ? blocker.proceed() : blocker.reset())}>{t('leave.save')}</K.Button>,
            ]} />
        </Overlay>
      )}
    </main>
  )
}

/** F4: Kataki's own portraits. */
function Picker({ onClose, onPick }: { onClose: () => void; onPick: (src: string, focus: string) => void }) {
  const [n, setN] = useState(0)
  return (
    <Overlay onClose={onClose}>
      <section className="dlg dlg--xl" role="dialog" aria-modal="true" aria-labelledby="pick-title">
        <div className="dlg__head">
          <div className="dlg__titles"><h2 className="dlg__title" id="pick-title">{t('pick.title')}</h2><p className="dlg__desc">{t('pick.body')}</p></div>
          <K.IconButton icon="x" label="Close" size="sm" onClick={onClose} />
        </div>
        <div className="dlg__body">
          <div className="ed-set" role="radiogroup" aria-label={t('pick.title')}
            onKeyDown={(e) => { const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]; if (d) { e.preventDefault(); setN((x) => (x + d + SET.length) % SET.length) } }}>
            {SET.map(([src, focus], i) => (
              <button key={src} type="button" role="radio" aria-checked={i === n} aria-label={t('pick.n', { n: i + 1 })} tabIndex={i === n ? 0 : -1}
                className="ed-set__item" onClick={() => setN(i)} onDoubleClick={() => onPick(src, focus)}>
                <img src={src} alt="" style={{ objectPosition: focus }} />
              </button>
            ))}
          </div>
        </div>
        <div className="dlg__foot">
          <span className="dlg__note">{t('pick.foot', { n: n + 1 })}</span>
          <div className="k-btngroup">
            <K.Button variant="ghost" onClick={onClose}>{t('pick.cancel')}</K.Button>
            <K.Button variant="primary" onClick={() => onPick(SET[n][0], SET[n][1])}>{t('pick.use')}</K.Button>
          </div>
        </div>
      </section>
    </Overlay>
  )
}

/** F5: where the face is, so every crop centres on it; and what the picture shows. */
function Focus({ src, bad, focus, alt, name, onClose, onChoose, onUse }: {
  src: string; bad?: boolean; focus?: string; alt?: string; name: string; onClose: () => void; onChoose: () => void; onUse: (focus: string, alt: string) => void
}) {
  const [x0, y0] = (focus ?? '50% 40%').split(' ').map((v) => parseFloat(v))
  const [at, setAt] = useState({ x: x0, y: y0 })
  const [text, setText] = useState(alt ?? '')
  const box = useRef<HTMLDivElement>(null)
  const place = (e: { clientX: number; clientY: number }) => {
    const r = box.current!.getBoundingClientRect()
    setAt({ x: Math.round(Math.max(0, Math.min(100, ((e.clientX - r.left) / r.width) * 100))), y: Math.round(Math.max(0, Math.min(100, ((e.clientY - r.top) / r.height) * 100))) })
  }
  const pos = `${at.x}% ${at.y}%`
  return (
    <Overlay onClose={onClose}>
      <section className="dlg dlg--xl" role="dialog" aria-modal="true" aria-labelledby="focus-title">
        <div className="dlg__head">
          <div className="dlg__titles"><h2 className="dlg__title" id="focus-title">{t('focus.title')}</h2><p className="dlg__desc">{t('focus.body')}</p></div>
          <K.IconButton icon="x" label="Close" size="sm" onClick={onClose} />
        </div>
        <div className="dlg__body">
          {bad ? (
            <K.Callout tone="bad" title={t('focus.bad')} action={<K.Button size="sm" onClick={() => { onClose(); onChoose() }}>{t('ed.chooseFile')}</K.Button>}>{t('focus.badBody')}</K.Callout>
          ) : (
            <div className="ed-focus">
              <div ref={box} className="ed-focus__img" onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); place(e) }}
                onPointerMove={(e) => e.buttons && place(e)}>
                <img src={src} alt="" />
                <span className="ed-focus__ring" role="slider" tabIndex={0} aria-label={t('focus.title')} aria-valuetext={t('focus.value', { x: at.x, y: at.y })}
                  style={{ left: `${at.x}%`, top: `${at.y}%` }}
                  onKeyDown={(e) => {
                    const step = e.shiftKey ? 10 : 1
                    const d = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[e.key]
                    if (d) { e.preventDefault(); setAt((a) => ({ x: Math.max(0, Math.min(100, a.x + d[0])), y: Math.max(0, Math.min(100, a.y + d[1])) })) }
                  }} />
              </div>
              <div className="col" style={{ gap: 14 }}>
                <K.Eyebrow>{t('focus.crops')}</K.Eyebrow>
                <div className="row" style={{ gap: 14, alignItems: 'flex-end' }}>
                  {[20, 40, 64].map((s) => <K.Avatar key={s} src={src} focus={pos} size={s} />)}
                </div>
                <div className="ed-focus__card"><img src={src} alt="" style={{ objectPosition: pos }} /></div>
                <span className="t-meta">{t('focus.value', { x: at.x, y: at.y })}</span>
                <K.TextField label={t('focus.alt')} hint={t('focus.altHint')} value={text} onChange={setText} placeholder={name} />
              </div>
            </div>
          )}
        </div>
        <div className="dlg__foot">
          <span />
          <div className="k-btngroup">
            <K.Button variant="ghost" onClick={onClose}>{t('focus.cancel')}</K.Button>
            {!bad && <K.Button variant="primary" onClick={() => onUse(pos, text.trim())}>{t('focus.use')}</K.Button>}
          </div>
        </div>
      </section>
    </Overlay>
  )
}

