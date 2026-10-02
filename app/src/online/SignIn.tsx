// Signing in to Kataki online (design-brief-3 S1–S3, as amended by the profiles spec: passwords
// are in). Shown instead of the app while nobody is signed in; signing in reloads into the app,
// at the address the person was on. A mailed link (reset, sign-in) lands here with its token.
import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { K } from '../ds'
import { auth, passkeySignIn, passkeysWork, type AuthError } from './session'
import { t, type Key } from '../strings'

const home = import.meta.env.BASE_URL // where a mailed link comes back to: the app

// what the gateway can say, in our words; anything else reads as "try again"
const SAID: Record<string, Key> = {
  INVALID_EMAIL_OR_PASSWORD: 'si.e.wrong', INVALID_USERNAME_OR_PASSWORD: 'si.e.wrong', INVALID_EMAIL: 'si.e.email', PASSWORD_TOO_SHORT: 'si.e.short', PASSWORD_TOO_LONG: 'si.e.long',
  PASSWORD_COMPROMISED: 'si.e.breached', TOO_MANY_REQUESTS: 'si.e.slow', ADULTS_ONLY: 'si.e.adult', INVALID_TOKEN: 'si.e.link',
  INVALID_CODE: 'si.e.code', INVALID_BACKUP_CODE: 'si.e.code', INVALID_TWO_FACTOR_COOKIE: 'si.e.codeLate', TOO_MANY_ATTEMPTS_REQUEST_NEW_CODE: 'si.e.codeLate',
}
const NAMES: Record<string, string> = { google: 'Google', github: 'GitHub', discord: 'Discord', apple: 'Apple' }
type View = 'in' | 'up' | 'forgot' | 'link' | 'reset' | 'magic' | 'code'

export default function SignIn() {
  const [asked] = useState(() => new URLSearchParams(location.search))
  // what a redirect back to us said went wrong, if anything
  const [came] = useState(() => {
    const code = asked.get('error')
    if (code) history.replaceState(null, '', location.pathname) // said once: not again on a reload
    return code
  })
  // another service signed someone in who has no account here: straight to making one
  // step=2: a sign-in link or another service signed in an account with two-step sign-in on
  const [view, setView] = useState<View>(() => {
    if (asked.get('step') === '2') { history.replaceState(null, '', location.pathname); return 'code' }
    return asked.get('magic') ? 'magic' : asked.get('token') ? 'reset' : came === 'signup_disabled' ? 'up' : 'in'
  })
  const [code, setCode] = useState('')
  const [backup, setBackup] = useState(false) // a backup code instead of the app's
  const [trust, setTrust] = useState(false)
  const [sent, setSent] = useState<Key>() // S2: what "check your email" says
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [adult, setAdult] = useState(false)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState(came === 'signup_disabled' ? t('si.noAccount') : '')
  // S3: a link that is used up or too old; anything else that went wrong on the way back says its code
  const [error, setError] = useState(!came || came === 'signup_disabled' ? '' : /token|attempt/i.test(came) ? t('si.e.link') : t('si.e.back', { code: came }))
  const [social, setSocial] = useState<string[]>([])
  useEffect(() => { fetch('/api/providers').then((r) => r.json()).then((p: { social: string[] }) => setSocial(p.social), () => {}) }, [])
  // Leave for the other service. Creating an account carries "18 or older" with it; signing in never creates one.
  const leave = (provider: string) => {
    if (view === 'up' && !adult) return setError(t('si.e.tick')) // say what is missing, rather than a dead button
    auth<{ url: string }>('/sign-in/social', { provider, callbackURL: home, errorCallbackURL: home, ...(view === 'up' ? { requestSignUp: true, additionalData: { adult: true } } : {}) })
      .then((r) => location.assign(r.url), () => setError(t('si.e.other')))
  }

  const go = (to: View) => { setView(to); setError(''); setNote(''); setSent(undefined) }
  const mail = email.trim()
  const acts: Record<View, () => Promise<void>> = {
    in: async () => {
      // an "@" means an email; anything else is a username
      const r = await auth<{ twoFactorRedirect?: boolean }>(mail.includes('@') ? '/sign-in/email' : '/sign-in/username', mail.includes('@') ? { email: mail, password, callbackURL: home } : { username: mail, password })
      if (r?.twoFactorRedirect) return go('code') // the password was right; now the second step
      location.reload()
    },
    code: async () => {
      await auth(backup ? '/two-factor/verify-backup-code' : '/two-factor/verify-totp', { code: code.trim(), trustDevice: trust })
      location.assign(location.pathname)
    },
    up: async () => { await auth('/sign-up/email', { name: name.trim(), email: mail, password, adult, callbackURL: home }); setSent('si.sentBody') },
    forgot: async () => { await auth('/request-password-reset', { email: mail, redirectTo: home }); setSent('si.forgotSent') },
    link: async () => { await auth('/sign-in/magic-link', { email: mail, callbackURL: home }); setSent('si.linkSent') },
    reset: async () => {
      await auth('/reset-password', { newPassword: password, token: asked.get('token') })
      history.replaceState(null, '', location.pathname) // the token is spent: off the address bar
      setPassword('')
      go('in')
      setNote(t('si.resetDone'))
    },
    // the button, not the mail's link, makes the request that uses the token up
    magic: async () => location.assign(`/api/auth/magic-link/verify?token=${encodeURIComponent(asked.get('magic')!)}&callbackURL=${encodeURIComponent(home)}`),
  }
  const submit = async (e?: FormEvent) => {
    e?.preventDefault()
    setBusy(true)
    setError('')
    try {
      await acts[view]()
    } catch (x) {
      const said = x as AuthError
      if (said.code === 'EMAIL_NOT_VERIFIED') setSent('si.sentBody') // the gateway mails the link again
      else setError(t(SAID[said.code ?? ''] ?? 'si.e.other'))
    } finally {
      setBusy(false)
    }
  }
  const again = () => auth('/send-verification-email', { email: mail, callbackURL: home }).catch(() => {})
  const ready = {
    in: mail.length >= 3 && password.length > 0,
    up: mail.includes('@') && !!name.trim() && adult && password.length >= 12,
    forgot: mail.includes('@'), link: mail.includes('@'), reset: password.length >= 12, magic: true, code: code.trim().length >= 6,
  }[view]
  const title: Record<View, Key> = { in: 'si.title', up: 'si.upTitle', forgot: 'si.forgotTitle', link: 'si.linkTitle', reset: 'si.resetTitle', magic: 'si.magicTitle', code: 'si.codeTitle' }
  const action: Record<View, Key> = { in: 'si.in', up: 'si.up', forgot: 'si.forgotGo', link: 'si.linkGo', reset: 'si.resetGo', magic: 'si.in', code: 'si.in' }
  const link = (to: View, label: Key): ReactNode => <K.Button size="sm" variant="link" onClick={() => go(to)}>{t(label)}</K.Button>

  return (
    <div data-theme="night" className="si">
      <div className="si__sky"><K.Sky /></div>
      <main className="card si__card" aria-label={t('si.title')}>
        <span className="ab-mark">K</span>
        {sent ? (
          <>
            <h1 className="si__title">{t('si.sentTitle')}</h1>
            <p className="t-body">{t(sent, { email: mail })}</p>
            <div className="row" style={{ gap: 10 }}>
              {sent === 'si.sentBody' && <K.Button size="sm" onClick={again}>{t('si.resend')}</K.Button>}
              <K.Button size="sm" variant="ghost" onClick={() => go('in')}>{t('si.back')}</K.Button>
            </div>
          </>
        ) : (
          <form className="col" style={{ gap: 16 }} onSubmit={submit}>
            <h1 className="si__title">{t(title[view])}</h1>
            {(view === 'in' || view === 'up') && <K.Segmented label={t('si.title')} options={[t('si.in'), t('si.up')]} value={t(view === 'in' ? 'si.in' : 'si.up')} onChange={(v) => go(v === t('si.in') ? 'in' : 'up')} />}
            {view === 'forgot' && <p className="t-body">{t('si.forgotBody')}</p>}
            {view === 'link' && <p className="t-body">{t('si.linkBody')}</p>}
            {view === 'magic' && <p className="t-body">{t('si.magicBody')}</p>}
            {view === 'code' && (
              <>
                <p className="t-body">{t(backup ? 'si.backupBody' : 'si.codeBody')}</p>
                <K.TextField label={t(backup ? 'si.backupCode' : 'si.code')} value={code} onChange={setCode} max={backup ? 16 : 6} />
                <K.Checkbox label={t('si.trust')} checked={trust} onChange={setTrust} />
              </>
            )}
            {view === 'up' && <K.TextField label={t('si.name')} value={name} onChange={setName} max={40} />}
            {view !== 'reset' && view !== 'magic' && view !== 'code' && <K.TextField label={t(view === 'in' ? 'si.emailOrName' : 'si.email')} type={view === 'in' ? 'text' : 'email'} value={email} onChange={setEmail} />}
            {(view === 'in' || view === 'up' || view === 'reset') && (
              <K.TextField label={t(view === 'reset' ? 'si.newPassword' : 'si.password')} type="password" value={password} onChange={setPassword} hint={view === 'in' ? undefined : t('si.passwordHint')} />
            )}
            {view === 'up' && <K.Checkbox label={t('si.adult')} checked={adult} onChange={(v) => { setAdult(v); setError('') }} />}
            {note && <K.Callout tone="ok">{note}</K.Callout>}
            {error && <K.Callout tone="bad">{error}</K.Callout>}
            {/* a real submit button too, so Enter in a field signs in */}
            <button type="submit" hidden disabled={!ready || busy} />
            <K.Button variant="primary" full loading={busy} disabled={!ready} onClick={() => submit()}>{t(action[view])}</K.Button>
            {view === 'in' && <div className="row" style={{ justifyContent: 'space-between' }}>{link('forgot', 'si.forgot')}{link('link', 'si.linkInstead')}</div>}
            {view === 'in' && passkeysWork() && (
              <K.Button full icon="key" onClick={() => passkeySignIn().then(() => location.reload(), (x) => { if ((x as Error).name !== 'NotAllowedError') setError(t('si.e.passkey')) })}>{t('si.passkey')}</K.Button>
            )}
            {(view === 'in' || view === 'up') && social.map((p) => (
              <K.Button key={p} full onClick={() => leave(p)}>{t(view === 'in' ? 'si.with' : 'si.upWith', { name: NAMES[p] ?? p })}</K.Button>
            ))}
            {(view === 'forgot' || view === 'link') && <div>{link('in', 'si.back')}</div>}
            {view === 'code' && (
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <K.Button size="sm" variant="link" onClick={() => { setBackup(!backup); setCode(''); setError('') }}>{t(backup ? 'si.useApp' : 'si.useBackup')}</K.Button>
                {link('in', 'si.back')}
              </div>
            )}
          </form>
        )}
      </main>
    </div>
  )
}
