// You (J1–J3): who you play as, and what each character knows about them.
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { api, mediaUrl, upload, type Item, type Person, type Profile, type Pronouns, type StorySummary } from '../api'
import { fullName, isPersona, pronoun, tagline } from '../characters'
import { K } from '../ds'
import { face, useLibrary, useLoad } from '../hooks'
import { Overlay, toast, withMenu, type MenuItem } from '../overlay'
import { setPref, usePrefs } from '../prefs'
import { personaMenu } from './Palette'
import { t, type Key } from '../strings'

const PRONOUNS: Pronouns[] = ['she', 'he', 'they']

export default function You() {
  const navigate = useNavigate()
  const { items, reload } = useLibrary()
  const [prefs] = usePrefs()
  const def = prefs.persona as number | null | undefined
  const personas = items.filter(isPersona).sort((a, b) => Number(b.id === def) - Number(a.id === def)) // the default first
  const [picked, setPicked] = useState<number | null>()
  const current = picked === undefined ? (def === null ? null : personas.find((p) => p.id === def) ?? personas[0]) : picked === null ? null : personas.find((p) => p.id === picked)
  const [params] = useSearchParams()
  const [editing, setEditing] = useState<Item | 'new' | undefined>(() => (params.get('new') ? 'new' : undefined))
  const [deleting, setDeleting] = useState<Item>()
  const [stories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [known, reloadKnown] = useLoad(() => (current ? knownAbout(current) : Promise.resolve([])), [current?.id])
  // PersonaCardMenu (M1)
  const personaCardMenu = (p: Item): MenuItem[] => [
    { label: t('pcm.play', { name: p.name }), icon: 'user', disabled: isDef(p), onSelect: () => setPref('persona', p.id) },
    { label: t('you.edit'), icon: 'edit', onSelect: () => setEditing(p) },
    { label: t('menu.duplicate'), icon: 'layers', onSelect: () => api<Item>('/library', 'POST', { kind: p.kind, name: `${p.name} (2)`, description: p.description, private: p.private, data: p.data, tags: p.tags }).then(reload) },
    { divider: true },
    { label: t('pcm.delete'), icon: 'trash', danger: true, disabled: isDef(p), onSelect: () => setDeleting(p) },
  ]
  const isDef = (p: Item) => p.id === (def ?? personas[0]?.id) && def !== null
  const played = current ? (stories ?? []).filter((s) => s.persona?.lib_item_id === current.id).length : 0
  const f: { who?: string; src?: string } = current ? face(current) : {}
  return (
    <main className="app__main" aria-label={t('you.title')} style={{ gap: 28 }}>
      <div className="pg-head">
        <div><h1 className="pg-title">{t('you.title')}</h1><p className="pg-sub">{t('you.sub')}</p></div>
        <K.Button icon="plus" onClick={() => setEditing('new')}>{t('you.new')}</K.Button>
      </div>

      {current && (
        <section className="you-hero">
          {f.src ?? (f.who && K.ART[f.who]?.src) ? <img className="you-portrait" src={f.src ?? K.ART[f.who!]!.src!} alt={current.name} style={{ objectPosition: current.data.focus ?? K.ART[f.who ?? '']?.focus }} />
            : <K.Avatar name={current.name} size={120} />}
          <div className="col" style={{ gap: 12, flex: 1 }}>
            <K.Eyebrow tone="mid">{t(isDef(current) ? 'you.default' : 'you.persona')}</K.Eyebrow>
            <h2 className="you-name">{fullName(current)}</h2>
            {tagline(current) && <p className="you-line">{tagline(current)}</p>}
            {current.tags.length > 0 && <div className="row" style={{ gap: 8 }}>{current.tags.map((g) => <K.Tag key={g}>{g}</K.Tag>)}</div>}
            <div className="row" style={{ gap: 10 }}>
              <K.Button icon="edit" onClick={() => setEditing(current)}>{t('you.edit')}</K.Button>
              <span onClick={(e) => personaMenu(e.currentTarget, items, def, navigate)}><K.Button variant="ghost" icon="swap">{t('you.switchTo')}</K.Button></span>
            </div>
          </div>
          <K.StatRow stats={[[String(played), t('you.stories', { n: played })], [String(new Set(known?.map((k) => k.who)).size), t('you.knowers', { n: new Set(known?.map((k) => k.who)).size, p: pronoun(current) })]]} />
        </section>
      )}

      <section className="sec" aria-label={t('you.personas')}>
        <h2 className="sec-title">{t('you.personas')}</h2>
        <div className="row row--wrap" style={{ gap: 14, alignItems: 'stretch' }}>
          {personas.map((p) => (
            <button key={p.id} type="button" className="ns-pick" aria-pressed={current?.id === p.id} onClick={() => setPicked(p.id)} {...withMenu(() => personaCardMenu(p))}>
              <K.PersonaCard {...face(p)} name={fullName(p)} line={tagline(p)} isDefault={isDef(p)} selected={current?.id === p.id} />
            </button>
          ))}
          <button type="button" className="ns-pick" aria-pressed={current === null} onClick={() => setPicked(null)}>
            <K.PersonaCard icon="eye" name={t('you.director')} line={t('you.directorLine')} selected={current === null} isDefault={def === null} />
          </button>
          <div style={{ width: 220 }}><K.AddCard wide onClick={() => setEditing('new')}>{t('you.new')}</K.AddCard></div>
        </div>
        {current && !isDef(current) && <div><K.Button size="sm" variant="ghost" onClick={() => setPref('persona', current.id)}>{t('you.switch')}</K.Button></div>}
        {current === null && def !== null && <div><K.Button size="sm" variant="ghost" onClick={() => setPref('persona', null)}>{t('you.switch')}</K.Button></div>}
      </section>

      {current && <Knows persona={current} known={known} reload={reloadKnown} onDelete={() => setDeleting(current)} />}
      {editing && <EditPersona p={editing === 'new' ? undefined : editing} isDefault={editing !== 'new' && editing.id === def} stories={stories ?? []}
        onClose={() => setEditing(undefined)} onDone={reload} />}
      {deleting && <DeletePersona p={deleting} isDefault={deleting.id === (def ?? personas[0]?.id)} onClose={() => setDeleting(undefined)}
        onDone={() => { setPicked(undefined); reload() }} />}
    </main>
  )
}

type Known = { memory: number; text: string; who: string; story: string; tier: string; belief: number }

/** Every memory a character holds about this persona, in every story it was played in. */
async function knownAbout(persona: Item): Promise<Known[]> {
  const profile = await api<Profile>(`/library/${persona.id}/profile`)
  const out: Known[] = []
  for (const s of profile.stories.filter((x) => x.role === 'persona')) {
    for (const p of await api<Person[]>(`/stories/${s.id}/people`)) {
      for (const m of p.about_you?.samples ?? []) out.push({ memory: m.memory_id, text: m.text, who: p.name, story: s.title, tier: m.tier, belief: m.belief })
    }
  }
  return out
}

/** Who knows this persona: per character, per story, how sure they are. */
function Knows({ persona, known, reload, onDelete }: { persona: Item; known: Known[] | undefined; reload: () => void; onDelete: () => void }) {
  const { items } = useLibrary()
  const [only, setOnly] = useState('')
  const names = [...new Set((known ?? []).map((k) => k.who))]
  const everyone = t('you.everyone')
  const rows = (known ?? []).filter((k) => !only || k.who === only)
  const forget = (id: number) => {
    api(`/memories/${id}`, 'PATCH', { hidden: true }).then(reload)
    toast(t('toast.forgot', { n: 1 }), { action: t('toast.undo'), onAction: () => api(`/memories/${id}`, 'PATCH', { hidden: false }).then(reload) })
  }
  const name = persona.name
  return (
    <section className="sec" aria-label={t('you.knows', { name })}>
      <div className="sec-head">
        <div className="row" style={{ gap: 14, alignItems: 'baseline' }}><h2 className="sec-title">{t('you.knows', { name })}</h2><span className="t-meta">{t('you.knowsSub')}</span></div>
        {names.length > 0 && <div style={{ width: 200 }}><K.Select label="" options={[everyone, ...names]} value={only || everyone} onChange={(v) => setOnly(v === everyone ? '' : v)} /></div>}
      </div>
      {!rows.length ? <p className="t-meta">{t('you.knowsNone', { name })}</p> : (
        <div className="card">
          {rows.map((k) => {
            const who = items.find((i) => i.kind === 'character' && i.name === k.who)
            const doubted = k.belief < 0.7
            return (
              <div key={k.memory} className="know">
                <span className="know__text">{k.text}</span>
                <span className="row" style={{ gap: 8 }}><K.Avatar {...face(who, k.who)} size={22} alt={k.who} /><span className="t-meta">{t('you.where', { name: k.who, story: k.story })}</span></span>
                <K.StatePill tone={doubted ? 'warm' : k.tier === 'sharp' ? 'ok' : 'muted'}>{t(doubted ? 'mem.word.doubted' : (`mem.word.${k.tier}` as Key))}</K.StatePill>
                <K.Button size="sm" variant="ghost" onClick={() => forget(k.memory)}>{t('you.forget', { p: pronoun(who) })}</K.Button>
              </div>
            )
          })}
        </div>
      )}
      <div className="row" style={{ gap: 20 }}>
        <span onClick={onDelete}><K.TextLink icon="trash" quiet>{t('you.delete')}</K.TextLink></span>
      </div>
    </section>
  )
}

/** J2: the person characters meet. */
function EditPersona({ p, isDefault, stories, onClose, onDone }: { p?: Item; isDefault: boolean; stories: StorySummary[]; onClose: () => void; onDone: () => void }) {
  const [name, setName] = useState(p?.name ?? '')
  const [who, setWho] = useState(p?.description ?? '')
  const [pronouns, setPronouns] = useState<Pronouns>(p?.data.pronouns ?? 'they')
  const [tags, setTags] = useState((p?.tags ?? []).join(', '))
  const [portrait, setPortrait] = useState(p?.data.portrait)
  const [makeDefault, setMakeDefault] = useState(isDefault)
  const save = async () => {
    const body = { name: name.trim(), description: who.trim(), tags: tags.split(',').map((x) => x.trim()).filter(Boolean).slice(0, 3), data: { ...(p?.data ?? {}), persona: true, pronouns, portrait } }
    const saved = p ? await api<Item>(`/library/${p.id}`, 'PATCH', body) : await api<Item>('/library', 'POST', { kind: 'character', ...body })
    if (makeDefault) await setPref('persona', saved.id)
    onDone()
    onClose()
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog size="lg" title={p ? t('ep.title', { name: fullName(p) }) : t('ep.newTitle')} description={t('ep.body')} onClose={onClose}
        note={p && isDefault ? t('ep.note', { n: stories.filter((s) => s.persona?.lib_item_id === p.id).length }) : undefined}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>, <K.Button key="s" variant="primary" disabled={!name.trim()} onClick={save}>{t('ep.save')}</K.Button>]}>
        <div className="row" style={{ gap: 14 }}>
          <K.Avatar src={portrait ? mediaUrl(portrait) : undefined} name={name || '?'} size={64} />
          <label className="k-btn k-btn--secondary k-btn--sm">{t(portrait ? 'ep.picture' : 'ep.pictureAdd')}<input type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={async (e) => { const f = e.target.files?.[0]; if (f) setPortrait((await upload(f)).name) }} /></label>
          {portrait && <K.Button size="sm" variant="ghost" onClick={() => setPortrait(undefined)}>{t('ep.remove')}</K.Button>}
        </div>
        <div className="ep-pair">
          <K.TextField label={t('ep.name')} required story value={name} onChange={setName} max={40} />
          <K.Select label={t('ep.pronouns')} options={PRONOUNS.map((x) => t(`pron.${x}` as Key))} value={t(`pron.${pronouns}` as Key)} onChange={(v) => setPronouns(PRONOUNS.find((x) => t(`pron.${x}` as Key) === v) ?? 'they')} />
        </div>
        <K.TextArea label={t('ep.who')} story rows={3} value={who} onChange={setWho} hint={t('ep.whoHint')} />
        <K.TextField label={t('ep.tags')} optional value={tags} onChange={setTags} />
        <div className="row" style={{ gap: 12 }}><K.Toggle label={t('ep.default', { name: name || '…' })} on={makeDefault} onToggle={setMakeDefault} /><span className="t-body">{t('ep.default', { name: name || '…' })}</span></div>
      </K.Dialog>
    </Overlay>
  )
}

/** J3: stop playing as someone. The default can't go until another takes its place. */
function DeletePersona({ p, isDefault, onClose, onDone }: { p: Item; isDefault: boolean; onClose: () => void; onDone: () => void }) {
  if (isDefault) {
    return (
      <Overlay onClose={onClose}>
        <K.Dialog icon="alert" tone="warm" size="sm" title={t('dp.default')} description={t('dp.defaultBody')} onClose={onClose}
          actions={[<K.Button key="c" onClick={onClose}>{t('dp.close')}</K.Button>]} />
      </Overlay>
    )
  }
  const go = async () => {
    await api(`/library/${p.id}`, 'DELETE')
    onDone()
    onClose()
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="trash" tone="bad" title={t('dp.title', { name: fullName(p) })} description={t('dp.body', { name: p.name })} onClose={onClose}
        actions={[<K.Button key="k" variant="ghost" onClick={onClose}>{t('dp.keep', { name: p.name })}</K.Button>, <K.Button key="d" variant="danger" onClick={go}>{t('dp.go')}</K.Button>]} />
    </Overlay>
  )
}
