// An account that asked to be deleted, signed in again before its day: it can stay, or go on
// leaving (docs/specs/2026-10-02-kataki-online.md G5). Shown instead of the app.
import { useState } from 'react'
import { K } from '../ds'
import { signOut, type Me } from './session'
import { t } from '../strings'

export default function Deleting({ me }: { me: Me }) {
  const [busy, setBusy] = useState(false)
  const stay = async () => {
    setBusy(true)
    await fetch('/api/account/keep', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    location.reload()
  }
  return (
    <div data-theme="night" className="si">
      <div className="si__sky"><K.Sky /></div>
      <main className="card si__card" aria-label={t('lv.goingTitle')}>
        <span className="ab-mark">K</span>
        <h1 className="si__title">{t('lv.goingTitle')}</h1>
        <p className="t-body">{t('lv.goingBody', { name: me.name, date: new Date(me.deleteAt!).toLocaleDateString(undefined, { dateStyle: 'long' }) })}</p>
        <K.Button variant="primary" full loading={busy} onClick={stay}>{t('lv.stay')}</K.Button>
        <K.Button variant="ghost" full onClick={signOut}>{t('lv.go')}</K.Button>
      </main>
    </div>
  )
}
