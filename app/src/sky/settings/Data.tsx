// Data and privacy (K10, K11, K13): take it with you, bring it in, keys, delete.
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { bytes } from '../DiskFull'
import { api, download, sendFile, type Storage, type Item, type Provider, type StorySummary } from '../../api'
import { K } from '../../ds'
import { useLibrary, useLoad } from '../../hooks'
import { Overlay, toast } from '../../overlay'
import { setPref, usePrefs } from '../../prefs'
import { relative, t, type Key } from '../../strings'

export default function Data() {
  const navigate = useNavigate()
  const { reload } = useLibrary()
  const [providers, reloadProviders] = useLoad(() => api<Provider[]>('/providers'), [])
  const [busy, setBusy] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [backing, setBacking] = useState(false)
  const [list, reloadList] = useLoad(() => api<Backup[]>('/backups').catch(() => []), [])
  const keyed = (providers ?? []).filter((p) => p.has_key)
  const [places] = useLoad(() => api<Storage>('/storage').then((s) => s.places.filter((p) => p.what !== 'backups'), () => []), [])
  const [prefs] = usePrefs()
  const every = String(prefs['backups.every'] ?? 'daily')
  const exportAll = async () => {
    setBusy(true)
    try { toast(t('toast.exportedLib', { name: await download('/export/library') }), {}, 5000) } finally { setBusy(false) }
  }
  const importLibrary = async (file?: File) => {
    if (!file) return
    try {
      await sendFile('/import/kataki', file)
      reload()
      toast(t('toast.importedLib'), {}, 4000)
    } catch (e) {
      toast((e as Error).message, {}, 8000)
    }
  }
  return (
    <>
      <K.Callout tone="privacy" title={t('da.privacy')}>{t('da.privacyBody')}</K.Callout>
      {!!places?.length && (
        <K.SettingsSection title={t('da.where')}>
          {places.map((p) => (
            <K.FolderRow key={p.what} icon={p.what === 'library' ? 'book' : 'image'} label={t(`da.where.${p.what}` as Key)} path={p.path} size={size(p.bytes)}
              onOpen={window.kataki?.reveal ? () => window.kataki!.reveal!(p.what) : undefined} openLabel={t('da.open')} />
          ))}
        </K.SettingsSection>
      )}
      <K.SettingsSection title={t('da.take')}>
        <K.SettingsRow title={t('da.export')} description={t('da.exportSub')}><K.Button size="sm" icon="download" loading={busy} onClick={exportAll}>{t('da.exportBtn')}</K.Button></K.SettingsRow>
        <K.SettingsRow title={t('bk.row')} description={every === 'never' ? t('bk.off') : [t(`bk.${every}` as Key), t('bk.summary', { n: list?.length ?? 0, when: list?.[0] ? relative(Date.parse(list[0].at)) : 'none' })].join(' · ')}>
          <div className="row" style={{ gap: 12 }}>
            <K.Button size="sm" onClick={() => setBacking(true)}>{t('bk.change')}</K.Button>
            <K.Toggle label={t('bk.row')} on={every !== 'never'} onToggle={(on) => setPref('backups.every', on ? 'daily' : 'never')} />
          </div>
        </K.SettingsRow>
        <K.SettingsRow title={t('da.import')} description={t('da.importSub')}>
          <div className="row" style={{ gap: 8 }}>
            <K.Button onClick={() => navigate('/characters')}>{t('da.importCards')}</K.Button>
            <label className="k-btn k-btn--ghost">{t('da.importLibrary')}<input type="file" accept=".kataki" hidden onChange={(e) => importLibrary(e.target.files?.[0])} /></label>
          </div>
        </K.SettingsRow>
        <K.SettingsRow title={t('da.keys')} description={t('da.keysSub', { n: keyed.length, names: new Intl.ListFormat('en').format(keyed.map((p) => p.name)), os: /Win/.test(navigator.userAgent) ? 'win' : /Mac/.test(navigator.userAgent) ? 'mac' : 'other' })}>
          <K.Button size="sm" variant="ghost" disabled={!keyed.length}
            onClick={() => Promise.all(keyed.map((p) => api(`/providers/${p.id}`, 'PATCH', { api_key: '' }))).then(() => { reloadProviders(); toast(t('toast.keysForgotten'), {}, 3000) })}>
            {t('da.forgetKeys', { n: keyed.length })}
          </K.Button>
        </K.SettingsRow>
        <K.SettingsRow title={t('da.delete')} description={t('da.deleteSub')}><K.Button size="sm" variant="danger" onClick={() => setDeleting(true)}>{t('da.deleteBtn')}</K.Button></K.SettingsRow>
      </K.SettingsSection>
      {deleting && <DeleteSomething onClose={() => setDeleting(false)} onExport={exportAll} />}
      {backing && <Backups list={list ?? []} onClose={() => setBacking(false)} onChange={reloadList} />}
    </>
  )
}

type Backup = { name: string; bytes: number; at: string }
const size = bytes

/** K12: copies of the library, how often and how many, and restoring one. */
function Backups({ list, onClose, onChange }: { list: Backup[]; onClose: () => void; onChange: () => void }) {
  const [prefs] = usePrefs()
  const [busy, setBusy] = useState(false)
  const [restoring, setRestoring] = useState<Backup>()
  const every: [string, 'bk.daily' | 'bk.weekly' | 'bk.never'][] = [['daily', 'bk.daily'], ['weekly', 'bk.weekly'], ['never', 'bk.never']]
  const keep: [string, 'bk.keep7' | 'bk.keep30' | 'bk.keepAll'][] = [['7', 'bk.keep7'], ['30', 'bk.keep30'], ['all', 'bk.keepAll']]
  const pick = (opts: [string, Key][], key: string, fallback: string) => (
    <K.Select label="" options={opts.map(([, l]) => t(l))} value={t(opts.find(([v]) => v === String(prefs[key] ?? fallback))![1])}
      onChange={(v) => setPref(key, opts.find(([, l]) => t(l) === v)?.[0] ?? fallback)} />
  )
  const now = async () => {
    setBusy(true)
    try { await api('/backups', 'POST'); onChange(); toast(t('toast.backedUp'), {}, 3000) } finally { setBusy(false) }
  }
  const restore = async (b: Backup) => {
    await api(`/backups/${encodeURIComponent(b.name)}/restore`, 'POST')
    if (window.kataki?.restart) window.kataki.restart()
    else { setRestoring(undefined); toast(t('toast.restartToFinish'), {}, 10000) }
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="shield" size="lg" title={t('bk.title')} description={t('bk.body')} onClose={onClose}
        note={t('bk.total', { n: list.length, size: size(list.reduce((n, b) => n + b.bytes, 0)) })}
        actions={[<K.Button key="d" variant="primary" onClick={onClose}>{t('bk.done')}</K.Button>]}>
        <K.KeyValue label={t('bk.where')}>{t('bk.whereValue')}</K.KeyValue>
        <div className="np-pair">
          <K.Segmented label={t('bk.every')} size="sm" options={every.map(([, l]) => t(l))} value={t(every.find(([v]) => v === String(prefs['backups.every'] ?? 'daily'))![1])}
            onChange={(v) => setPref('backups.every', every.find(([, l]) => t(l) === v)?.[0] ?? 'daily')} />
          <K.Field label={t('bk.keep')}>{pick(keep, 'backups.keep', '7')}</K.Field>
        </div>
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <b style={{ fontSize: 13.5 }}>{t('bk.here')}</b>
          <K.Button size="sm" variant="ghost" icon="refresh" loading={busy} onClick={now}>{t('bk.now')}</K.Button>
        </div>
        {list.length > 0 && (
          <K.Panel flush>
            {list.map((b) => (
              <div key={b.name} className="ch-row" style={{ padding: '10px 14px' }}>
                <span style={{ flex: 1 }} className="t-body">{new Date(b.at).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })}</span>
                <span className="t-meta">{size(b.bytes)}</span>
                <K.Button size="sm" variant={restoring === b ? 'primary' : 'ghost'} onClick={() => (restoring === b ? restore(b) : setRestoring(b))}>{t(restoring === b ? 'bk.go' : 'bk.restore')}</K.Button>
              </div>
            ))}
          </K.Panel>
        )}
        <K.Callout tone="warm" icon="refresh" title={t('bk.sure')}>{t('bk.sureBody')}</K.Callout>
      </K.Dialog>
    </Overlay>
  )
}

/** K13: one thing goes to its own page's delete; everything is wiped here, models and keys kept. */
function DeleteSomething({ onClose, onExport }: { onClose: () => void; onExport: () => void }) {
  const navigate = useNavigate()
  const { items, reload } = useLibrary()
  const [stories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [what, setWhat] = useState('story')
  const [typed, setTyped] = useState('')
  const [busy, setBusy] = useState(false)
  const count = (k: Item['kind']) => items.filter((i) => i.kind === k).length
  const ok = typed.trim() === t('ds.phrase')
  const next = () => {
    onClose()
    if (what === 'story') navigate('/stories')
    else if (what === 'character') navigate('/characters')
    else navigate('/you')
  }
  const wipe = async () => {
    setBusy(true)
    for (const s of stories ?? []) await api(`/stories/${s.id}`, 'DELETE')
    for (const i of items) await api(`/library/${i.id}`, 'DELETE')
    reload()
    onClose()
    navigate('/welcome', { replace: true })
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="trash" tone="bad" title={t('ds.title')} description={t('ds.desc')} note={what === 'everything' ? t('ds.restarts') : undefined} onClose={onClose}
        actions={what === 'everything' ? [
          <K.Button key="k" variant="ghost" onClick={onClose}>{t('ds.keep')}</K.Button>,
          <K.Button key="e" variant="secondary" icon="download" onClick={onExport}>{t('ds.exportFirst')}</K.Button>,
          <K.Button key="d" variant="danger" disabled={!ok} loading={busy} onClick={wipe}>{t('ds.go')}</K.Button>,
        ] : [<K.Button key="k" variant="ghost" onClick={onClose}>{t('ds.keep')}</K.Button>, <K.Button key="n" variant="primary" onClick={next}>{t('ds.next')}</K.Button>]}>
        <K.RadioGroup label={t('ds.what')} value={what} onChange={setWhat} options={[
          { value: 'story', label: t('ds.story') }, { value: 'character', label: t('ds.character') }, { value: 'persona', label: t('ds.persona') },
          { value: 'everything', label: t('ds.everything'), description: t('ds.everythingSub') },
        ]} />
        {what === 'everything' && (
          <>
            <K.Callout tone="bad" title={t('ds.all')}>
              {t('ds.allBody', { stories: stories?.length ?? 0, characters: count('character'), places: count('place') })} {t('ds.noCopy')}
            </K.Callout>
            <K.TextField label={t('ds.type')} value={typed} onChange={setTyped} error={typed && !ok && typed.length >= t('ds.phrase').length ? t('ds.mismatch') : undefined} />
          </>
        )}
      </K.Dialog>
    </Overlay>
  )
}
