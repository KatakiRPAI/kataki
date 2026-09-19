import { useEffect, useState } from 'react'
import { api, type Kind, type Provider, type RoleRow } from '../api'
import { href, useAction, useLoad } from '../hooks'
import { Candy, Chip, Dialog, ErrorLine, Field, Glass, Icon, Seg, type CandyColor } from '../ui'

// Settings: the model servers and which model does each job (every field of the old Models page), and About.

const PRESETS = [
  { name: 'OpenRouter', base_url: 'https://openrouter.ai/api/v1' },
  { name: 'HuggingFace', base_url: 'https://router.huggingface.co/v1' },
  { name: 'llama.cpp', base_url: 'http://127.0.0.1:8080/v1' },
  { name: 'Ollama', base_url: 'http://127.0.0.1:11434/v1' },
  { name: 'LM Studio', base_url: 'http://127.0.0.1:1234/v1' },
]

type Job = { role: string; label: string; short: string; help: string; icon: string; color: CandyColor }

const JOBS: Job[] = [
  { role: 'rp', label: 'Characters', short: "Speaks for everyone you've added", icon: 'users', color: 'pink',
    help: 'Every character reply. A standard (non-reasoning) model keeps replies fast.' },
  { role: 'narrator', label: 'Narrator', short: 'Tells what happens between the lines', icon: 'feather', color: 'orange',
    help: 'Narration and scene description. Left empty, it uses Characters.' },
  { role: 'utility', label: 'Memory reader', short: 'Files what happened every few turns', icon: 'book', color: 'green',
    help: 'Reads the story into memory every few turns, at temperature 0. A small fast model is ideal.' },
  { role: 'reasoning', label: 'Reasoning', short: 'Reads carefully when a scene closes', icon: 'spark', color: 'purple',
    help: 'Careful re-reads when a scene closes, and on request. A reasoning model shines here.' },
  { role: 'embed', label: 'Recall by meaning', short: 'Finds memories that fit the moment', icon: 'search', color: 'blue',
    help: 'Lets "that treachery" find "Tobin betrayed us". Works out of the box: a small built-in model runs on this computer (downloaded once, 125 MB). Pick a server only to use your own embedding model, such as nomic-embed-text in Ollama.' },
] // one job per model role; images and music get theirs in later milestones

const SAMPLERS: Record<string, Record<string, number>> = {
  Balanced: { temperature: 1.0, min_p: 0.05 },
  'Balanced + DRY': { temperature: 1.0, min_p: 0.05, dry_multiplier: 0.8, dry_base: 1.75, dry_allowed_length: 2 },
  'Creative + XTC': {
    temperature: 1.0, min_p: 0.05, dry_multiplier: 0.8, dry_base: 1.75, dry_allowed_length: 2,
    xtc_threshold: 0.1, xtc_probability: 0.5,
  },
  Focused: { temperature: 0.7, min_p: 0.1 },
} // DRY and XTC are llama.cpp and KoboldCpp samplers

const isLocal = (url: string) => /\/\/(127\.0\.0\.1|localhost|\[::1\])[:/]/.test(url)
const host = (url: string) => (isLocal(url) ? url.replace(/^https?:\/\//, '').replace(/\/v1\/?$/, '') : url.replace(/^https?:\/\//, ''))
const jobOf = (role: string | null) => JOBS.find((j) => j.role === role)

type Probe = { ok: boolean; models: string[]; error?: string }

/** #/settings and #/settings/about */
export default function Settings({ page }: { page?: string }) {
  const [health, , healthError] = useLoad(() => api<{ version: string; schema: number }>('/health'), [])
  const about = page === 'about'
  return (
    <div className="ka-settings">
      <nav className="k-glass ka-subnav" aria-label="Settings">
        <span className="k-display ka-subnav__title">Settings</span>
        <a className="ka-subnav__item" href={href('/settings')} aria-current={about ? undefined : 'page'}>
          <Icon name="cpu" size={17} />
          Models
        </a>
        <a className="ka-subnav__item" href={href('/settings/about')} aria-current={about ? 'page' : undefined}>
          <Icon name="help" size={17} />
          About
        </a>
      </nav>
      <div className="ka-settings__main">
        <header className="ka-settings__head">
          <span className="ka-stack ka-stack--tight">
            <h1 className="k-display ka-page-title">{about ? 'About' : 'Models'}</h1>
            {!about && <span className="ka-muted">Kataki ships no model. Connect one, and pick which does each job. One is enough to start.</span>}
          </span>
          <span className={`k-status${health ? '' : ' k-status--warn'}`}>{health ? 'engine ok' : healthError ? 'engine unreachable' : 'connecting…'}</span>
        </header>
        {about ? (
          <Glass title="Kataki RPAI">
            <span className="k-mono">engine ok · v{health?.version ?? '…'} · schema {health?.schema ?? '…'}</span>
            <span className="ka-muted">Role-play with characters who remember: who heard what, and how clearly, as story time goes by.</span>
            <span className="ka-muted">Everything runs on your computer. Text only leaves it for the models you connect.</span>
          </Glass>
        ) : (
          <Models />
        )}
      </div>
    </div>
  )
}

function Models() {
  const [providers, reloadProviders, providerError] = useLoad(() => api<Provider[]>('/providers'), [])
  const [roles, reloadRoles, roleError] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const [open, setOpen] = useState('rp')
  const reload = () => {
    reloadProviders()
    reloadRoles()
  }
  const row = (role: string) => roles?.find((r) => r.role === role)
  const shown = row(open)
  return (
    <>
      <ErrorLine error={providerError || roleError} />
      <Servers providers={providers ?? []} roles={roles ?? []} onChange={reload} />
      <section className="k-glass ka-panel" aria-labelledby="ka-jobs-title">
        <h2 id="ka-jobs-title">Jobs</h2>
        {roles && shown && (
          <div className="ka-jobs">
            <JobEditor key={open} job={jobOf(open)!} row={shown} providers={providers ?? []} onChange={reloadRoles} />
            <div className="ka-stack">
              {JOBS.filter((j) => j.role !== open).map((j) => {
                const [line, sub] = summary(j, row(j.role)!, providers ?? [])
                return (
                  <button key={j.role} type="button" className="ka-job-row" onClick={() => setOpen(j.role)}>
                    <Candy icon={j.icon} color={j.color} />
                    <span className="ka-stack ka-stack--tight">
                      <strong>{j.label}</strong>
                      <span className="ka-job-row__line">{line}</span>
                      <span className="ka-muted ka-small">{sub}</span>
                    </span>
                    <Icon name="right" size={18} />
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </section>
    </>
  )
}

/** What a collapsed job shows: where its model comes from, and one more line. */
function summary(job: Job, row: RoleRow, providers: Provider[]): [string, string] {
  if (!row.effective_model) return job.role === 'embed' ? ['Built-in', 'Runs on this computer, no server needed'] : ['No model yet', job.short]
  const server = providers.find((p) => p.id === row.effective_provider_id)?.name ?? 'a server'
  if (row.inherited_from) return [`Same as ${jobOf(row.inherited_from)?.label ?? row.inherited_from}`, `${server} · ${row.effective_model}`]
  const thinking = row.params.thinking === 'enabled' ? ' · thinking on' : row.params.thinking === 'disabled' ? ' · thinking off' : ''
  return [`${row.effective_model}${thinking}`, job.short]
}

function Servers({ providers, roles, onChange }: { providers: Provider[]; roles: RoleRow[]; onChange: () => void }) {
  const [run, error, busy] = useAction()
  const [probes, setProbes] = useState<Record<number, Probe | undefined>>({})
  const [found, setFound] = useState<{ name: string; base_url: string; models: string[] }[] | null>(null)
  const [adding, setAdding] = useState({ open: false, n: 0 }) // n gives each opening a fresh form
  const [keyFor, setKeyFor] = useState<Provider>()
  const [removing, setRemoving] = useState<number>()
  const rpEmpty = !roles.find((r) => r.role === 'rp')?.model

  const test = (p: Provider) =>
    api<{ models: string[] }>(`/providers/${p.id}/models`).then(
      ({ models }) => setProbes((s) => ({ ...s, [p.id]: { ok: true, models } })),
      (e: Error) => setProbes((s) => ({ ...s, [p.id]: { ok: false, models: [], error: e.message } })),
    )
  const retest = (p: Provider) => {
    setProbes((s) => ({ ...s, [p.id]: undefined }))
    test(p)
  }
  useEffect(() => {
    providers.forEach(test) // an automatic test whenever the list changes
  }, [providers])

  const add = (name: string, base_url: string, api_key: string, firstModel?: string) =>
    run(async () => {
      const p = await api<Provider>('/providers', 'POST', { name, base_url, api_key: api_key || null })
      if (rpEmpty && firstModel) await api('/roles/rp', 'PUT', { provider_id: p.id, model: firstModel })
      setAdding((a) => ({ ...a, open: false }))
      onChange()
    })
  const known = new Set(providers.map((p) => p.base_url.replace(/\/$/, '')))
  const detected = (found ?? []).filter((f) => !known.has(f.base_url.replace(/\/$/, '')))

  return (
    <section className="k-glass ka-panel" aria-labelledby="ka-servers-title">
      <div className="ka-card-head">
        <h2 id="ka-servers-title">Model servers and APIs</h2>
        <span className="ka-row ka-row--gap">
          <button type="button" className="k-btn" disabled={busy} onClick={() => run(async () => setFound(await api('/providers/detect')))}>
            <Icon name="search" size={17} />
            Look for model servers on this computer
          </button>
          <button type="button" className="k-btn k-btn--dark" onClick={() => setAdding((a) => ({ open: true, n: a.n + 1 }))}>
            <Icon name="plus" size={17} />
            Add an API
          </button>
        </span>
      </div>
      {providers.length === 0 && !detected.length && (
        <span className="ka-muted">
          Nothing connected yet. If a model server already runs on this computer (llama.cpp, Ollama, LM Studio, KoboldCpp), look for it; otherwise add an API.
        </span>
      )}
      {found && !detected.length && providers.length > 0 && <span className="ka-muted ka-small">No other model servers found on this computer.</span>}
      {found && !found.length && providers.length === 0 && <span className="ka-muted ka-small">None found. Is the server running?</span>}
      <div className="ka-servers">
        {providers.map((p) => {
          const probe = probes[p.id]
          return (
            <div key={p.id} className="ka-server">
              <Candy icon={isLocal(p.base_url) ? 'server' : 'globe'} color={isLocal(p.base_url) ? 'green' : 'purple'} />
              <span className="ka-stack ka-stack--tight ka-grow">
                <strong>{p.name}</strong>
                <span className="ka-mono-sm">{isLocal(p.base_url) ? 'this computer' : 'online API'} · {host(p.base_url)}</span>
                <span className="ka-row ka-row--gap6">
                  {!probe && <span className="k-status k-status--idle">testing…</span>}
                  {probe && (probe.ok ? <span className="k-status">connected</span> : <span className="k-status k-status--warn" title={probe.error}>unreachable</span>)}
                  {probe?.ok && <span className="ka-pill">{probe.models.length === 1 ? `${probe.models[0]} loaded` : `${probe.models.length} models`}</span>}
                  {p.has_key && <span className="ka-pill ka-pill--gold">key stored</span>}
                </span>
              </span>
              {removing === p.id ? (
                <span className="ka-stack ka-server__actions">
                  <span className="ka-small">Remove {p.name}?</span>
                  <span className="ka-row ka-row--gap6">
                    <button type="button" className="k-btn k-btn--sm" onClick={() => setRemoving(undefined)}>Keep</button>
                    <button type="button" className="k-btn k-btn--dark k-btn--sm" onClick={() => run(async () => { await api(`/providers/${p.id}`, 'DELETE'); setRemoving(undefined); onChange() })}>Remove</button>
                  </span>
                </span>
              ) : (
                <span className="ka-stack ka-server__actions">
                  <button type="button" className="k-btn k-btn--sm" onClick={() => retest(p)}>Test</button>
                  {(p.has_key || !isLocal(p.base_url)) && (
                    <button type="button" className="k-btn k-btn--ghost k-btn--sm" onClick={() => setKeyFor(p)}>{p.has_key ? 'Change key' : 'Add a key'}</button>
                  )}
                  <button type="button" className="k-btn k-btn--danger k-btn--sm" onClick={() => setRemoving(p.id)}>Remove</button>
                </span>
              )}
            </div>
          )
        })}
        {detected.map((f) => (
          <div key={f.base_url} className="ka-server ka-server--found">
            <Candy icon="server" color="green" />
            <span className="ka-stack ka-stack--tight ka-grow">
              <strong>{f.name}</strong>
              <span className="ka-mono-sm">found on this computer · {host(f.base_url)}</span>
              <span className="ka-muted ka-small">{f.models.length ? f.models.slice(0, 3).join(', ') : 'no models listed'}</span>
            </span>
            <button type="button" className="k-btn k-btn--dark k-btn--sm" disabled={busy} onClick={() => add(f.name, f.base_url, '', f.models[0])}>
              {rpEmpty && f.models[0] ? 'Use this' : 'Add'}
            </button>
          </div>
        ))}
      </div>
      <ErrorLine error={error} />
      <AddApi key={adding.n} open={adding.open} onClose={() => setAdding((a) => ({ ...a, open: false }))} onAdd={(n, u, k) => add(n, u, k)} busy={busy} error={error} />
      <KeyDialog provider={keyFor} onClose={() => setKeyFor(undefined)} onSaved={onChange} />
    </section>
  )
}

function AddApi({ open, onClose, onAdd, busy, error }: { open: boolean; onClose: () => void; onAdd: (name: string, url: string, key: string) => void; busy: boolean; error: string }) {
  const [draft, setDraft] = useState({ name: '', base_url: '', api_key: '' })
  return (
    <Dialog open={open} onClose={onClose} title="Add an API">
      <form
        className="ka-form"
        onSubmit={(e) => {
          e.preventDefault()
          onAdd(draft.name.trim(), draft.base_url.trim(), draft.api_key)
        }}
      >
        <div className="ka-row">
          {PRESETS.map((p) => (
            <Chip key={p.name} pressed={draft.base_url === p.base_url} onClick={() => setDraft({ ...draft, name: p.name, base_url: p.base_url })}>{p.name}</Chip>
          ))}
        </div>
        <Field label="Name"><input className="k-input" required value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} /></Field>
        <Field label="Base URL (OpenAI-compatible)">
          <input className="k-input ka-mono-input" required placeholder="https://…/v1" value={draft.base_url} onChange={(e) => setDraft({ ...draft, base_url: e.target.value })} />
        </Field>
        <Field label="API key (kept in your system keychain, never in the library)">
          <input className="k-input" type="password" autoComplete="off" value={draft.api_key} onChange={(e) => setDraft({ ...draft, api_key: e.target.value })} />
        </Field>
        <ErrorLine error={error} />
        <div className="ka-row ka-row--end">
          <button type="button" className="k-btn" onClick={onClose}>Cancel</button>
          <button className="k-btn k-btn--dark" disabled={busy}>Add</button>
        </div>
      </form>
    </Dialog>
  )
}

function KeyDialog({ provider, onClose, onSaved }: { provider?: Provider; onClose: () => void; onSaved: () => void }) {
  const [key, setKey] = useState('')
  const [run, error, busy] = useAction()
  return (
    <Dialog open={!!provider} onClose={onClose} title={`${provider?.has_key ? 'Change the key for' : 'Add a key for'} ${provider?.name ?? ''}`}>
      <form
        className="ka-form"
        onSubmit={(e) => {
          e.preventDefault()
          run(async () => {
            await api(`/providers/${provider!.id}`, 'PATCH', { api_key: key })
            setKey('')
            onSaved()
            onClose()
          })
        }}
      >
        <Field label="API key (kept in your system keychain, never in the library)">
          <input className="k-input" type="password" autoComplete="off" autoFocus value={key} onChange={(e) => setKey(e.target.value)} />
        </Field>
        <ErrorLine error={error} />
        <div className="ka-row ka-row--end">
          <button type="button" className="k-btn" onClick={onClose}>Cancel</button>
          <button className="k-btn k-btn--dark" disabled={busy || !key}>Save the key</button>
        </div>
      </form>
    </Dialog>
  )
}

function JobEditor({ job, row, providers, onChange }: { job: Job; row: RoleRow; providers: Provider[]; onChange: () => void }) {
  const [run, error, busy] = useAction()
  const [providerId, setProviderId] = useState<number | null>(row.provider_id)
  const [model, setModel] = useState(row.model ?? '')
  const [kind, setKind] = useState<Kind>(row.kind)
  const [params, setParams] = useState(row.params)
  const [body, setBody] = useState(JSON.stringify(row.params.body ?? {}, null, 1))
  const [models, setModels] = useState<string[]>([])
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setModels([])
    if (providerId) api<{ models: string[] }>(`/providers/${providerId}/models`).then((r) => setModels(r.models), () => {})
  }, [providerId])

  const set = (key: string, value: unknown) => {
    setSaved(false)
    setParams((p) => {
      const next = { ...p }
      if (value === '' || value === undefined) delete next[key]
      else next[key] = value
      return next
    })
  }

  const save = () =>
    run(async () => {
      let parsed: unknown
      try {
        parsed = JSON.parse(body || '{}')
      } catch {
        throw new Error('What is sent with every request must be valid JSON.')
      }
      const own: Record<string, unknown> = { ...params, body: parsed }
      if (!Object.keys(parsed as object).length) delete own.body
      const inherit = !providerId || !model.trim()
      await api(`/roles/${job.role}`, 'PUT', { provider_id: inherit ? null : providerId, model: inherit ? null : model.trim(), kind, params: own })
      setSaved(true)
      onChange()
    })
  const probe = () => run(async () => { await api(`/roles/${job.role}/probe`, 'POST'); onChange() })

  const simple = job.role === 'embed' // a model and nothing else
  const shownKind = simple ? null : kind === 'auto' ? row.effective_kind : kind
  const sampler = Object.entries(SAMPLERS).find(([, v]) => JSON.stringify(v) === JSON.stringify(safeParse(body)))?.[0] ?? ''
  const inherited = row.inherited_from && !providerId

  return (
    <div className="ka-job">
      <div className="ka-row ka-row--gap">
        <Candy icon={job.icon} color={job.color} />
        <span className="ka-stack ka-stack--tight">
          <strong className="ka-job__name">{job.label}</strong>
          <span className="ka-muted ka-small">{job.short}</span>
        </span>
        {shownKind && <span className="ka-pill ka-push-right">{shownKind}</span>}
      </div>
      <span className="ka-muted ka-small">{job.help}</span>
      {inherited && <span className="ka-small">Now: same as {jobOf(row.inherited_from)?.label} ({row.effective_model}). Pick a server to give it its own.</span>}
      <div className="ka-grid2">
        <Field label="Server">
          <select className="k-select" value={providerId ?? ''} onChange={(e) => { setSaved(false); setProviderId(e.target.value ? Number(e.target.value) : null) }}>
            <option value="">{job.role === 'rp' ? 'Choose…' : simple ? 'Built-in' : `Same as ${jobOf(row.inherited_from ?? 'rp')?.label ?? 'Characters'}`}</option>
            {providers.map((p) => <option key={p.id} value={p.id}>{p.name}{isLocal(p.base_url) ? ' · this computer' : ''}</option>)}
          </select>
        </Field>
        <Field label="Model">
          <input className="k-input" list={`models-${job.role}`} value={model} disabled={!providerId} placeholder={providerId ? 'Type or pick a model' : ''} onChange={(e) => { setSaved(false); setModel(e.target.value) }} />
          <datalist id={`models-${job.role}`}>{models.map((m) => <option key={m} value={m} />)}</datalist>
        </Field>
        {!simple && (
          <>
            <Field label="Context size">
              <input className="k-input ka-mono-input" type="number" min={1024} step={1024} placeholder="8192" value={String(params.ctx_size ?? '')} onChange={(e) => set('ctx_size', e.target.value ? Number(e.target.value) : '')} />
            </Field>
            <div className="k-field">
              <span>Thinking</span>
              <Seg label="Thinking" value={String(params.thinking ?? 'default')} onChange={(v) => set('thinking', v === 'default' ? '' : v)}
                options={[['default', 'As the model likes'], ['enabled', 'On'], ['disabled', 'Off']]} />
            </div>
          </>
        )}
      </div>
      {!simple && (
        <div className="k-field">
          <span>Kind</span>
          <div className="ka-row ka-row--gap">
            <Seg label="Kind" value={kind} onChange={(v) => { setSaved(false); setKind(v) }}
              options={[['auto', 'Detect automatically'], ['standard', 'Standard'], ['reasoning', 'Reasoning']]} />
            <button type="button" className="k-btn k-btn--ghost k-btn--sm" disabled={busy || !row.effective_model} onClick={probe}>
              <Icon name="refresh" size={15} />
              Detect now
            </button>
            {row.detected_kind && <span className="ka-muted ka-small">found: {row.detected_kind}</span>}
          </div>
        </div>
      )}
      {shownKind === 'reasoning' && (
        <div className="ka-grid2">
          <Field label="Room to think (tokens)">
            <input className="k-input ka-mono-input" type="number" min={0} step={250} placeholder="1500" value={String(params.think_budget_tokens ?? '')} onChange={(e) => set('think_budget_tokens', e.target.value ? Number(e.target.value) : '')} />
          </Field>
          <Field label="Reasoning effort (APIs that support it)">
            <select className="k-select" value={String(params.reasoning_effort ?? '')} onChange={(e) => set('reasoning_effort', e.target.value)}>
              <option value="">Default</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </Field>
        </div>
      )}
      {(job.role === 'rp' || job.role === 'narrator') && (
        <>
          <div className="k-field">
            <span>Sampler</span>
            <Seg label="Sampler" value={sampler} onChange={(name) => { setSaved(false); setBody(JSON.stringify(SAMPLERS[name], null, 1)) }}
              options={Object.keys(SAMPLERS).map((n) => [n, n] as [string, string])} />
          </div>
          <Field label="Sent with every request (JSON)">
            <textarea className="ka-json" rows={4} spellCheck={false} value={body} onChange={(e) => { setSaved(false); setBody(e.target.value) }} />
          </Field>
        </>
      )}
      <ErrorLine error={error} />
      <span className="ka-row ka-row--gap">
        <button type="button" className="k-btn k-btn--dark" disabled={busy} onClick={save}>Save {job.label}</button>
        {saved && <span className="ka-muted ka-small">Saved.</span>}
      </span>
    </div>
  )
}

function safeParse(text: string): unknown {
  try {
    return JSON.parse(text || '{}')
  } catch {
    return null
  }
}
