// Settings › Account (Kataki online): who is signed in, what is left to spend, two-step sign-in,
// and signing out. The rest of U1 (methods, sessions, export, deletion) is G5 of
// docs/specs/2026-10-02-kataki-online.md.
import { useState } from 'react'
import { api } from '../../api'
import { K } from '../../ds'
import { useLoad } from '../../hooks'
import { account, signOut } from '../../online/session'
import { t } from '../../strings'
import { Passkeys, Sessions, SigningIn } from './AccountParts'
import Leaving from './Leaving'
import TwoStep from './TwoStep'

export default function Account() {
  const me = account()!
  const [got] = useLoad(() => api<{ balance: number }>('/api/me'), [])
  const [twoStep, setTwoStep] = useState(!!me.twoFactorEnabled)
  const [doing, setDoing] = useState<'on' | 'off' | 'codes'>()
  const dollars = got ? new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 4 }).format(got.balance / 1e6) : '…'
  return (
    <>
      <K.SettingsSection title={t('set.n.account')} note={t('ac.note')}>
        <K.SettingsRow title={me.name} description={me.email}><K.Button size="sm" onClick={signOut}>{t('ac.signOut')}</K.Button></K.SettingsRow>
        <K.SettingsRow title={t('ac.balance')} description={t('ac.balanceSub')}><b>{dollars}</b></K.SettingsRow>
      </K.SettingsSection>
      <SigningIn me={me} />
      <Passkeys />
      <K.SettingsSection title={t('ts.title')} note={t('ts.note')}>
        <K.SettingsRow title={t('ts.app')} description={t(twoStep ? 'ts.isOn' : 'ts.isOff')}>
          {twoStep ? (
            <div className="row" style={{ gap: 8 }}>
              <K.StatePill tone="ok" icon="check">{t('ts.on')}</K.StatePill>
              <K.Button size="sm" variant="ghost" onClick={() => setDoing('codes')}>{t('ts.newCodes')}</K.Button>
              <K.Button size="sm" variant="ghost" onClick={() => setDoing('off')}>{t('ts.turnOff')}</K.Button>
            </div>
          ) : <K.Button size="sm" icon="shield" onClick={() => setDoing('on')}>{t('ts.turnOn')}</K.Button>}
        </K.SettingsRow>
      </K.SettingsSection>
      <Sessions />
      <Leaving />
      {doing && <TwoStep key={doing} doing={doing} onClose={() => setDoing(undefined)} onChange={(on) => { setTwoStep(on); me.twoFactorEnabled = on }} />}
    </>
  )
}
