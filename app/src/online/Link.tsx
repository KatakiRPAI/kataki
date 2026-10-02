// Linking a computer to this account (docs/specs/2026-10-02-kataki-online.md §8): the desktop
// app showed a code and opened this page; the signed-in person says yes or no. Shown instead of
// the app when the address carries `?link=CODE`.
import { useEffect, useState } from 'react'
import { K } from '../ds'
import type { Me } from './session'
import { t } from '../strings'

export default function Link({ me, code }: { me: Me; code: string }) {
  const [name, setName] = useState<string | null>() // the computer asking; null: no such code waiting
  const [done, setDone] = useState(false)
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    fetch(`/api/device/link?code=${encodeURIComponent(code)}`).then((r) => (r.ok ? r.json() : null)).then((got: { name: string } | null) => setName(got?.name ?? null), () => setName(null))
  }, [code])
  const home = () => location.assign(location.pathname)
  const approve = async () => {
    setBusy(true)
    const r = await fetch('/api/device/approve', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) })
    setBusy(false)
    if (r.ok) setDone(true)
    else setName(null)
  }
  return (
    <div data-theme="night" className="si">
      <div className="si__sky"><K.Sky /></div>
      <main className="card si__card" aria-label={t('ln.title')}>
        <span className="ab-mark">K</span>
        {done ? (
          <>
            <h1 className="si__title">{t('ln.doneTitle')}</h1>
            <p className="t-body">{t('ln.doneBody')}</p>
            <K.Button full onClick={home}>{t('ln.toApp')}</K.Button>
          </>
        ) : name === null ? (
          <>
            <h1 className="si__title">{t('ln.goneTitle')}</h1>
            <p className="t-body">{t('ln.goneBody')}</p>
            <K.Button full onClick={home}>{t('ln.toApp')}</K.Button>
          </>
        ) : (
          <>
            <h1 className="si__title">{t('ln.title')}</h1>
            <p className="t-body">{t('ln.body', { computer: name ?? '…', account: me.name })}</p>
            <div className="cl-code" aria-label={t('cl.code')}>{code.toUpperCase()}</div>
            <p className="t-meta">{t('ln.check')}</p>
            <K.Button variant="primary" full loading={busy} disabled={!name} onClick={approve}>{t('ln.go')}</K.Button>
            <K.Button variant="ghost" full onClick={home}>{t('ln.no')}</K.Button>
          </>
        )}
      </main>
    </div>
  )
}
