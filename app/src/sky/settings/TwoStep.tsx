// Two-step sign-in (docs/specs/2026-10-02-kataki-online.md G4): turning it on with an
// authenticator app, the backup codes, new codes, and turning it off. Each needs the password.
import { useState } from 'react'
import { renderSVG } from 'uqr'
import { K } from '../../ds'
import { auth, signOut, stale, type AuthError } from '../../online/session'
import { Overlay, toast } from '../../overlay'
import { t } from '../../strings'

type Doing = 'on' | 'off' | 'codes'

export default function TwoStep({ doing, hasPassword, onClose, onChange }: { doing: Doing; hasPassword: boolean; onClose: () => void; onChange: (on: boolean) => void }) {
  const [password, setPassword] = useState('')
  const [setup, setSetup] = useState<{ totpURI: string; backupCodes: string[] }>() // on: the app is being paired
  const [code, setCode] = useState('')
  const [codes, setCodes] = useState<string[]>() // shown once, at the end
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [old, setOld] = useState(false) // the sign-in is too old for this: sign in again

  const run = async (what: () => Promise<void>) => {
    setBusy(true)
    setError('')
    try { await what() } catch (x) {
      if (stale(x)) setOld(true)
      else setError(t((x as AuthError).code === 'INVALID_CODE' || setup ? 'ts.e.code' : hasPassword ? 'ts.e.password' : 'am.e.other'))
    } finally { setBusy(false) }
  }
  const next = () => run(async () => {
    const said = hasPassword ? { password } : {} // an account with no password is asked for a recent sign-in instead
    if (doing === 'on' && !setup) return setSetup(await auth('/two-factor/enable', said))
    if (doing === 'on') {
      await auth('/two-factor/verify-totp', { code: code.trim() }) // on only once a code has come back
      onChange(true)
      return setCodes(setup!.backupCodes)
    }
    if (doing === 'codes') return setCodes((await auth<{ backupCodes: string[] }>('/two-factor/generate-backup-codes', said)).backupCodes)
    await auth('/two-factor/disable', said)
    onChange(false)
    toast(t('ts.offDone'), { icon: 'shield' }, 6000)
    onClose()
  })

  const secret = setup ? new URL(setup.totpURI).searchParams.get('secret') ?? '' : ''
  const title = codes ? t('ts.codesTitle') : t(doing === 'on' ? 'ts.onTitle' : doing === 'off' ? 'ts.offTitle' : 'ts.newCodesTitle')
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="shield" title={title} onClose={onClose}
        description={codes ? t('ts.codesBody') : setup ? t('ts.scan') : t(doing === 'on' ? (hasPassword ? 'ts.onBody' : 'ts.onBodyNoPassword') : doing === 'off' ? (hasPassword ? 'ts.offBody' : 'ts.offBodyNoPassword') : hasPassword ? 'ts.newCodesBody' : 'ts.newCodesBodyNoPassword')}
        actions={old ? [
          <K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>,
          <K.Button key="o" variant="primary" onClick={signOut}>{t('ac.signOut')}</K.Button>,
        ] : codes ? [
          <K.Button key="c" variant="ghost" onClick={() => navigator.clipboard.writeText(codes.join('\n')).then(() => toast(t('ts.copied'), {}, 3000))}>{t('ts.copy')}</K.Button>,
          <K.Button key="d" variant="primary" onClick={onClose}>{t('ts.saved')}</K.Button>,
        ] : [
          <K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>,
          <K.Button key="n" variant={doing === 'off' ? 'danger' : 'primary'} loading={busy} disabled={setup ? code.trim().length < 6 : hasPassword && !password} onClick={next}>
            {t(setup ? 'ts.finish' : doing === 'on' ? 'ts.continue' : doing === 'off' ? 'ts.offGo' : 'ts.newCodesGo')}
          </K.Button>,
        ]}>
        {old ? <K.Callout tone="warm" title={t('lv.staleTitle')}>{t('am.fresh')}</K.Callout> : codes ? (
          <pre className="ts-codes">{codes.join('\n')}</pre>
        ) : setup ? (
          <>
            <img className="ts-qr" alt={t('ts.qrAlt')} src={`data:image/svg+xml,${encodeURIComponent(renderSVG(setup.totpURI))}`} />
            <K.KeyValue label={t('ts.secret')}><code className="ts-secret">{secret}</code></K.KeyValue>
            <K.TextField label={t('ts.code')} value={code} onChange={setCode} max={6} />
          </>
        ) : hasPassword ? (
          <K.TextField label={t('si.password')} type="password" value={password} onChange={setPassword} />
        ) : null}
        {error && <K.Callout tone="bad">{error}</K.Callout>}
      </K.Dialog>
    </Overlay>
  )
}
