// Models (K4–K8): where replies come from, and which model does which job.
import { useEffect, useState } from 'react'
import { api, type Provider, type RoleRow } from '../../api'
import { K } from '../../ds'
import { useLoad } from '../../hooks'
import { Overlay, toast } from '../../overlay'
import { t, type Key } from '../../strings'

type Test = { ok: boolean; ms?: number; error?: string; models?: string[] }
const JOBS = ['rp', 'narrator', 'utility', 'reasoning', 'embed'] as const
type Job = (typeof JOBS)[number]
const ABOVE: Partial<Record<Job, Job>> = { narrator: 'rp', utility: 'rp', reasoning: 'utility' }

async function test(p: Provider): Promise<Test> {
  const start = performance.now()
  try {
    const { models } = await api<{ models: string[] }>(`/providers/${p.id}/models`)
    return { ok: true, ms: performance.now() - start, models }
  } catch (e) {
    return { ok: false, error: (e as Error).message }
  }
}

export default function Models() {
  const [providers, reloadProviders] = useLoad(() => api<Provider[]>('/providers'), [])
  const [roles, reloadRoles] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const [tests, setTests] = useState<Record<number, Test | 'testing'>>({})
  const [open, setOpen] = useState<Job>()
  const [adding, setAdding] = useState<'api' | 'find' | null>(null)
  const rp = roles?.find((r) => r.role === 'rp')
  const main = providers?.find((p) => p.id === rp?.effective_provider_id)
  const run = async (p: Provider) => {
    setTests((x) => ({ ...x, [p.id]: 'testing' }))
    const r = await test(p)
    setTests((x) => ({ ...x, [p.id]: r }))
  }
  const mainTest = main ? tests[main.id] : undefined
  useEffect(() => { if (main && !tests[main.id]) run(main) }, [main?.id]) // eslint-disable-line react-hooks/exhaustive-deps
  const status = !main || !rp?.effective_model
    ? <K.StatusLine tone="warm" title={t('mo.none')}>{t('mo.noneBody')}</K.StatusLine>
    : mainTest && mainTest !== 'testing' && !mainTest.ok
      ? <K.StatusLine tone="bad" title={t('mo.bad')} action={<K.Button size="sm" onClick={() => run(main)}>{t('mo.testAgain')}</K.Button>}>{t('mo.badBody', { server: main.name })}</K.StatusLine>
      : <K.StatusLine tone="ok" title={t('mo.ok')} action={<K.Button size="sm" loading={mainTest === 'testing'} onClick={() => run(main)}>{t('mo.testAgain')}</K.Button>}>
          {t('mo.okBody', { model: rp.effective_model, server: main.name, s: mainTest && mainTest !== 'testing' ? (mainTest.ms! / 1000).toFixed(1) : '—' })}
        </K.StatusLine>
  const reload = () => { reloadProviders(); reloadRoles() }
  const remove = (p: Provider) => api(`/providers/${p.id}`, 'DELETE').then(reload)

  return (
    <>
      {status}
      <K.SettingsSection title={t('mo.where')} note={t('mo.whereNote')}>
        <K.Panel flush>
          {(providers ?? []).map((p) => {
            const r = tests[p.id]
            const state = r === 'testing' || !r ? (p.id === main?.id ? 'connected' : 'ready') : r.ok ? (p.id === main?.id ? 'connected' : 'ready') : 'offline'
            const bad = r && r !== 'testing' && !r.ok ? r : undefined
            return (
              <div key={p.id}>
                <K.ConnectionRow icon={p.has_key ? 'globe' : 'server'} name={p.name} status={state} detail={t('mo.detail', { url: p.base_url, key: p.has_key ? 'yes' : 'no' })}
                  onTest={() => run(p)} testing={r === 'testing'} testLabel={t('mo.test')} onRemove={() => remove(p)} removeLabel={t('mo.remove')} />
                {bad && (
                  <div className="mo-err">
                    <K.Callout tone="bad" title={/401|unauthor/i.test(bad.error ?? '') ? t('mo.keyBad', { name: p.name }) : t('mo.failed', { url: p.base_url })}
                      action={<K.Button size="sm" onClick={() => run(p)}>{t('mo.testAgain')}</K.Button>}>
                      {/401|unauthor/i.test(bad.error ?? '') ? t('mo.keyBadBody') : t('mo.failedBody', { error: bad.error ?? '' })}
                    </K.Callout>
                  </div>
                )}
              </div>
            )
          })}
        </K.Panel>
        <div className="row" style={{ gap: 8 }}>
          <K.Button size="sm" icon="search" onClick={() => setAdding('find')}>{t('mo.find')}</K.Button>
          <K.Button size="sm" icon="plus" onClick={() => setAdding('api')}>{t('mo.addOnline')}</K.Button>
        </div>
      </K.SettingsSection>

      <K.SettingsSection title={t('mo.who')} note={t('mo.whoSub')}>
        <K.Panel flush>
          {JOBS.map((job) => {
            const row = roles?.find((r) => r.role === job)
            const model = row?.model ?? (row?.inherited_from ? t('mo.borrows', { job: t(`mo.job.${row.inherited_from}` as Key) }) : row?.effective_model ?? (job === 'embed' ? t('mo.builtIn') : t('mo.unset')))
            return (
              <div key={job}>
                <K.JobRow icon={job === 'embed' ? 'search' : job === 'utility' ? 'thought' : job === 'reasoning' ? 'spark' : job === 'narrator' ? 'quill' : 'users'}
                  name={t(`mo.job.${job}` as Key)} description={t(`mo.job.${job}Sub` as Key)} model={model} open={open === job}
                  onClick={() => setOpen(open === job ? undefined : job)} />
                {open === job && row && <JobPanel key={job} job={job} row={row} providers={providers ?? []} onSaved={reloadRoles} />}
              </div>
            )
          })}
        </K.Panel>
      </K.SettingsSection>

      {adding === 'api' && <AddApi onClose={() => setAdding(null)} onAdded={reload} />}
      {adding === 'find' && <FindServers providers={providers ?? []} onClose={() => setAdding(null)} onAdded={reload} />}
    </>
  )
}

/** K5: one job opened: its connection and model, how much it thinks, and its sampling. */
function JobPanel({ job, row, providers, onSaved }: { job: Job; row: RoleRow; providers: Provider[]; onSaved: () => void }) {
  const borrows = !!ABOVE[job]
  const [inherit, setInherit] = useState(borrows && row.provider_id === null)
  const [pid, setPid] = useState<number | null>(row.provider_id ?? providers[0]?.id ?? null)
  const [model, setModel] = useState(row.model ?? '')
  const [params, setParams] = useState<Record<string, unknown>>(row.params ?? {})
  const body = (params.body ?? {}) as Record<string, unknown>
  const [models] = useLoad(() => (pid ? api<{ models: string[] }>(`/providers/${pid}/models`).then((m) => m.models, () => []) : Promise.resolve([])), [pid])
  const setBody = (k: string, v: unknown) => setParams((p) => ({ ...p, body: { ...((p.body ?? {}) as object), [k]: v === '' || v === undefined ? undefined : v } }))
  const num = (k: string) => (body[k] === undefined ? '' : String(body[k]))
  const save = async () => {
    await api(`/roles/${job}`, 'PUT', { provider_id: inherit ? null : pid, model: inherit ? null : model || null, kind: row.kind, params })
    onSaved()
    toast(t('set.saved'), {}, 2000)
  }
  const efforts: [string, Key][] = [['', 'mo.think.none'], ['low', 'mo.think.low'], ['medium', 'mo.think.medium'], ['high', 'mo.think.high']]
  return (
    <div className="mo-job">
      {borrows && <K.Checkbox label={t('mo.borrow')} checked={inherit} onChange={setInherit} />}
      {!inherit && (
        <div className="mo-grid">
          <K.Select label={t('mo.connection')} options={providers.map((p) => p.name)} value={providers.find((p) => p.id === pid)?.name}
            onChange={(v) => setPid(providers.find((p) => p.name === v)?.id ?? null)} />
          <K.Select label={t('mo.model')} options={[...new Set([model, ...(models ?? [])].filter(Boolean))]} value={model} onChange={setModel} />
        </div>
      )}
      {job !== 'embed' && (
        <>
          <K.Select label={t('mo.thinking')} options={efforts.map(([, l]) => t(l))} value={t(efforts.find(([v]) => v === (params.reasoning_effort ?? ''))?.[1] ?? 'mo.think.none')}
            onChange={(v) => setParams((p) => ({ ...p, reasoning_effort: efforts.find(([, l]) => t(l) === v)?.[0] || undefined }))} />
          <div className="mo-grid">
            <K.Slider label={t('mo.temperature')} min={0} max={2} step={0.05} value={Number(body.temperature ?? 1)} valueText={String(body.temperature ?? 1)} onChange={(v) => setBody('temperature', v)} />
            <K.Slider label={t('mo.longest')} min={64} max={4096} step={64} value={Number(body.max_tokens ?? 512)} valueText={String(body.max_tokens ?? 512)} onChange={(v) => setBody('max_tokens', v)} />
            <K.Slider label={t('mo.context')} min={2048} max={131072} step={2048} value={Number(params.ctx_size ?? 16384)} valueText={String(params.ctx_size ?? 16384)} onChange={(v) => setParams((p) => ({ ...p, ctx_size: v }))} />
            <K.TextField label={t('mo.topP')} value={num('top_p')} onChange={(v) => setBody('top_p', v ? Number(v) : undefined)} />
            <K.TextField label={t('mo.minP')} value={num('min_p')} onChange={(v) => setBody('min_p', v ? Number(v) : undefined)} />
            <K.TextField label={t('mo.rep')} value={num('repetition_penalty')} onChange={(v) => setBody('repetition_penalty', v ? Number(v) : undefined)} />
            <K.TextField label={t('mo.seed')} hint={t('mo.seedHint')} value={num('seed')} onChange={(v) => setBody('seed', v ? Number(v) : undefined)} />
          </div>
          <K.TextArea label={t('mo.stop')} hint={t('mo.stopHint')} optional rows={2} value={((body.stop as string[] | undefined) ?? []).join('\n')}
            onChange={(v) => setBody('stop', v.split('\n').map((x) => x.trim()).filter(Boolean))} />
        </>
      )}
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <span className="t-faint">{t('mo.note')}</span>
        <div className="row" style={{ gap: 8 }}>
          <K.Button size="sm" variant="ghost" onClick={() => setParams({})}>{t('mo.defaults')}</K.Button>
          <K.Button size="sm" variant="primary" onClick={save}>{t('mo.save')}</K.Button>
        </div>
      </div>
    </div>
  )
}

const SERVICES: [string, Key, string][] = [
  ['openrouter', 'api.openrouter', 'https://openrouter.ai/api/v1'], ['openai', 'api.openai', 'https://api.openai.com/v1'],
  ['anthropic', 'api.anthropic', 'https://api.anthropic.com/v1'], ['other', 'api.other', ''],
]

/** K7: an online model, by key. */
function AddApi({ onClose, onAdded }: { onClose: () => void; onAdded: () => void }) {
  const [service, setService] = useState('openrouter')
  const [address, setAddress] = useState('')
  const [key, setKey] = useState('')
  const [name, setName] = useState('')
  const [made, setMade] = useState<{ provider: Provider; models: string[] }>()
  const [model, setModel] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const url = service === 'other' ? address.trim() : SERVICES.find(([s]) => s === service)![2]
  const call = name.trim() || t(SERVICES.find(([s]) => s === service)![1])
  const tryIt = async () => {
    setBusy(true)
    setError('')
    try {
      const provider = made?.provider ?? await api<Provider>('/providers', 'POST', { name: call, base_url: url, api_key: key.trim() || null })
      const r = await test(provider)
      if (!r.ok) { setMade({ provider, models: [] }); throw new Error(r.error) }
      setMade({ provider, models: r.models ?? [] })
      setModel(r.models?.[0] ?? '')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  const cancel = () => { if (made && !model) api(`/providers/${made.provider.id}`, 'DELETE').catch(() => {}); onClose() }
  const add = async () => {
    if (!made) return
    await api('/roles/rp', 'PUT', { provider_id: made.provider.id, model, kind: 'auto', params: {} })
    onAdded()
    onClose()
  }
  return (
    <Overlay onClose={cancel}>
      <K.Dialog icon="globe" size="lg" title={t('api.title')} description={t('api.desc')} note={t('fr.keyStored', { os: /Win/.test(navigator.userAgent) ? 'win' : /Mac/.test(navigator.userAgent) ? 'mac' : 'other' })} onClose={cancel}
        actions={[
          <K.Button key="c" variant="ghost" onClick={cancel}>{t('api.cancel')}</K.Button>,
          made?.models.length ? <K.Button key="a" variant="primary" disabled={!model} onClick={add}>{t('api.add')}</K.Button>
            : <K.Button key="t" variant="primary" loading={busy} disabled={!url || !key.trim()} onClick={tryIt}>{t('api.test')}</K.Button>,
        ]}>
        <K.Segmented label={t('api.service')} options={SERVICES.map(([, l]) => t(l))} value={t(SERVICES.find(([s]) => s === service)![1])}
          onChange={(v) => setService(SERVICES.find(([, l]) => t(l) === v)?.[0] ?? 'openrouter')} />
        {service === 'other' && <K.TextField label={t('api.address')} required icon="link" hint={t('api.addressHint')} value={address} onChange={setAddress} placeholder="https://…/v1" />}
        <K.TextField label={t('api.key')} required icon="key" type="password" value={key} onChange={setKey} />
        <K.TextField label={t('api.call')} optional hint={t('api.callHint')} value={name} onChange={setName} placeholder={call} />
        {error && <K.Callout tone="bad" title={t('api.bad')}>{error}</K.Callout>}
        {made && made.models.length > 0 && (
          <>
            <K.StatusLine tone="ok" title={t('api.result', { service: call, n: made.models.length })} />
            <K.Select label={t('mo.model')} options={made.models} value={model} onChange={setModel} />
          </>
        )}
      </K.Dialog>
    </Overlay>
  )
}

/** K8: model servers already running on this computer. */
function FindServers({ providers, onClose, onAdded }: { providers: Provider[]; onClose: () => void; onAdded: () => void }) {
  const [found, again] = useLoad(() => api<{ name: string; base_url: string; models: string[] }[]>('/providers/detect'), [])
  const [address, setAddress] = useState('')
  const add = async (name: string, base_url: string, model?: string) => {
    const p = await api<Provider>('/providers', 'POST', { name, base_url })
    if (model && !providers.length) await api('/roles/rp', 'PUT', { provider_id: p.id, model, kind: 'auto', params: {} })
    onAdded()
  }
  const here = (url: string) => providers.some((p) => p.base_url.replace(/\/$/, '') === url.replace(/\/$/, ''))
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="server" size="lg" title={t('fs.title')} description={t('fs.body')} onClose={onClose}
        actions={[<K.Button key="a" variant="ghost" onClick={() => again()}>{t('fs.again')}</K.Button>, <K.Button key="d" variant="primary" onClick={onClose}>{t('fs.done')}</K.Button>]}>
        {found === undefined ? <K.Spinner /> : !found.length ? <span className="t-meta">{t('fs.none')}</span> : (
          <K.Panel flush>
            {found.map((f) => (
              <div key={f.base_url} className="ch-row" style={{ padding: '10px 14px' }}>
                <div style={{ flex: 1 }}><b>{f.name}</b><div className="t-meta">{t('fs.models', { n: f.models.length, names: f.models.slice(0, 3).join(', ') })}</div></div>
                {here(f.base_url) ? <K.StatePill tone="ok">{t('fs.added')}</K.StatePill>
                  : <K.Button size="sm" onClick={() => add(f.name, f.base_url, f.models[0])}>{t('fs.add')}</K.Button>}
              </div>
            ))}
          </K.Panel>
        )}
        <div className="row" style={{ gap: 8, alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}><K.TextField label={t('fs.byAddress')} hint={t('fs.byAddressHint')} value={address} onChange={setAddress} placeholder="http://192.168.1.20:8080/v1" /></div>
          <K.Button disabled={!/^https?:\/\//.test(address.trim())} onClick={() => add(new URL(address.trim()).host, address.trim()).then(() => setAddress(''))}>{t('fs.add')}</K.Button>
        </div>
      </K.Dialog>
    </Overlay>
  )
}

