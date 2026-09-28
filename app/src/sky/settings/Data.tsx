// Data and privacy (K10, K11, K13): take it with you, bring it in, keys, delete.
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { api, download, sendFile, type Item, type Provider, type StorySummary } from '../../api'
import { K } from '../../ds'
import { useLibrary, useLoad } from '../../hooks'
import { Overlay, toast } from '../../overlay'
import { t } from '../../strings'

export default function Data() {
  const navigate = useNavigate()
  const { reload } = useLibrary()
  const [providers, reloadProviders] = useLoad(() => api<Provider[]>('/providers'), [])
  const [busy, setBusy] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const keyed = (providers ?? []).filter((p) => p.has_key)
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
      <K.Callout tone="privacy" icon="lock" title={t('da.privacy')}>{t('da.privacyBody')}</K.Callout>
      <K.SettingsSection title={t('da.take')}>
        <K.SettingsRow title={t('da.export')} description={t('da.exportSub')}><K.Button icon="download" loading={busy} onClick={exportAll}>{t('da.export')}</K.Button></K.SettingsRow>
      </K.SettingsSection>
      <K.SettingsSection title={t('da.import')}>
        <K.SettingsRow title={t('da.import')} description={t('da.importSub')}>
          <div className="row" style={{ gap: 8 }}>
            <K.Button onClick={() => navigate('/characters')}>{t('da.importCards')}</K.Button>
            <label className="k-btn k-btn--ghost">{t('da.importLibrary')}<input type="file" accept=".kataki" hidden onChange={(e) => importLibrary(e.target.files?.[0])} /></label>
          </div>
        </K.SettingsRow>
      </K.SettingsSection>
      <K.SettingsSection title={t('da.keys')}>
        <K.SettingsRow title={t('da.keys')} description={t('da.keysSub', { n: keyed.length, names: new Intl.ListFormat('en').format(keyed.map((p) => p.name)) })}>
          <K.Button variant="ghost" disabled={!keyed.length}
            onClick={() => Promise.all(keyed.map((p) => api(`/providers/${p.id}`, 'PATCH', { api_key: '' }))).then(() => { reloadProviders(); toast(t('toast.keysForgotten'), {}, 3000) })}>
            {t('da.forgetKeys')}
          </K.Button>
        </K.SettingsRow>
      </K.SettingsSection>
      <K.SettingsSection title={t('da.delete')}>
        <K.SettingsRow title={t('da.delete')} description={t('da.deleteSub')}><K.Button variant="danger" onClick={() => setDeleting(true)}>{t('da.deleteBtn')}</K.Button></K.SettingsRow>
      </K.SettingsSection>
      {deleting && <DeleteSomething onClose={() => setDeleting(false)} onExport={exportAll} />}
    </>
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
      <K.Dialog icon="trash" tone="bad" title={t('ds.title')} onClose={onClose}
        actions={what === 'everything' ? [
          <K.Button key="k" variant="ghost" onClick={onClose}>{t('ds.keep')}</K.Button>,
          <K.Button key="e" variant="secondary" icon="download" onClick={onExport}>{t('ds.exportFirst')}</K.Button>,
          <K.Button key="d" variant="danger" disabled={!ok} loading={busy} onClick={wipe}>{t('ds.go')}</K.Button>,
        ] : [<K.Button key="k" variant="ghost" onClick={onClose}>{t('ds.keep')}</K.Button>, <K.Button key="n" variant="primary" onClick={next}>{t('ds.next')}</K.Button>]}>
        <K.RadioGroup value={what} onChange={setWhat} options={[
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
