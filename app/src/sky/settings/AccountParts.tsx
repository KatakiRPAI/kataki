// Settings › Account, the parts about getting in (docs/specs/2026-10-02-kataki-online.md G5):
// the email, the password, the other services linked, and every place the account is signed in.
import { useState } from 'react'
import { api } from '../../api'
import { K } from '../../ds'
import { useLoad } from '../../hooks'
import { addPasskey, auth, passkeysWork, signOut, stale, thisSession, type AuthError, type Me } from '../../online/session'
import { Overlay, toast } from '../../overlay'
import { relative, t } from '../../strings'

const NAMES: Record<string, string> = { google: 'Google', github: 'GitHub', discord: 'Discord', apple: 'Apple' }
type Linked = { providerId: string }

/** How the account can be entered; `credential` among them means it has a password. */
export const useLinked = () => useLoad(() => auth<Linked[]>('/list-accounts', 'get'), [])

export function SigningIn({ me }: { me: Me }) {
  const [linked, reload] = useLinked()
  const [offered] = useLoad(() => fetch('/api/providers').then((r) => r.json()).then((p: { social: string[] }) => p.social, () => [] as string[]), [])
  const [changing, setChanging] = useState<'email' | 'password' | 'backup' | 'username'>()
  const [username, setUsername] = useState(me.username ?? '')
  const [mine, reloadMine] = useLoad(() => api<{ backupEmail: string | null; backupEmailVerified: boolean }>('/api/me'), [])
  const dropBackup = () => api('/api/account/backup-email', 'DELETE').then(reloadMine, () => toast(t('am.e.other'), { icon: 'alert' }, 6000))
  const has = (provider: string) => !!linked?.some((a) => a.providerId === provider)
  const link = (provider: string) => auth<{ url: string }>('/link-social', { provider, callbackURL: location.href }).then((r) => location.assign(r.url), () => toast(t('am.e.other'), { icon: 'alert' }, 6000))
  const unlink = (providerId: string) => auth('/unlink-account', { providerId }).then(reload, () => toast(t('am.e.unlink'), { icon: 'alert' }, 8000))
  return (
    <K.SettingsSection title={t('am.title')}>
      <K.SettingsRow title={t('am.username')} description={username ? t('am.usernameIs', { name: username }) : t('am.usernameNone')}>
        <K.Button size="sm" onClick={() => setChanging('username')}>{t(username ? 'am.change' : 'am.add')}</K.Button>
      </K.SettingsRow>
      <K.SettingsRow title={t('am.email')} description={me.email}><K.Button size="sm" onClick={() => setChanging('email')}>{t('am.change')}</K.Button></K.SettingsRow>
      <K.SettingsRow title={t('am.backup')} description={mine?.backupEmail ? t(mine.backupEmailVerified ? 'am.backupOn' : 'am.backupWaiting', { email: mine.backupEmail }) : t('am.backupNone')}>
        <div className="row" style={{ gap: 8 }}>
          <K.Button size="sm" onClick={() => setChanging('backup')}>{t(mine?.backupEmail ? 'am.change' : 'am.add')}</K.Button>
          {mine?.backupEmail && <K.Button size="sm" variant="ghost" onClick={dropBackup}>{t('ep.remove')}</K.Button>}
        </div>
      </K.SettingsRow>
      <K.SettingsRow title={t('am.password')} description={t(has('credential') ? 'am.passwordSet' : 'am.passwordNone')}>
        <K.Button size="sm" disabled={!has('credential')} onClick={() => setChanging('password')}>{t('am.change')}</K.Button>
      </K.SettingsRow>
      {(offered ?? []).map((p) => (
        <K.SettingsRow key={p} title={t('am.with', { name: NAMES[p] ?? p })} description={t('am.withSub', { name: NAMES[p] ?? p })}>
          {has(p) ? (
            <div className="row" style={{ gap: 8 }}>
              <K.StatePill tone="ok" icon="check">{t('am.linked')}</K.StatePill>
              <K.Button size="sm" variant="ghost" onClick={() => unlink(p)}>{t('am.unlink')}</K.Button>
            </div>
          ) : <K.Button size="sm" icon="link" onClick={() => link(p)}>{t('am.link')}</K.Button>}
        </K.SettingsRow>
      ))}
      {changing && <Change what={changing} onClose={() => { setChanging(undefined); reloadMine() }} onName={(n) => { setUsername(n); me.username = n }} />}
    </K.SettingsSection>
  )
}

function Change({ what, onClose, onName }: { what: 'email' | 'password' | 'backup' | 'username'; onClose: () => void; onName: (name: string) => void }) {
  const [first, setFirst] = useState('') // the new email, or the current password
  const [next, setNext] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const email = what === 'email' || what === 'backup' // an address is asked for
  const backup = what === 'backup'
  const naming = what === 'username'
  const wanted = first.trim().toLowerCase()
  const go = async () => {
    setBusy(true)
    setError('')
    try {
      if (naming) { await auth('/update-user', { username: wanted }); onName(wanted) }
      else if (backup) await api('/api/account/backup-email', 'POST', { email: first.trim() })
      else if (email) await auth('/change-email', { newEmail: first.trim(), callbackURL: location.pathname })
      else await auth('/change-password', { currentPassword: first, newPassword: next, revokeOtherSessions: true })
      toast(naming ? t('am.usernameDone', { name: wanted }) : backup ? t('am.backupSent', { email: first.trim() }) : email ? t('am.emailSent', { email: first.trim() }) : t('am.passwordDone'), { icon: 'shield' }, 8000)
      onClose()
    } catch (x) {
      const code = (x as AuthError).code
      setError(t(code === 'PASSWORD_COMPROMISED' ? 'si.e.breached' : code === 'PASSWORD_TOO_SHORT' ? 'si.e.short' : code === 'USERNAME_IS_ALREADY_TAKEN' ? 'am.e.taken' : naming ? 'am.e.name' : 'am.e.other'))
    } finally {
      setBusy(false)
    }
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog size="sm" icon="key" title={t(naming ? 'am.usernameTitle' : backup ? 'am.backupTitle' : email ? 'am.emailTitle' : 'am.passwordTitle')} description={t(naming ? 'am.usernameBody' : backup ? 'am.backupBody' : email ? 'am.emailBody' : 'am.passwordBody')} onClose={onClose}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>,
          <K.Button key="g" variant="primary" loading={busy} disabled={naming ? !/^[a-z0-9_]{3,30}$/.test(wanted) : email ? !first.includes('@') : !first || next.length < 12} onClick={go}>{t(naming ? 'ep.save' : backup ? 'am.backupGo' : email ? 'am.emailGo' : 'am.passwordGo')}</K.Button>]}>
        {naming ? <K.TextField label={t('am.username')} value={first} onChange={setFirst} max={30} hint={t('am.usernameHint')} /> : email ? <K.TextField label={t(backup ? 'am.backup' : 'am.newEmail')} type="email" value={first} onChange={setFirst} /> : (
          <>
            <K.TextField label={t('am.current')} type="password" value={first} onChange={setFirst} />
            <K.TextField label={t('si.newPassword')} type="password" value={next} onChange={setNext} hint={t('si.passwordHint')} />
          </>
        )}
        {error && <K.Callout tone="bad">{error}</K.Callout>}
      </K.Dialog>
    </Overlay>
  )
}

type Place = { token: string; userAgent?: string | null; createdAt: string }
/** "Chrome on Windows", from what the browser said it was. */
function device(agent?: string | null): string {
  const browser = /Firefox|Edg|OPR|Chrome|Safari/.exec(agent ?? '')?.[0].replace('Edg', 'Edge').replace('OPR', 'Opera')
  const system = /Windows|Android|iPhone|iPad|Mac OS X|Linux/.exec(agent ?? '')?.[0].replace('Mac OS X', 'macOS')
  return browser && system ? `${browser} · ${system}` : browser ?? system ?? t('se.unknown')
}

type Passkey = { id: string; name?: string | null; createdAt: string }

/** Passkeys: sign in with the device itself (a fingerprint, a face, its PIN). */
export function Passkeys() {
  const [keys, reload] = useLoad(() => auth<Passkey[]>('/passkey/list-user-passkeys', 'get'), [])
  const [busy, setBusy] = useState(false)
  if (!passkeysWork()) return null
  const add = async () => {
    setBusy(true)
    try {
      await addPasskey(device(navigator.userAgent))
      reload()
      toast(t('pk.added'), { icon: 'key' }, 6000)
    } catch (x) {
      if (stale(x)) toast(t('am.fresh'), { icon: 'shield', action: t('ac.signOut'), onAction: signOut }, 20_000)
      else if ((x as Error).name !== 'NotAllowedError') toast(t('pk.e'), { icon: 'alert' }, 8000) // NotAllowed: they cancelled
    } finally {
      setBusy(false)
    }
  }
  return (
    <K.SettingsSection title={t('pk.title')} note={t('pk.note')}>
      {(keys ?? []).map((k) => (
        <K.SettingsRow key={k.id} title={k.name || t('pk.one')} description={t('pk.since', { when: relative(Date.parse(k.createdAt)) })}>
          <K.Button size="sm" variant="ghost" onClick={() => auth('/passkey/delete-passkey', { id: k.id }).then(reload, () => {})}>{t('ep.remove')}</K.Button>
        </K.SettingsRow>
      ))}
      <K.SettingsRow title={t('pk.add')} description={t('pk.addSub')}><K.Button size="sm" icon="key" loading={busy} onClick={add}>{t('pk.addBtn')}</K.Button></K.SettingsRow>
    </K.SettingsSection>
  )
}

type Device = { id: string; name: string; createdAt: string; lastUsedAt: string | null }

/** Computers linked to this account for cloud save (the desktop app's Settings › Data). */
export function Devices() {
  const [list, reload] = useLoad(() => api<Device[]>('/api/devices').catch(() => [] as Device[]), [])
  if (!list?.length) return null
  return (
    <K.SettingsSection title={t('dv.title')} note={t('dv.note')}>
      {list.map((d) => (
        <K.SettingsRow key={d.id} title={d.name} description={d.lastUsedAt ? t('dv.used', { when: relative(Date.parse(d.lastUsedAt)) }) : t('dv.never')}>
          <K.Button size="sm" variant="ghost" onClick={() => api(`/api/devices/${d.id}`, 'DELETE').then(reload, () => {})}>{t('ep.remove')}</K.Button>
        </K.SettingsRow>
      ))}
    </K.SettingsSection>
  )
}

export function Sessions() {
  const [places, reload] = useLoad(() => auth<Place[]>('/list-sessions', 'get'), [])
  const here = thisSession()
  const out = (token: string) => auth('/revoke-session', { token }).then(reload, () => {})
  const others = (places ?? []).filter((p) => p.token !== here)
  return (
    <K.SettingsSection title={t('se.title')} note={t('se.note')}>
      {(places ?? []).map((p) => (
        <K.SettingsRow key={p.token} title={device(p.userAgent)} description={t('se.since', { when: relative(Date.parse(p.createdAt)) })}>
          {p.token === here ? <K.StatePill tone="ok" icon="check">{t('se.here')}</K.StatePill> : <K.Button size="sm" variant="ghost" onClick={() => out(p.token)}>{t('se.out')}</K.Button>}
        </K.SettingsRow>
      ))}
      {others.length > 0 && (
        <div><K.Button size="sm" onClick={() => auth('/revoke-other-sessions').then(() => { reload(); toast(t('se.othersDone'), { icon: 'shield' }, 5000) })}>{t('se.others')}</K.Button></div>
      )}
    </K.SettingsSection>
  )
}
