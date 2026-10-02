// Settings › Data › Cloud (desktop): keep a copy of this library on your Kataki online account
// (docs/specs/2026-10-02-kataki-online.md §8). The engine does the talking (cloud.py); here it
// is linked, sent up, brought down, and the person decides when the two copies disagree.
import { useEffect, useState } from 'react'
import { api } from '../../api'
import { K } from '../../ds'
import { useLoad } from '../../hooks'
import { Overlay, toast } from '../../overlay'
import { relative, t } from '../../strings'

type Holds = { stories?: number; characters?: number; places?: number; plots?: number }
type Snapshot = { revision: number; holds: Holds; device: string; at?: string }
type Status = { available: boolean; connected?: boolean; offline?: boolean; account?: string; snapshot?: Snapshot | null; base?: number; local?: Holds; free?: Holds; pricePerGbMonth?: number }
type Sent = { snapshot?: Snapshot; conflict?: Snapshot | null; too_big?: number | null; needs_credit?: { over: string[]; free: Holds } }

const holds = (h: Holds = {}) => t('cl.holds', { stories: h.stories ?? 0, characters: h.characters ?? 0, places: h.places ?? 0, plots: h.plots ?? 0 })
const when = (s: Snapshot) => (s.at ? relative(Date.parse(s.at)) : '')

export default function Cloud() {
  const [status, reload] = useLoad(() => api<Status>('/cloud').catch(() => ({ available: false }) as Status), [])
  const [linking, setLinking] = useState<{ code: string; url: string }>()
  const [clash, setClash] = useState<Snapshot | null>() // the cloud holds something this library was not built on
  const [down, setDown] = useState(false) // asking before the library is replaced
  const [busy, setBusy] = useState('')
  if (!status?.available) return null

  const said = (e: unknown) => toast((e as Error).message || t('cl.e'), { icon: 'alert' }, 8000)
  const connect = async () => {
    try {
      const made = await api<{ code: string; url: string }>('/cloud/connect', 'POST')
      setLinking(made)
      if (window.kataki?.openOnline) window.kataki.openOnline(made.url)
      else window.open(made.url, '_blank', 'noopener')
    } catch (e) { said(e) }
  }
  const upload = async (force = false) => {
    setBusy('up')
    try {
      const sent = await api<Sent>(`/cloud/upload${force ? '?force=true' : ''}`, 'POST')
      if (sent.conflict !== undefined) setClash(sent.conflict)
      else if (sent.too_big !== undefined) toast(t('cl.tooBig', { mb: Math.round((sent.too_big ?? 0) / 1048576) }), { icon: 'alert' }, 10_000)
      else if (sent.needs_credit) toast(t('cl.needsCredit'), { icon: 'alert' }, 12_000)
      else { setClash(undefined); toast(t('cl.sent'), { icon: 'cloud' }, 5000) }
      reload()
    } catch (e) { said(e) } finally { setBusy('') }
  }
  const download = async () => {
    setBusy('down')
    try {
      const got = await api<{ restart?: boolean; nothing?: boolean }>('/cloud/download', 'POST')
      if (got.nothing) return toast(t('cl.nothing'), {}, 6000)
      if (window.kataki?.restart) window.kataki.restart()
      else toast(t('toast.restartToFinish'), {}, 10_000)
    } catch (e) { said(e) } finally { setBusy(''); setDown(false); setClash(undefined) }
  }
  const snapshot = status.snapshot
  const ahead = !!snapshot && snapshot.revision !== (status.base ?? 0) // the cloud has moved on since this library last met it
  const past = Object.entries(status.free ?? {}).some(([what, most]) => (status.local?.[what as keyof Holds] ?? 0) > (most ?? 0)) // this library is past the free limit

  return (
    <K.SettingsSection title={t('cl.title')} note={t('cl.note')}>
      {!status.connected ? (
        <K.SettingsRow title={t('cl.connect')} description={t('cl.connectSub')}><K.Button size="sm" icon="cloud" onClick={connect}>{t('cl.connectBtn')}</K.Button></K.SettingsRow>
      ) : (
        <>
          <K.SettingsRow title={status.offline ? t('cl.offline') : t('cl.account', { name: status.account ?? '' })}
            description={status.offline ? t('cl.offlineSub') : snapshot ? t('cl.saved', { when: when(snapshot), device: snapshot.device, holds: holds(snapshot.holds) }) : t('cl.none')}>
            <K.Button size="sm" variant="ghost" onClick={() => api('/cloud/disconnect', 'POST').then(reload, said)}>{t('cl.disconnect')}</K.Button>
          </K.SettingsRow>
          {!status.offline && (
            <K.SettingsRow title={t('cl.here')} description={holds(status.local) + (ahead ? ` ${t('cl.ahead')}` : '')}>
              <div className="row" style={{ gap: 8 }}>
                <K.Button size="sm" icon="cloud" loading={busy === 'up'} onClick={() => upload()}>{t('cl.up')}</K.Button>
                <K.Button size="sm" variant="ghost" icon="download" disabled={!snapshot} loading={busy === 'down'} onClick={() => setDown(true)}>{t('cl.down')}</K.Button>
              </div>
            </K.SettingsRow>
          )}
        </>
      )}
      {status.connected && status.free && (
        <K.SettingsRow title={t('cl.free')} description={t('cl.freeSub', { holds: holds(status.free), price: new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(status.pricePerGbMonth ?? 0) }) + (past ? ` ${t('cl.past')}` : '')}><span /></K.SettingsRow>
      )}
      {linking && <Linking {...linking} onClose={() => { setLinking(undefined); reload() }} />}
      {clash !== undefined && (
        <Overlay onClose={() => setClash(undefined)}>
          <K.Dialog icon="cloud" tone="warm" title={t('cl.clashTitle')} onClose={() => setClash(undefined)}
            description={clash ? t('cl.clashBody', { when: when(clash), device: clash.device, holds: holds(clash.holds) }) : t('cl.clashGone')}
            actions={[
              <K.Button key="c" variant="ghost" onClick={() => setClash(undefined)}>{t('ep.cancel')}</K.Button>,
              <K.Button key="d" icon="download" disabled={!clash} onClick={() => { setClash(undefined); setDown(true) }}>{t('cl.down')}</K.Button>,
              <K.Button key="u" variant="danger" loading={busy === 'up'} onClick={() => upload(true)}>{t('cl.replace')}</K.Button>,
            ]} />
        </Overlay>
      )}
      {down && (
        <Overlay onClose={() => setDown(false)}>
          <K.Dialog icon="download" title={t('cl.downTitle')} description={t('cl.downBody')} onClose={() => setDown(false)}
            actions={[<K.Button key="c" variant="ghost" onClick={() => setDown(false)}>{t('ep.cancel')}</K.Button>,
              <K.Button key="g" variant="primary" loading={busy === 'down'} onClick={download}>{t('cl.downGo')}</K.Button>]} />
        </Overlay>
      )}
    </K.SettingsSection>
  )
}

/** The code to approve on the website, while the engine waits to be told yes. */
function Linking({ code, url, onClose }: { code: string; url: string; onClose: () => void }) {
  const [state, setState] = useState('waiting')
  useEffect(() => {
    if (state !== 'waiting') return
    const tick = setInterval(() => api<{ state: string }>('/cloud/poll', 'POST').then((r) => setState(r.state), () => {}), 2000)
    return () => clearInterval(tick)
  }, [state])
  useEffect(() => {
    if (state !== 'linked') return
    toast(t('cl.linked'), { icon: 'cloud' }, 5000)
    onClose()
  }, [state]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="cloud" title={t('cl.linkTitle')} description={t(state === 'expired' ? 'cl.linkExpired' : 'cl.linkBody')} onClose={onClose}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>]}>
        {state !== 'expired' && (
          <>
            <div className="cl-code" aria-label={t('cl.code')}>{code}</div>
            <K.KeyValue label={t('cl.where')}><code className="ts-secret">{url}</code></K.KeyValue>
            <div className="row" style={{ gap: 10 }}><K.Spinner /><span className="t-meta">{t('cl.waiting')}</span></div>
          </>
        )}
      </K.Dialog>
    </Overlay>
  )
}
