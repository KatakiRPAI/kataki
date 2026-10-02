// Signing in to Kataki online (design-brief-3 S1–S2, as amended by the profiles spec: passwords
// are in). Shown instead of the app while nobody is signed in; signing in reloads into the app,
// at the address the person was on.
import { useState, type FormEvent } from 'react'
import { K } from '../ds'
import { auth, type AuthError } from './session'
import { t, type Key } from '../strings'

const home = import.meta.env.BASE_URL // where a mailed link comes back to: the app

// what the gateway can say, in our words; anything else reads as "try again"
const SAID: Record<string, Key> = {
  INVALID_EMAIL_OR_PASSWORD: 'si.e.wrong', INVALID_EMAIL: 'si.e.email', PASSWORD_TOO_SHORT: 'si.e.short', PASSWORD_TOO_LONG: 'si.e.long',
  PASSWORD_COMPROMISED: 'si.e.breached', TOO_MANY_REQUESTS: 'si.e.slow', ADULTS_ONLY: 'si.e.adult',
}

export default function SignIn() {
  const [mode, setMode] = useState<'in' | 'up'>('in')
  const [sent, setSent] = useState(false) // S2: check your email
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [adult, setAdult] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e?: FormEvent) => {
    e?.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (mode === 'up') {
        await auth('/sign-up/email', { name: name.trim(), email: email.trim(), password, adult, callbackURL: home })
        setSent(true)
      } else {
        await auth('/sign-in/email', { email: email.trim(), password, callbackURL: home })
        location.reload()
      }
    } catch (x) {
      const said = x as AuthError
      if (said.code === 'EMAIL_NOT_VERIFIED') setSent(true) // the gateway mails the link again
      else setError(t(SAID[said.code ?? ''] ?? 'si.e.other'))
    } finally {
      setBusy(false)
    }
  }
  const again = () => auth('/send-verification-email', { email: email.trim(), callbackURL: home }).catch(() => {})
  const ready = email.includes('@') && password.length > 0 && (mode === 'in' || (name.trim() && adult && password.length >= 12))

  return (
    <div data-theme="night" className="si">
      <div className="si__sky"><K.Sky /></div>
      <main className="card si__card" aria-label={t('si.title')}>
        <span className="ab-mark">K</span>
        {sent ? (
          <>
            <h1 className="si__title">{t('si.sentTitle')}</h1>
            <p className="t-body">{t('si.sentBody', { email: email.trim() })}</p>
            <div className="row" style={{ gap: 10 }}>
              <K.Button size="sm" onClick={again}>{t('si.resend')}</K.Button>
              <K.Button size="sm" variant="ghost" onClick={() => { setSent(false); setMode('in') }}>{t('si.back')}</K.Button>
            </div>
          </>
        ) : (
          <form className="col" style={{ gap: 16 }} onSubmit={submit}>
            <h1 className="si__title">{t(mode === 'in' ? 'si.title' : 'si.upTitle')}</h1>
            <K.Segmented label={t('si.title')} options={[t('si.in'), t('si.up')]} value={t(mode === 'in' ? 'si.in' : 'si.up')} onChange={(v) => { setMode(v === t('si.in') ? 'in' : 'up'); setError('') }} />
            {mode === 'up' && <K.TextField label={t('si.name')} value={name} onChange={setName} max={40} />}
            <K.TextField label={t('si.email')} type="email" value={email} onChange={setEmail} />
            <K.TextField label={t('si.password')} type="password" value={password} onChange={setPassword} hint={mode === 'up' ? t('si.passwordHint') : undefined} />
            {mode === 'up' && <K.Checkbox label={t('si.adult')} checked={adult} onChange={setAdult} />}
            {error && <K.Callout tone="bad">{error}</K.Callout>}
            {/* a real submit button too, so Enter in a field signs in */}
            <button type="submit" hidden disabled={!ready || busy} />
            <K.Button variant="primary" full loading={busy} disabled={!ready} onClick={() => submit()}>{t(mode === 'in' ? 'si.in' : 'si.up')}</K.Button>
          </form>
        )}
      </main>
    </div>
  )
}
