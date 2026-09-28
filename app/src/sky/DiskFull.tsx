// N2: a takeover while the library can't be written; it lifts itself when a write succeeds.
import { useEffect, useState } from 'react'
import { api, type Storage } from '../api'
import { K } from '../ds'
import { err, type Code } from '../errors'
import { skyTheme, usePrefs } from '../prefs'
import { t, type Key } from '../strings'

export const bytes = (n: number) => (n > 1e9 ? `${(n / 1e9).toFixed(1)} GB` : n > 1e6 ? `${Math.round(n / 1e6)} MB` : `${Math.max(1, Math.round(n / 1e3))} KB`)

export default function DiskFull() {
  const [prefs] = usePrefs()
  const [code, setCode] = useState<Code | null>(null)
  const [left, setLeft] = useState(30)
  const [room, setRoom] = useState<Storage>()
  useEffect(() => {
    const on = (e: Event) => setCode((e as CustomEvent<Code>).detail)
    addEventListener('kataki:disk', on)
    return () => removeEventListener('kataki:disk', on)
  }, [])
  const check = () => api('/settings', 'PUT', { 'disk.checked': new Date().toISOString() }).then(() => setCode(null), () => setLeft(30))
  useEffect(() => {
    if (!code) return
    api<Storage>('/storage').then(setRoom, () => {}) // reading still works on a full disk
    const tick = setInterval(() => setLeft((s) => { if (s <= 1) { check(); return 30 } return s - 1 }), 1000)
    return () => clearInterval(tick)
  }, [code]) // eslint-disable-line react-hooks/exhaustive-deps
  if (!code) return null
  const drive = room?.drive ?? t('disk.drive')
  const e = err(code, { drive, neededMb: 50, lastSavedAt: t('disk.lastSaved'), libraryFolder: t('disk.folder') })
  const ours = room ? room.places.reduce((n, p) => n + p.bytes, 0) || 1 : 1
  const backups = room?.places.find((p) => p.what === 'backups')
  return (
    <div data-theme={skyTheme(prefs)} className="takeover" role="alertdialog" aria-modal="true" aria-label={e.title}>
      <K.Sky />
      <main className="takeover__col">
        <div className="takeover__mark">{t('app.name')}</div>
        <K.Alert title={e.title} code={e.code} icon="alert" actions={<K.Button variant="primary" icon="refresh" onClick={check}>{e.actions[0]}</K.Button>}>{e.body}</K.Alert>
        {room && (
          <div className="card" style={{ padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            <span className="sec-title" style={{ fontSize: 17 }}>{t('disk.uses', { drive })}</span>
            {room.places.map((p) => (
              <K.Meter key={p.what} label={`${t(`disk.what.${p.what}` as Key)} · ${bytes(p.bytes)}`} value={Math.max(1, Math.round((100 * p.bytes) / ours))} tone={p.bytes === Math.max(...room.places.map((x) => x.bytes)) ? 'warm' : undefined} />
            ))}
            <span className="t-meta">{t('disk.free', { drive, free: bytes(room.free), total: bytes(room.total) })}</span>
          </div>
        )}
        {!!backups?.bytes && (
          <K.Callout tone="info" title={t('disk.fewer')} action={<K.Button size="sm" href="/settings/data">{t('disk.openBackups')}</K.Button>}>{t('disk.fewerBody', { size: bytes(backups.bytes) })}</K.Callout>
        )}
        <div className="row" style={{ gap: 10 }} role="status" aria-live="polite"><K.Spinner size={14} /><span className="t-meta">{t('disk.live', { s: left })}</span></div>
      </main>
    </div>
  )
}
