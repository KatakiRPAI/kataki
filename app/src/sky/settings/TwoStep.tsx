// Two-step sign-in (docs/specs/2026-10-02-kataki-online.md G4): turning it on with an
// authenticator app, the backup codes, new codes, and turning it off. Each needs the password.
import { useState } from 'react'
import { renderSVG } from 'uqr'
import { K } from '../../ds'
import { auth, type AuthError } from '../../online/session'
import { Overlay, toast } from '../../overlay'
import { t } from '../../strings'

type Doing = 'on' | 'off' | 'codes'

export default function TwoStep({ doing, onClose, onChange }: { doing: Doing; onClose: () => void; onChange: (on: boolean) => void }) {
  const [password, setPassword] = useState('')
  const [setup, setSetup] = useState<{ totpURI: string; backupCodes: string[] }>() // on: the app is being paired
  const [code, setCode] = useState('')
  const [codes, setCodes] = useState<string[]>() // shown once, at the end
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const run = async (what: () => Promise<void>) => {
    setBusy(true)
    setError('')
    try { await what() } catch (x) { setError(t((x as AuthError).code === 'INVALID_CODE' ? 'ts.e.code' : setup ? 'ts.e.code' : 'ts.e.password')) } finally { setBusy(false) }
  }
  const next = () => run(async () => {
    if (doing === 'on' && !setup) return setSetup(await auth('/two-factor/enable', { password }))
    if (doing === 'on') {
      await auth('/two-factor/verify-totp', { code: code.trim() }) // on only once a code has come back
      onChange(true)
      return setCodes(setup!.backupCodes)
    }
    if (doing === 'codes') return setCodes((await auth<{ backupCodes: string[] }>('/two-factor/generate-backup-codes', { password })).backupCodes)
    await auth('/two-factor/disable', { password })
    onChange(false)
    toast(t('ts.offDone'), { icon: 'shield' }, 6000)
    onClose()
  })

  const secret = setup ? new URL(setup.totpURI).searchParams.get('secret') ?? '' : ''
  const title = codes ? t('ts.codesTitle') : t(doing === 'on' ? 'ts.onTitle' : doing === 'off' ? 'ts.offTitle' : 'ts.newCodesTitle')
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="shield" title={title} onClose={onClose}
        description={codes ? t('ts.codesBody') : setup ? t('ts.scan') : t(doing === 'on' ? 'ts.onBody' : doing === 'off' ? 'ts.offBody' : 'ts.newCodesBody')}
        actions={codes ? [
          <K.Button key="c" variant="ghost" onClick={() => navigator.clipboard.writeText(codes.join('\n')).then(() => toast(t('ts.copied'), {}, 3000))}>{t('ts.copy')}</K.Button>,
          <K.Button key="d" variant="primary" onClick={onClose}>{t('ts.saved')}</K.Button>,
        ] : [
          <K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>,
          <K.Button key="n" variant={doing === 'off' ? 'danger' : 'primary'} loading={busy} disabled={setup ? code.trim().length < 6 : !password} onClick={next}>
            {t(setup ? 'ts.finish' : doing === 'on' ? 'ts.continue' : doing === 'off' ? 'ts.offGo' : 'ts.newCodesGo')}
          </K.Button>,
        ]}>
        {codes ? (
          <pre className="ts-codes">{codes.join('\n')}</pre>
        ) : setup ? (
          <>
            <img className="ts-qr" alt={t('ts.qrAlt')} src={`data:image/svg+xml,${encodeURIComponent(renderSVG(setup.totpURI))}`} />
            <K.KeyValue label={t('ts.secret')}><code className="ts-secret">{secret}</code></K.KeyValue>
            <K.TextField label={t('ts.code')} value={code} onChange={setCode} max={6} />
          </>
        ) : (
          <K.TextField label={t('si.password')} type="password" value={password} onChange={setPassword} hint={t('ts.passwordHint')} />
        )}
        {error && <K.Callout tone="bad">{error}</K.Callout>}
      </K.Dialog>
    </Overlay>
  )
}
