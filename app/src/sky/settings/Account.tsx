// Settings › Account (Kataki online): who is signed in, what is left to spend, and signing out.
// The rest of U1 (methods, sessions, export, deletion) is G5 of docs/specs/2026-10-02-kataki-online.md.
import { api } from '../../api'
import { K } from '../../ds'
import { useLoad } from '../../hooks'
import { account, signOut } from '../../online/session'
import { t } from '../../strings'

export default function Account() {
  const me = account()!
  const [got] = useLoad(() => api<{ balance: number }>('/api/me'), [])
  const dollars = got ? new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 4 }).format(got.balance / 1e6) : '…'
  return (
    <K.SettingsSection title={t('set.n.account')} note={t('ac.note')}>
      <K.SettingsRow title={me.name} description={me.email}><K.Button size="sm" onClick={signOut}>{t('ac.signOut')}</K.Button></K.SettingsRow>
      <K.SettingsRow title={t('ac.balance')} description={t('ac.balanceSub')}><b>{dollars}</b></K.SettingsRow>
    </K.SettingsSection>
  )
}
