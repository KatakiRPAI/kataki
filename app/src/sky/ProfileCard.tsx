// The profile card: you, the person behind the personas. It lives in the library's `profile`
// setting, so it travels with the library (docs/specs/2026-10-02-profiles-and-accounts.md P2).
import { useState, type CSSProperties } from 'react'
import { api, mediaUrl, upload, type Pronouns } from '../api'
import { K } from '../ds'
import { useLoad } from '../hooks'
import { Overlay } from '../overlay'
import { setPref, usePrefs } from '../prefs'
import { lang, t, type Key } from '../strings'
import { Crop, type Picture } from './Crop'

export type Card = Picture & { name?: string; pronouns?: Pronouns; bio?: string; accent?: string }
type Stats = { stories: number; characters: number; words: number; days: number }

const PRONOUNS: Pronouns[] = ['she', 'he', 'they']
const compact = new Intl.NumberFormat(lang, { notation: 'compact' })

export default function ProfileCard() {
  const [prefs, loaded] = usePrefs()
  const card = (prefs.profile ?? {}) as Card
  const [stats] = useLoad(() => api<Stats>('/profile/stats'), [])
  const [editing, setEditing] = useState(false)
  if (!loaded) return null
  const n = (key: keyof Stats, label: Key): [string, string] => [compact.format(stats?.[key] ?? 0), t(label, { n: stats?.[key] ?? 0 })]
  return (
    <section className="card card--pad pc" aria-label={t('pc.title')} style={{ '--pc': card.accent } as CSSProperties}>
      <span className="pc__face"><K.Avatar src={card.portrait ? mediaUrl(card.portrait) : undefined} focus={card.focus} zoom={card.zoom} alt={card.alt} name={card.name || '?'} size={72} /></span>
      <div className="col" style={{ gap: 4, flex: 1, minWidth: 0 }}>
        <K.Eyebrow tone="mid">{t('pc.title')}</K.Eyebrow>
        <h2 className="pc__name">{card.name || t('pc.unnamed')}{card.name && card.pronouns && <span className="t-meta">{t(`pron.${card.pronouns}` as Key)}</span>}</h2>
        <p className="pc__bio">{card.bio || t('pc.blank')}</p>
      </div>
      <K.StatRow stats={[n('stories', 'pc.stories'), n('characters', 'pc.characters'), n('words', 'pc.words'), n('days', 'pc.days')]} />
      <K.Button size="sm" icon="edit" onClick={() => setEditing(true)}>{t(card.name ? 'pc.edit' : 'pc.setUp')}</K.Button>
      {editing && <EditCard card={card} onClose={() => setEditing(false)} />}
    </section>
  )
}

function EditCard({ card, onClose }: { card: Card; onClose: () => void }) {
  const [name, setName] = useState(card.name ?? '')
  const [bio, setBio] = useState(card.bio ?? '')
  const [pronouns, setPronouns] = useState<Pronouns | undefined>(card.pronouns)
  const [accent, setAccent] = useState(card.accent)
  const [pic, setPic] = useState<Picture>({ portrait: card.portrait, focus: card.focus, zoom: card.zoom, alt: card.alt })
  const [cropping, setCropping] = useState<string>() // a media name
  const none = t('pc.pronounsNone')
  const save = async () => {
    await setPref('profile', { name: name.trim(), bio: bio.trim().slice(0, 190), pronouns, accent, ...pic })
    // the desktop's list of profiles shows the same name
    const shell = window.kataki
    if (name.trim() && shell?.profiles) shell.profiles().then((s) => shell.profileRename!(s.current, name.trim()))
    onClose()
  }
  if (cropping) return <Crop src={mediaUrl(cropping)} {...(cropping === pic.portrait ? pic : {})} name={name} onClose={() => setCropping(undefined)} onUse={(focus, zoom, alt) => { setPic({ portrait: cropping, focus, zoom, alt }); setCropping(undefined) }} />
  return (
    <Overlay onClose={onClose}>
      <K.Dialog size="lg" title={t('pc.editTitle')} description={t('pc.editBody')} onClose={onClose}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>, <K.Button key="s" variant="primary" disabled={!name.trim()} onClick={save}>{t('ep.save')}</K.Button>]}>
        <div className="row" style={{ gap: 14 }}>
          <K.Avatar src={pic.portrait ? mediaUrl(pic.portrait) : undefined} focus={pic.focus} zoom={pic.zoom} name={name || '?'} size={64} />
          <label className="k-btn k-btn--secondary k-btn--sm">{t(pic.portrait ? 'ep.picture' : 'ep.pictureAdd')}<input type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={async (e) => { const f = e.target.files?.[0]; if (f) setCropping((await upload(f)).name) }} /></label>
          {pic.portrait && <K.Button size="sm" onClick={() => setCropping(pic.portrait)}>{t('ed.cropFocus')}</K.Button>}
          {pic.portrait && <K.Button size="sm" variant="ghost" onClick={() => setPic({})}>{t('ep.remove')}</K.Button>}
        </div>
        <div className="ep-pair">
          <K.TextField label={t('pc.name')} required value={name} onChange={setName} max={40} />
          <K.Select label={t('ep.pronouns')} options={[none, ...PRONOUNS.map((x) => t(`pron.${x}` as Key))]} value={pronouns ? t(`pron.${pronouns}` as Key) : none} onChange={(v) => setPronouns(PRONOUNS.find((x) => t(`pron.${x}` as Key) === v))} />
        </div>
        <K.TextArea label={t('pc.bio')} rows={3} value={bio} onChange={(v) => setBio(v.slice(0, 190))} hint={t('pc.bioHint', { n: 190 - bio.length })} />
        <K.Field label={t('pc.accent')} hint={t('pc.accentHint')}>
          <div className="row" style={{ gap: 10 }}>
            <input type="color" aria-label={t('pc.accent')} value={accent ?? '#8fb4ff'} onChange={(e) => setAccent(e.target.value)} />
            {accent && <K.Button size="sm" variant="ghost" onClick={() => setAccent(undefined)}>{t('ep.remove')}</K.Button>}
          </div>
        </K.Field>
      </K.Dialog>
    </Overlay>
  )
}
