import { useEffect, useState } from 'react'
import { api, type Kind, type Provider, type RoleRow } from './api'
import { ErrorLine, useAction, useLoad } from './ui'

const PRESETS = [
  { name: 'OpenRouter', base_url: 'https://openrouter.ai/api/v1', key: true },
  { name: 'HuggingFace', base_url: 'https://router.huggingface.co/v1', key: true },
  { name: 'llama.cpp', base_url: 'http://127.0.0.1:8080/v1', key: false },
  { name: 'Ollama', base_url: 'http://127.0.0.1:11434/v1', key: false },
  { name: 'LM Studio', base_url: 'http://127.0.0.1:1234/v1', key: false },
]

const TEXT_ROLES: { role: string; label: string; help: string }[] = [
  { role: 'rp', label: 'Characters', help: 'Every character reply. A standard (non-reasoning) model keeps replies fast.' },
  { role: 'narrator', label: 'Narrator', help: 'Narration and scene description. Empty: uses Characters.' },
  { role: 'utility', label: 'Memory reader', help: 'Reads the story into memory every few turns, at temperature 0. A small fast model is ideal.' },
  { role: 'reasoning', label: 'Reasoning', help: 'Careful re-reads when a scene closes, and on request. A reasoning model shines here.' },
]

const SAMPLERS: Record<string, Record<string, number>> = {
  Balanced: { temperature: 1.0, min_p: 0.05 },
  'Balanced + DRY (llama.cpp, KoboldCpp)': {
    temperature: 1.0, min_p: 0.05, dry_multiplier: 0.8, dry_base: 1.75, dry_allowed_length: 2,
  },
  'Creative + XTC (llama.cpp, KoboldCpp)': {
    temperature: 1.0, min_p: 0.05, dry_multiplier: 0.8, dry_base: 1.75, dry_allowed_length: 2,
    xtc_threshold: 0.1, xtc_probability: 0.5,
  },
  Focused: { temperature: 0.7, min_p: 0.1 },
}

export default function Models() {
  const [providers, reloadProviders, providerError] = useLoad(() => api<Provider[]>('/providers'), [])
  const [roles, reloadRoles, roleError] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const reloadAll = () => {
    reloadProviders()
    reloadRoles()
  }
  return (
    <div className="stack" style={{ maxWidth: 980 }}>
      <h1>Models</h1>
      <p className="muted">
        Kataki ships no models. Connect a model server or an API, then choose a model for each job. A job left empty
        uses the one it inherits from, so one model is enough to start.
      </p>
      <ErrorLine error={providerError || roleError} />
      <Providers providers={providers ?? []} roles={roles ?? []} onChange={reloadAll} />
      <section className="stack">
        <h2>Jobs</h2>
        {roles &&
          TEXT_ROLES.map((r) => (
            <RoleEditor
              key={r.role}
              meta={r}
              row={roles.find((x) => x.role === r.role)!}
              providers={providers ?? []}
              onChange={reloadRoles}
            />
          ))}
        <p className="muted">Embeddings, images and music get their own slots in later milestones.</p>
      </section>
    </div>
  )
}

function Providers({ providers, roles, onChange }: { providers: Provider[]; roles: RoleRow[]; onChange: () => void }) {
  const [run, error, busy] = useAction()
  const [found, setFound] = useState<{ name: string; base_url: string; models: string[] }[] | null>(null)
  const [draft, setDraft] = useState({ name: '', base_url: '', api_key: '' })
  const [tested, setTested] = useState<Record<number, string>>({})
  const rpEmpty = !roles.find((r) => r.role === 'rp')?.model

  const add = (name: string, base_url: string, api_key: string, firstModel?: string) =>
    run(async () => {
      const p = await api<Provider>('/providers', 'POST', { name, base_url, api_key: api_key || null })
      if (rpEmpty && firstModel) await api('/roles/rp', 'PUT', { provider_id: p.id, model: firstModel })
      setDraft({ name: '', base_url: '', api_key: '' })
      onChange()
    })

  const test = (p: Provider) =>
    run(async () => {
      try {
        const { models } = await api<{ models: string[] }>(`/providers/${p.id}/models`)
        setTested((t) => ({ ...t, [p.id]: `${models.length} model${models.length === 1 ? '' : 's'} available` }))
      } catch (e) {
        setTested((t) => ({ ...t, [p.id]: (e as Error).message }))
      }
    })

  return (
    <section className="card stack">
      <h2>Model servers and APIs</h2>
      {providers.length === 0 && (
        <p>
          Nothing connected yet. If a model server is already running on this computer (llama.cpp, Ollama, LM Studio,
          KoboldCpp), look for it; otherwise add an API below.
        </p>
      )}
      {providers.map((p) => (
        <div key={p.id} className="row">
          <strong>{p.name}</strong>
          <small>{p.base_url}</small>
          {p.has_key && <span className="badge">key stored</span>}
          <span className="spacer" />
          <small>{tested[p.id]}</small>
          <button onClick={() => test(p)} disabled={busy}>Test</button>
          <button
            className="danger"
            onClick={() => run(async () => { await api(`/providers/${p.id}`, 'DELETE'); onChange() })}
          >
            Remove
          </button>
        </div>
      ))}
      <div className="row">
        <button onClick={() => run(async () => setFound(await api('/providers/detect')))} disabled={busy}>
          Look for model servers on this computer
        </button>
        {found && !found.length && <small>None found. Is the server running?</small>}
      </div>
      {found?.map((f) => (
        <div key={f.base_url} className="row">
          <strong>{f.name}</strong>
          <small>{f.base_url} · {f.models.length} model(s): {f.models.slice(0, 3).join(', ')}</small>
          <span className="spacer" />
          <button className="primary" onClick={() => add(f.name, f.base_url, '', f.models[0])} disabled={busy}>
            Add{rpEmpty && f.models[0] ? ' and use it' : ''}
          </button>
        </div>
      ))}
      <h3>Add an API</h3>
      <div className="row">
        {PRESETS.map((p) => (
          <button key={p.name} className="link" onClick={() => setDraft({ ...draft, name: p.name, base_url: p.base_url })}>
            {p.name}
          </button>
        ))}
      </div>
      <form
        className="grid2"
        onSubmit={(e) => {
          e.preventDefault()
          add(draft.name, draft.base_url, draft.api_key)
        }}
      >
        <label>Name<input value={draft.name} required onChange={(e) => setDraft({ ...draft, name: e.target.value })} /></label>
        <label>Base URL (OpenAI-compatible)
          <input value={draft.base_url} required placeholder="https://…/v1" onChange={(e) => setDraft({ ...draft, base_url: e.target.value })} />
        </label>
        <label>API key (stored in your system keychain, never in the library)
          <input type="password" value={draft.api_key} autoComplete="off" onChange={(e) => setDraft({ ...draft, api_key: e.target.value })} />
        </label>
        <div className="row" style={{ alignSelf: 'end' }}>
          <button className="primary" disabled={busy}>Add</button>
        </div>
      </form>
      <ErrorLine error={error} />
    </section>
  )
}

function RoleEditor({
  meta,
  row,
  providers,
  onChange,
}: {
  meta: { role: string; label: string; help: string }
  row: RoleRow
  providers: Provider[]
  onChange: () => void
}) {
  const [run, error, busy] = useAction()
  const [providerId, setProviderId] = useState<number | null>(row.provider_id)
  const [model, setModel] = useState(row.model ?? '')
  const [kind, setKind] = useState<Kind>(row.kind)
  const [params, setParams] = useState(row.params)
  const [body, setBody] = useState(JSON.stringify(row.params.body ?? {}, null, 1))
  const [models, setModels] = useState<string[]>([])

  useEffect(() => {
    setModels([])
    if (providerId) api<{ models: string[] }>(`/providers/${providerId}/models`).then((r) => setModels(r.models), () => {})
  }, [providerId])

  const set = (key: string, value: unknown) =>
    setParams((p) => {
      const next = { ...p }
      if (value === '' || value === undefined) delete next[key]
      else next[key] = value
      return next
    })

  const save = () =>
    run(async () => {
      let parsed: unknown
      try {
        parsed = JSON.parse(body || '{}')
      } catch {
        throw new Error('The request JSON is not valid JSON.')
      }
      const own = { ...params, body: parsed }
      if (!Object.keys(parsed as object).length) delete (own as Record<string, unknown>).body
      const inherit = !providerId || !model.trim()
      await api(`/roles/${meta.role}`, 'PUT', {
        provider_id: inherit ? null : providerId,
        model: inherit ? null : model.trim(),
        kind,
        params: own,
      })
      onChange()
    })

  const probe = () => run(async () => { await api(`/roles/${meta.role}/probe`, 'POST'); onChange() })
  const shownKind = kind === 'auto' ? row.effective_kind : kind

  return (
    <div className="card stack">
      <div className="row">
        <h2 style={{ margin: 0 }}>{meta.label}</h2>
        {shownKind && <span className={`badge ${shownKind}`}>{shownKind}</span>}
        <span className="spacer" />
        <small>
          {row.effective_model
            ? `${row.inherited_from ? `same as ${TEXT_ROLES.find((r) => r.role === row.inherited_from)?.label ?? row.inherited_from}: ` : ''}${row.effective_model}`
            : 'no model yet'}
        </small>
      </div>
      <p className="muted" style={{ margin: 0 }}>{meta.help}</p>
      <div className="grid2">
        <label>Server
          <select value={providerId ?? ''} onChange={(e) => setProviderId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">{meta.role === 'rp' ? 'Choose…' : 'Inherit'}</option>
            {providers.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </label>
        <label>Model
          <input list={`models-${meta.role}`} value={model} disabled={!providerId} placeholder={providerId ? 'Type or pick a model' : ''} onChange={(e) => setModel(e.target.value)} />
          <datalist id={`models-${meta.role}`}>{models.map((m) => <option key={m} value={m} />)}</datalist>
        </label>
        <label>Kind
          <div className="row">
            <select value={kind} onChange={(e) => setKind(e.target.value as Kind)}>
              <option value="auto">Detect automatically{row.detected_kind ? ` (${row.detected_kind})` : ''}</option>
              <option value="standard">Standard</option>
              <option value="reasoning">Reasoning</option>
            </select>
            <button type="button" onClick={probe} disabled={busy || !row.effective_model}>Detect now</button>
          </div>
        </label>
        <label>Context size (tokens)
          <input type="number" min={1024} step={1024} value={String(params.ctx_size ?? '')} placeholder="8192" onChange={(e) => set('ctx_size', e.target.value ? Number(e.target.value) : '')} />
        </label>
        {shownKind === 'reasoning' && (
          <>
            <label>Thinking
              <select value={String(params.thinking ?? 'default')} onChange={(e) => set('thinking', e.target.value === 'default' ? '' : e.target.value)}>
                <option value="default">As the model likes</option>
                <option value="enabled">On</option>
                <option value="disabled">Off (faster)</option>
              </select>
            </label>
            <label>Room to think (tokens)
              <input type="number" min={0} step={250} value={String(params.think_budget_tokens ?? '')} placeholder="1500" onChange={(e) => set('think_budget_tokens', e.target.value ? Number(e.target.value) : '')} />
            </label>
            <label>Reasoning effort (APIs that support it)
              <select value={String(params.reasoning_effort ?? '')} onChange={(e) => set('reasoning_effort', e.target.value)}>
                <option value="">Default</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </label>
          </>
        )}
      </div>
      {meta.role !== 'utility' && meta.role !== 'reasoning' && (
        <details>
          <summary>Samplers and extra request fields</summary>
          <div className="stack" style={{ marginTop: '0.5rem' }}>
            <div className="row">
              {Object.entries(SAMPLERS).map(([name, values]) => (
                <button key={name} type="button" className="link" onClick={() => setBody(JSON.stringify(values, null, 1))}>{name}</button>
              ))}
            </div>
            <label>Sent with every request, exactly as written
              <textarea rows={4} spellCheck={false} value={body} onChange={(e) => setBody(e.target.value)} />
            </label>
          </div>
        </details>
      )}
      <div className="row">
        <button className="primary" onClick={save} disabled={busy}>Save</button>
        <ErrorLine error={error} />
      </div>
    </div>
  )
}
