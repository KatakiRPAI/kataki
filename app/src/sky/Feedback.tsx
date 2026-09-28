// Tell us something (L1–L4): feedback, a bug, or a suggestion, from any page.
import { useState, useSyncExternalStore } from 'react'
import { api, type RoleRow } from '../api'
import { K } from '../ds'
import { useLoad } from '../hooks'
import { Overlay } from '../overlay'
import { t } from '../strings'

type Kind = 'feedback' | 'bug' | 'suggestion'
let open: Kind | null = null
const subs = new Set<() => void>()
export const openFeedback = (kind: Kind) => { open = kind; subs.forEach((f) => f()) }
const close = () => { open = null; subs.forEach((f) => f()) }
// The feedback host is the product owner's to supply (README › Copy rules 6); until then, copy.
const HOST = import.meta.env.VITE_FEEDBACK_HOST as string | undefined

export function Feedback() {
  const kind0 = useSyncExternalStore((f) => (subs.add(f), () => subs.delete(f)), () => open)
  if (!kind0) return null
  return <Dialog key={kind0} first={kind0} />
}

function Dialog({ first }: { first: Kind }) {
  const [kind, setKind] = useState<Kind>(first)
  const [text, setText] = useState('')
  const [more, setMore] = useState('')
  const [email, setEmail] = useState('')
  const [result, setResult] = useState<'copied' | 'cant' | 'sent' | null>(null)
  const [health] = useLoad(() => api<{ version: string }>('/health'), [])
  const [roles] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const [dropped, setDropped] = useState<string[]>([])
  const os = navigator.userAgent.includes('Windows') ? 'Windows' : navigator.userAgent.includes('Mac') ? 'macOS' : 'Linux'
  const rp = roles?.find((r) => r.role === 'rp')
  const facts = [
    ['version', t('fb.version', { v: health?.version ?? '?', os })],
    ['model', t('fb.model', { server: String(rp?.effective_provider_id ?? '—'), model: rp?.effective_model ?? '—' })],
  ].filter(([k]) => !dropped.includes(k))
  const kinds: [Kind, 'fb.feedback' | 'fb.bug' | 'fb.suggestion'][] = [['feedback', 'fb.feedback'], ['bug', 'fb.bug'], ['suggestion', 'fb.suggestion']]
  const report = () => [`${t(kinds.find(([k]) => k === kind)![1])}`, text, more, email && `Reply to: ${email}`, ...(kind === 'bug' ? facts.map(([, v]) => v) : [])].filter(Boolean).join('\n\n')
  const copy = () => navigator.clipboard?.writeText(report()).then(() => setResult('copied'), () => setResult('copied'))
  const send = async () => {
    if (!HOST) return setResult('cant')
    try {
      await fetch(HOST, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ kind, text, more, email, facts: kind === 'bug' ? facts : [] }) })
      setResult('sent')
    } catch {
      setResult('cant')
    }
  }
  if (result) {
    return (
      <Overlay onClose={close}>
        <K.Dialog icon={result === 'cant' ? 'alert' : 'check'} tone={result === 'cant' ? 'warm' : undefined} size="sm" onClose={close}
          title={t(result === 'copied' ? 'fb.copied' : result === 'cant' ? 'fb.cant' : 'fb.copied')}
          description={t(result === 'copied' ? 'fb.copiedBody' : result === 'cant' ? 'fb.cantBody' : 'fb.copiedBody')}
          actions={result === 'cant' ? [<K.Button key="c" variant="ghost" onClick={close}>{t('fb.cancel')}</K.Button>, <K.Button key="p" variant="primary" onClick={copy}>{t('fb.copy')}</K.Button>]
            : [<K.Button key="d" variant="primary" onClick={close}>{t('fb.done')}</K.Button>]} />
      </Overlay>
    )
  }
  return (
    <Overlay onClose={close}>
      <K.Dialog icon="help" size="lg" title={t('fb.title')} description={t('fb.desc')} note={t('fb.note')} onClose={close}
        actions={[<K.Button key="c" variant="ghost" icon="link" onClick={copy} disabled={!text.trim()}>{t('fb.copy')}</K.Button>, <K.Button key="s" variant="primary" iconEnd="send" disabled={!text.trim()} onClick={send}>{t('fb.send')}</K.Button>]}>
        <K.Segmented label={t('fb.kind')} options={kinds.map(([, l]) => t(l))} value={t(kinds.find(([k]) => k === kind)![1])} onChange={(v) => setKind(kinds.find(([, l]) => t(l) === v)?.[0] ?? 'feedback')} />
        {kind === 'feedback' && (
          <>
            <K.TextArea label={t('fb.mind')} hint={t('fb.mindHint')} rows={4} value={text} onChange={setText} />
            <K.TextField label={t('fb.email')} hint={t('fb.emailHint')} optional type="email" value={email} onChange={setEmail} />
          </>
        )}
        {kind === 'bug' && (
          <>
            <K.TextArea label={t('fb.happened')} rows={3} value={text} onChange={setText} />
            <K.TextArea label={t('fb.more')} rows={3} optional value={more} onChange={setMore} />
            <K.Field label={t('fb.sent')} hint={t('fb.sentBody')}>
              <K.Panel flush>
                {facts.map(([k, v]) => (
                  <div key={k} className="ch-row" style={{ padding: '8px 14px' }}><span style={{ flex: 1 }} className="t-body">{v}</span>
                    <K.Button size="sm" variant="ghost" onClick={() => setDropped((d) => [...d, k])}>{t('fb.remove')}</K.Button></div>
                ))}
              </K.Panel>
            </K.Field>
          </>
        )}
        {kind === 'suggestion' && <K.TextArea label={t('fb.wanted')} hint={t('fb.wantedHint')} rows={4} value={text} onChange={setText} />}
      </K.Dialog>
    </Overlay>
  )
}
