// Settings › Account, the way out (docs/specs/2026-10-02-kataki-online.md G5): take what the
// service holds about you, and delete the account (fourteen days to change your mind).
import { useState } from 'react'
import { api, download } from '../../api'
import { K } from '../../ds'
import { signOut } from '../../online/session'
import { Overlay } from '../../overlay'
import { t } from '../../strings'

export default function Leaving() {
  const [deleting, setDeleting] = useState(false)
  return (
    <K.SettingsSection title={t('lv.title')}>
      <K.SettingsRow title={t('lv.export')} description={t('lv.exportSub')}>
        <div className="row" style={{ gap: 8 }}>
          <K.Button size="sm" icon="download" onClick={() => download('/api/account/export')}>{t('lv.exportBtn')}</K.Button>
          <K.Button size="sm" variant="ghost" href="/settings/data">{t('lv.library')}</K.Button>
        </div>
      </K.SettingsRow>
      <K.SettingsRow title={t('lv.delete')} description={t('lv.deleteSub')}><K.Button size="sm" variant="danger" onClick={() => setDeleting(true)}>{t('lv.deleteBtn')}</K.Button></K.SettingsRow>
      {deleting && <Delete onClose={() => setDeleting(false)} />}
    </K.SettingsSection>
  )
}

function Delete({ onClose }: { onClose: () => void }) {
  const [typed, setTyped] = useState('')
  const [busy, setBusy] = useState(false)
  const [stale, setStale] = useState(false) // signed in too long ago to do this
  const [error, setError] = useState('')
  const ok = typed.trim() === t('lv.phrase')
  const go = async () => {
    setBusy(true)
    try {
      await api('/api/account/delete', 'POST', {})
      location.reload() // signed out everywhere, this browser too
    } catch (e) {
      if ((e as { detail?: { code?: string } }).detail?.code === 'FRESH') setStale(true)
      else setError(t('am.e.other'))
      setBusy(false)
    }
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="trash" tone="bad" title={t('lv.deleteTitle')} description={t('lv.deleteBody')} onClose={onClose}
        actions={stale ? [
          <K.Button key="k" variant="ghost" onClick={onClose}>{t('lv.keep')}</K.Button>,
          <K.Button key="o" variant="primary" onClick={signOut}>{t('ac.signOut')}</K.Button>,
        ] : [
          <K.Button key="k" variant="ghost" onClick={onClose}>{t('lv.keep')}</K.Button>,
          <K.Button key="d" variant="danger" disabled={!ok} loading={busy} onClick={go}>{t('lv.deleteGo')}</K.Button>,
        ]}>
        {stale ? <K.Callout tone="warm" title={t('lv.staleTitle')}>{t('lv.stale')}</K.Callout> : (
          <>
            <K.Callout tone="bad" title={t('lv.what')}>{t('lv.whatBody')}</K.Callout>
            <K.TextField label={t('lv.type', { phrase: t('lv.phrase') })} value={typed} onChange={setTyped} />
          </>
        )}
        {error && <K.Callout tone="bad">{error}</K.Callout>}
      </K.Dialog>
    </Overlay>
  )
}
