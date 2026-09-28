// You (J1–J3): who you play as, and what each character knows about them.
import { useState } from 'react'
import { api, mediaUrl, upload, type Item, type Person, type Profile, type Pronouns, type StorySummary } from '../api'
import { isPersona } from '../characters'
import { K } from '../ds'
import { face, useLibrary, useLoad } from '../hooks'
import { Overlay, toast } from '../overlay'
import { setPref, usePrefs } from '../prefs'
import { t, type Key } from '../strings'

const PRONOUNS: Pronouns[] = ['she', 'he', 'they']

export default function You() {
  const { items, reload } = useLibrary()
  const [prefs] = usePrefs()
  const personas = items.filter(isPersona)
  const def = prefs.persona as number | null | undefined
  const [picked, setPicked] = useState<number | null>()
  const current = picked === undefined ? (def === null ? null : personas.find((p) => p.id === def) ?? personas[0]) : picked === null ? null : personas.find((p) => p.id === picked)
  const [editing, setEditing] = useState<Item | 'new'>()
  const [deleting, setDeleting] = useState<Item>()
  const [stories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  return (
    <main className="app__main" aria-label={t('you.title')} style={{ gap: 26 }}>
      <div className="pg-head"><div><h1 className="pg-title">{t('you.title')}</h1><p className="pg-sub">{t('you.sub')}</p></div></div>
      <div className="row row--wrap" style={{ gap: 14, alignItems: 'stretch' }}>
        {personas.map((p) => {
          const isDef = p.id === (def ?? personas[0]?.id) && def !== null
          return (
            <div key={p.id} className="you-card">
              <button type="button" className="ns-pick" aria-pressed={current?.id === p.id} onClick={() => setPicked(p.id)}>
                <K.PersonaCard {...face(p)} name={p.name} line={p.description} isDefault={isDef} selected={current?.id === p.id} />
              </button>
              <div className="row" style={{ gap: 6 }}>
                {isDef ? <K.StatePill tone="accent">{t('you.default')}</K.StatePill> : <K.Button size="sm" variant="ghost" onClick={() => setPref('persona', p.id)}>{t('you.switch')}</K.Button>}
                <K.Button size="sm" variant="ghost" icon="edit" onClick={() => setEditing(p)}>{t('you.edit')}</K.Button>
              </div>
            </div>
          )
        })}
        <div className="you-card">
          <button type="button" className="ns-pick" aria-pressed={current === null} onClick={() => setPicked(null)}>
            <K.PersonaCard icon="feather" name={t('you.director')} line={t('you.directorLine')} selected={current === null} isDefault={def === null} />
          </button>
          {def !== null && <K.Button size="sm" variant="ghost" onClick={() => setPref('persona', null)}>{t('you.switch')}</K.Button>}
        </div>
        <K.AddCard wide icon="user" onClick={() => setEditing('new')}>{t('you.new')}</K.AddCard>
      </div>
      {current && <Knows persona={current} stories={stories ?? []} onDelete={() => setDeleting(current)} />}
      {editing && <EditPersona p={editing === 'new' ? undefined : editing} isDefault={editing !== 'new' && editing.id === def} stories={stories ?? []}
        onClose={() => setEditing(undefined)} onDone={reload} />}
      {deleting && <DeletePersona p={deleting} isDefault={deleting.id === (def ?? personas[0]?.id)} onClose={() => setDeleting(undefined)}
        onDone={() => { setPicked(undefined); reload() }} />}
    </main>
  )
}

/** Who knows this persona: per character, per story, how sure they are. */
function Knows({ persona, stories, onDelete }: { persona: Item; stories: StorySummary[]; onDelete: () => void }) {
  const [profile] = useLoad(() => api<Profile>(`/library/${persona.id}/profile`), [persona.id])
  const played = (profile?.stories ?? []).filter((s) => s.role === 'persona')
  const [people, reload] = useLoad(async () => {
    const all: (Person & { story: string; storyId: number })[] = []
    for (const s of played) for (const p of await api<Person[]>(`/stories/${s.id}/people`)) if (p.about_you?.count) all.push({ ...p, story: s.title, storyId: s.id })
    return all
  }, [profile])
  const forget = (id: number) => {
    api(`/memories/${id}`, 'PATCH', { hidden: true }).then(reload)
    toast(t('toast.forgot', { n: 1 }), { action: t('toast.undo'), onAction: () => api(`/memories/${id}`, 'PATCH', { hidden: false }).then(reload) })
  }
  return (
    <section className="sec" aria-label={t('you.knows', { name: persona.name })}>
      <h2 className="sec-title">{t('you.knows', { name: persona.name })}</h2>
      {!people?.length ? <p className="t-meta">{t('you.knowsNone', { name: persona.name })}</p> : (
        <K.Panel>
          <div className="col" style={{ gap: 18 }}>
            {people.map((who) => (
              <div key={`${who.storyId}-${who.id}`} className="col" style={{ gap: 10 }}>
                <div className="row" style={{ gap: 10 }}><K.Avatar name={who.name} size={28} /><b>{who.name}</b><span className="t-meta">{who.story}</span></div>
                {who.about_you!.samples.map((m) => (
                  <div key={m.memory_id} className="pf-memrow">
                    <K.MemoryRow word={t(m.belief < 0.7 ? 'mem.word.doubted' : (`mem.word.${m.tier}` as Key))} value={m.tier === 'sharp' ? 80 : m.tier === 'hazy' ? 40 : 10}
                      tone={m.belief < 0.7 ? 'warm' : m.tier === 'sharp' ? 'ok' : 'muted'}
                      meta={t('you.meta', { name: who.name, story: who.story, word: t(`mem.word.${m.tier}` as Key) })}>{m.text}</K.MemoryRow>
                    <K.Button size="sm" variant="ghost" onClick={() => forget(m.memory_id)}>{t('you.forget', { p: 'other' })}</K.Button>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </K.Panel>
      )}
      <div className="row" style={{ gap: 16 }}>
        <span className="t-meta">{t('ep.note', { n: stories.filter((s) => s.persona?.lib_item_id === persona.id).length })}</span>
        <button type="button" className="linkbtn" onClick={onDelete}>{t('you.delete')}</button>
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
      <K.Dialog icon="user" size="lg" title={p ? t('ep.title', { name: p.name }) : t('ep.newTitle')} description={t('ep.body')} onClose={onClose}
        note={p && isDefault ? t('ep.note', { n: stories.filter((s) => s.persona?.lib_item_id === p.id).length }) : undefined}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>, <K.Button key="s" variant="primary" disabled={!name.trim()} onClick={save}>{t('ep.save')}</K.Button>]}>
        <div className="row" style={{ gap: 14 }}>
          <K.Avatar src={portrait ? mediaUrl(portrait) : undefined} name={name || '?'} size={64} />
          <label className="k-btn k-btn--secondary k-btn--sm">{t(portrait ? 'ep.picture' : 'ep.pictureAdd')}<input type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={async (e) => { const f = e.target.files?.[0]; if (f) setPortrait((await upload(f)).name) }} /></label>
          {portrait && <K.Button size="sm" variant="ghost" onClick={() => setPortrait(undefined)}>{t('ep.remove')}</K.Button>}
        </div>
        <K.TextField label={t('ep.name')} required story value={name} onChange={setName} max={60} />
        <K.Select label={t('ep.pronouns')} options={PRONOUNS.map((x) => t(`pron.${x}` as Key))} value={t(`pron.${pronouns}` as Key)} onChange={(v) => setPronouns(PRONOUNS.find((x) => t(`pron.${x}` as Key) === v) ?? 'they')} />
        <K.TextArea label={t('ep.who')} story rows={3} value={who} onChange={setWho} />
        <K.TextField label={t('ep.tags')} hint={t('ed.tagsHint')} value={tags} onChange={setTags} />
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
      <K.Dialog icon="trash" tone="bad" title={t('dp.title', { name: p.name })} description={t('dp.body', { name: p.name })} onClose={onClose}
        actions={[<K.Button key="k" variant="ghost" onClick={onClose}>{t('dp.keep', { name: p.name })}</K.Button>, <K.Button key="d" variant="danger" onClick={go}>{t('dp.go')}</K.Button>]} />
    </Overlay>
  )
}
