// N2: a takeover while the library can't be written; it lifts itself when a write succeeds.
import { useEffect, useState } from 'react'
import { api } from '../api'
import { K } from '../ds'
import { err, type Code } from '../errors'
import { t } from '../strings'

export default function DiskFull() {
  const [code, setCode] = useState<Code | null>(null)
  const [left, setLeft] = useState(30)
  useEffect(() => {
    const on = (e: Event) => setCode((e as CustomEvent<Code>).detail)
    addEventListener('kataki:disk', on)
    return () => removeEventListener('kataki:disk', on)
  }, [])
  const check = () => api('/settings', 'PUT', { 'disk.checked': new Date().toISOString() }).then(() => setCode(null), () => setLeft(30))
  useEffect(() => {
    if (!code) return
    const tick = setInterval(() => setLeft((s) => { if (s <= 1) { check(); return 30 } return s - 1 }), 1000)
    return () => clearInterval(tick)
  }, [code]) // eslint-disable-line react-hooks/exhaustive-deps
  if (!code) return null
  const e = err(code, { drive: t('disk.drive'), neededMb: 50, lastSavedAt: t('disk.lastSaved'), libraryFolder: t('disk.folder') })
  return (
    <div data-theme="night" className="takeover" role="alertdialog" aria-modal="true" aria-label={e.title}>
      <K.Alert title={e.title} code={e.code} actions={<K.Button variant="primary" onClick={check}>{e.actions[0]}</K.Button>}>{e.body}</K.Alert>
      <span className="t-meta">{t('disk.live', { s: left })}</span>
    </div>
  )
}
