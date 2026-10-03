// Models (K4–K8): where replies come from, and which model does which job.
import { useEffect, useState } from 'react'
import { api, type Provider, type RoleRow } from '../../api'
import { K } from '../../ds'
import type { IconName } from '../../ds/kataki'
import { useLoad } from '../../hooks'
import { Overlay, toast, openMenu, withMenu, type MenuItem } from '../../overlay'
import { t, type Key } from '../../strings'
import { classify, err } from '../../errors'
import { ModelPicker, type Job } from '../ModelPicker'
import { account } from '../../online/session'

type Test = { ok: boolean; ms?: number; error?: string; models?: string[] }
const JOBS: Job[] = ['rp', 'narrator', 'utility', 'reasoning', 'embed']
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
  if (account()) return <OnlineModels /> // online the service picks the models (design brief 3, K)
  return <LocalModels />
}

/** Kataki online: each job, its model and about what it costs; nothing here to set up. */
function OnlineModels() {
  const [roles] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const usd = (n: number) => new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: n < 0.1 ? 3 : 2 }).format(n)
  return (
    <K.SettingsSection title={t('mo.who')} note={t('mo.whoOnline')}>
      <K.Panel flush>
        {JOBS.map((job) => {
          const row = roles?.find((r) => r.role === job)
          const model = row?.effective_model ?? t(job === 'embed' ? 'mo.builtIn' : 'mo.unset')
          return <K.JobRow key={job} icon={ICON[job]} name={t(`mo.job.${job}` as Key)} description={t(`mo.job.${job}Sub` as Key)}
            model={row?.reply_cost ? t('mo.per100', { model, price: usd(row.reply_cost * 100) }) : model} />
        })}
      </K.Panel>
    </K.SettingsSection>
  )
}

const ICON: Record<Job, IconName> = { rp: 'users', narrator: 'quill', utility: 'thought', reasoning: 'spark', embed: 'search' }

function LocalModels() {
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
  // ConnectionMenu (M1): the jobs that borrow take it too, since only Characters is set
  const useFor = async (p: Provider, job: Job) => {
    const r = tests[p.id] && tests[p.id] !== 'testing' ? tests[p.id] as Test : await test(p)
    if (!r.ok || !r.models?.length) return toast(t('mo.noModels', { name: p.name }), {}, 5000)
    await api(`/roles/${job}`, 'PUT', { provider_id: p.id, model: r.models[0], kind: 'auto', params: {} })
    reloadRoles()
    toast(t('mo.usedFor', { name: p.name, job: t(`mo.job.${job}` as Key) }), {}, 4000)
  }
  const [editingConn, setEditingConn] = useState<Provider>()
  const connectionMenu = (p: Provider): MenuItem[] => [
    { label: t('mo.m.everything'), icon: 'check', onSelect: () => useFor(p, 'rp') },
    { label: t('mo.testAgain'), icon: 'refresh', onSelect: () => run(p) },
    { label: t('mo.m.edit'), icon: 'edit', onSelect: () => setEditingConn(p) },
    { label: t('mo.m.oneJob'), icon: 'cpu', onSelect: () => openMenu(document.activeElement ?? document.body, JOBS.filter((j) => j !== 'embed').map((j) => ({ label: t(`mo.job.${j}` as Key), onSelect: () => useFor(p, j) })), t('mo.m.oneJobTitle')) },
    { divider: true },
    { label: t('mo.m.remove'), icon: 'trash', danger: true, onSelect: () => remove(p) },
  ]

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
              <div key={p.id} {...withMenu(() => connectionMenu(p))}>
                <K.ConnectionRow icon={p.has_key ? 'globe' : 'server'} name={p.name} status={state} detail={t('mo.detail', { url: p.base_url, key: p.has_key ? 'yes' : 'no' })}
                  onTest={() => run(p)} testing={r === 'testing'} testLabel={t('mo.test')} onRemove={() => remove(p)} removeLabel={t('mo.remove')} />
                {bad && (
                  <div className="mo-err">
                    {(() => {
                      // the catalogue's words for what went wrong (SetModelsFailed, K6)
                      const online = !/^https?:\/\/(localhost|127\.|\[::1\])/.test(p.base_url)
                      const code = classify(bad.error ?? '', online, true)
                      const e = err(code === 'UNKNOWN' || code === 'REPLY_UNREACHABLE' ? 'SERVER_UNREACHABLE' : code, { server: p.name, provider: p.name, address: p.base_url, seconds: 5, model: rp?.effective_model ?? '' })
                      return (
                        <K.Callout tone="bad" title={e.title} action={<K.Button size="sm" onClick={() => run(p)}>{t('mo.testAgain')}</K.Button>}>
                          {e.body} <span className="errcode">{e.code}</span>
                        </K.Callout>
                      )
                    })()}
                  </div>
                )}
              </div>
            )
          })}
        </K.Panel>
        <div className="row" style={{ gap: 8 }}>
          <K.Button size="sm" icon="search" onClick={() => setAdding('find')}>{t('mo.find')}</K.Button>
          <K.Button size="sm" icon="plus" onClick={() => setAdding('api')}>{t('mo.addOnline')}</K.Button>
          <K.Button size="sm" variant="ghost" icon="refresh" href="/welcome">{t('mo.setup')}</K.Button>
        </div>
      </K.SettingsSection>

      <K.SettingsSection title={t('mo.who')} note={t('mo.whoSub')}>
        <K.Panel flush>
          {JOBS.map((job) => {
            const row = roles?.find((r) => r.role === job)
            const model = row?.model ?? (row?.inherited_from ? t('mo.borrows', { job: t(`mo.job.${row.inherited_from}` as Key) }) : row?.effective_model ?? (job === 'embed' ? t('mo.builtIn') : t('mo.unset')))
            return (
              <div key={job}>
                <K.JobRow icon={ICON[job]}
                  name={t(`mo.job.${job}` as Key)} description={t(`mo.job.${job}Sub` as Key)} model={model} open={open === job}
                  onClick={() => setOpen(open === job ? undefined : job)} />
                {open === job && row && <JobPanel key={job} job={job} row={row} providers={providers ?? []} onSaved={reloadRoles} />}
              </div>
            )
          })}
        </K.Panel>
      </K.SettingsSection>

      {editingConn && <EditConnection p={editingConn} onClose={() => setEditingConn(undefined)} onDone={reload} />}
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
        <ModelPicker label={t('mo.model')} job={job} providers={providers} value={pid && model ? { provider_id: pid, model } : null}
          onChange={(v) => { if (v) { setPid(v.provider_id); setModel(v.model) } }} />
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
            <ModelPicker label={t('mo.model')} job="rp" providers={[made.provider]} value={model ? { provider_id: made.provider.id, model } : null} onChange={(v) => setModel(v?.model ?? '')} />
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


/** ConnectionMenu › Edit address or key. An empty key field leaves the key as it is. */
function EditConnection({ p, onClose, onDone }: { p: Provider; onClose: () => void; onDone: () => void }) {
  const [name, setName] = useState(p.name)
  const [address, setAddress] = useState(p.base_url)
  const [key, setKey] = useState('')
  const save = () => api(`/providers/${p.id}`, 'PATCH', { name: name.trim(), base_url: address.trim(), ...(key.trim() ? { api_key: key.trim() } : {}) }).then(() => { onDone(); onClose() })
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="server" title={t('mo.editTitle', { name: p.name })} onClose={onClose}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('api.cancel')}</K.Button>, <K.Button key="s" variant="primary" disabled={!name.trim() || !address.trim()} onClick={save}>{t('ep.save')}</K.Button>]}>
        <K.TextField label={t('api.call')} value={name} onChange={setName} />
        <K.TextField label={t('api.address')} icon="link" value={address} onChange={setAddress} />
        <K.TextField label={t('api.key')} icon="key" type="password" optional placeholder={p.has_key ? t('mo.keyKept') : ''} value={key} onChange={setKey} />
      </K.Dialog>
    </Overlay>
  )
}
