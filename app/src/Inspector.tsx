import { useState } from 'react'
import { api, type Cast, type ContextLog, type Entity, type KnownMemory, type Run } from './api'
import { ErrorLine, useAction, useLoad } from './ui'

type Tab = 'memory' | 'context' | 'entities' | 'runs'

/** What the engine remembers, how it decided, and what it sent: the memory inspector. */
export default function Inspector({ storyId, cast, tick }: { storyId: number; cast: Cast | undefined; tick: number }) {
  const [tab, setTab] = useState<Tab>('memory')
  const tabs: [Tab, string][] = [['memory', 'Memory'], ['context', 'Prompt'], ['entities', 'Entities'], ['runs', 'Reading']]
  return (
    <section>
      <h3>Inspector</h3>
      <div className="tabs" role="tablist">
        {tabs.map(([t, label]) => (
          <button key={t} role="tab" aria-selected={tab === t} className={tab === t ? 'active' : ''} onClick={() => setTab(t)}>
            {label}
          </button>
        ))}
      </div>
      {tab === 'memory' && <Memories storyId={storyId} cast={cast} tick={tick} />}
      {tab === 'context' && <Prompt storyId={storyId} tick={tick} />}
      {tab === 'entities' && <Entities storyId={storyId} tick={tick} />}
      {tab === 'runs' && <Runs storyId={storyId} tick={tick} />}
    </section>
  )
}

function Memories({ storyId, cast, tick }: { storyId: number; cast: Cast | undefined; tick: number }) {
  const characters = cast?.entities.filter((e) => e.kind === 'character') ?? []
  const [knower, setKnower] = useState<number | null>(null)
  const who = knower ?? characters.find((c) => c.is_ai)?.id ?? characters[0]?.id ?? null
  const [memories, reload, error] = useLoad(
    () => (who ? api<KnownMemory[]>(`/stories/${storyId}/memories?knower=${who}`) : Promise.resolve([])),
    [storyId, who, tick],
  )
  const [run, actionError] = useAction()
  const patch = (id: number, body: object) => run(async () => { await api(`/memories/${id}`, 'PATCH', body); reload() })

  return (
    <div className="stack">
      <label>
        What does this character remember?
        <select value={who ?? ''} onChange={(e) => setKnower(Number(e.target.value))}>
          {characters.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </label>
      <small className="muted">
        Sharp: they recall the detail. Hazy: only the gist. Forgotten: nothing comes back unless something strongly
        reminds them. Shown as they would recall it right now with no reminder at all.
      </small>
      <ErrorLine error={error || actionError} />
      {memories?.length === 0 && <p className="muted">Nothing yet. Memory is read from the story every few turns.</p>}
      {memories?.map((m) => (
        <div key={m.memory_id} className="card" style={{ padding: '0.6rem 0.7rem', opacity: m.hidden ? 0.5 : 1 }}>
          <div className="row">
            <span className={`badge ${m.tier}`}>{m.tier}</span>
            <small>
              {m.source === 'told' ? `told by ${m.told_by ?? 'someone'}` : m.source}
              {m.belief < 0.7 && ' · doubted'} · importance {m.importance} · A {m.A.toFixed(2)}
            </small>
          </div>
          <p style={{ margin: '0.3em 0' }} title={m.detail}>{m.tier === 'sharp' ? m.detail : m.gist}</p>
          <div className="row">
            <button className="link" onClick={() => patch(m.memory_id, { pinned: !m.pinned })} title="Pinned facts sit in every prompt">
              {m.pinned ? 'Unpin' : 'Pin'}
            </button>
            <button className="link" onClick={() => patch(m.memory_id, { hidden: !m.hidden })}>{m.hidden ? 'Unhide' : 'Hide'}</button>
          </div>
        </div>
      ))}
      {cast && <AddMemory storyId={storyId} cast={cast} onAdded={reload} />}
    </div>
  )
}

function AddMemory({ storyId, cast, onAdded }: { storyId: number; cast: Cast; onAdded: () => void }) {
  const [run, error, busy] = useAction()
  const [detail, setDetail] = useState('')
  const [importance, setImportance] = useState(6)
  const [knowers, setKnowers] = useState<number[]>([])
  const [common, setCommon] = useState(false)
  const [pinned, setPinned] = useState(false)
  const characters = cast.entities.filter((e) => e.kind === 'character')
  return (
    <details>
      <summary>Write a memory</summary>
      <form
        className="stack"
        style={{ marginTop: '0.5rem' }}
        onSubmit={(e) => {
          e.preventDefault()
          run(async () => {
            await api(`/stories/${storyId}/memories`, 'POST', { detail, importance, knower_ids: knowers, common, pinned })
            setDetail('')
            onAdded()
          })
        }}
      >
        <textarea rows={3} required value={detail} placeholder="Mira owes the guild forty silver." onChange={(e) => setDetail(e.target.value)} />
        <label>Importance {importance}<input type="range" min={1} max={10} value={importance} onChange={(e) => setImportance(Number(e.target.value))} /></label>
        <label className="check"><input type="checkbox" checked={common} onChange={(e) => setCommon(e.target.checked)} />Everyone knows it</label>
        {!common && characters.map((c) => (
          <label key={c.id} className="check">
            <input type="checkbox" checked={knowers.includes(c.id)} onChange={() => setKnowers((k) => (k.includes(c.id) ? k.filter((x) => x !== c.id) : [...k, c.id]))} />
            {c.name} knows
          </label>
        ))}
        <label className="check"><input type="checkbox" checked={pinned} onChange={(e) => setPinned(e.target.checked)} />Keep it in every prompt</label>
        <button className="primary" disabled={busy}>Remember</button>
        <ErrorLine error={error} />
      </form>
    </details>
  )
}

function Prompt({ storyId, tick }: { storyId: number; tick: number }) {
  const [log, , error] = useLoad(() => api<ContextLog>(`/stories/${storyId}/context`), [storyId, tick])
  if (error) return <p className="muted">No prompt yet. Take a turn first.</p>
  if (!log) return null
  return (
    <div className="stack">
      <small>
        Estimated {log.est_tokens.toLocaleString()} of {log.budget.toLocaleString()} tokens
        {log.actual_tokens != null && `, the model counted ${log.actual_tokens.toLocaleString()}`}
        {log.cached_tokens != null && `, ${log.cached_tokens.toLocaleString()} reused from its cache`}.
      </small>
      <table>
        <thead><tr><th>Part</th><th>Tokens</th><th /></tr></thead>
        <tbody>
          {log.sections.map((s) => (
            <tr key={s.name}>
              <td>{s.name}{s.evicted > 0 && <small> ({s.evicted} cut)</small>}</td>
              <td>{s.tokens} / {s.cap}</td>
              <td style={{ width: '40%' }}>
                <div className="bar"><span className={s.tokens > s.cap ? 'over' : ''} style={{ width: `${Math.min(100, (100 * s.tokens) / Math.max(s.cap, 1))}%` }} /></div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {log.memories.length > 0 && (
        <table>
          <thead><tr><th>Memory</th><th>Tier</th><th>Shown as</th><th>A</th><th>B</th><th>S</th><th>G</th></tr></thead>
          <tbody>
            {log.memories.map((m) => (
              <tr key={String(m.memory_id)}>
                <td>M{String(m.memory_id)}</td>
                <td><span className={`badge ${m.tier}`}>{String(m.tier)}</span></td>
                <td>{String(m.rendered)}</td>
                <td>{String(m.A ?? '')}</td>
                <td>{String(m.B ?? '')}</td>
                <td>{String(m.S ?? '')}</td>
                <td>{String(m.G ?? '')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {log.prompt?.map((p, i) => (
        <details key={i}>
          <summary>{p.role} · {p.content.length.toLocaleString()} characters</summary>
          <pre>{p.content}</pre>
        </details>
      ))}
    </div>
  )
}

function Entities({ storyId, tick }: { storyId: number; tick: number }) {
  const [entities, reload, error] = useLoad(() => api<Entity[]>(`/stories/${storyId}/entities`), [storyId, tick])
  const [run, actionError, busy] = useAction()
  const [keep, setKeep] = useState<number | ''>('')
  const [drop, setDrop] = useState<number | ''>('')
  const shown = entities?.filter((e) => !e.hidden) ?? []
  return (
    <div className="stack">
      <ErrorLine error={error || actionError} />
      {shown.map((e) => {
        const current = new Map(e.flags.map((f) => [f.key, f]))
        return (
          <div key={e.id} className="card" style={{ padding: '0.6rem 0.7rem' }}>
            <div className="row">
              <strong>{e.name}</strong>
              <span className="badge">{e.kind}</span>
              {e.run_id && <span className="badge" title="Found by reading the story">found</span>}
            </div>
            {e.aliases.filter((a) => a !== e.name).length > 0 && <small>also: {e.aliases.filter((a) => a !== e.name).join(', ')}</small>}
            {[...current.values()].filter((f) => f.value).map((f) => (
              <div key={f.key}><small>{f.key}: {f.value}{f.private ? ' (private)' : ''}</small></div>
            ))}
          </div>
        )
      })}
      <details>
        <summary>These two are the same</summary>
        <div className="stack" style={{ marginTop: '0.5rem' }}>
          <select value={keep} onChange={(e) => setKeep(Number(e.target.value))}>
            <option value="">Keep…</option>
            {shown.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
          </select>
          <select value={drop} onChange={(e) => setDrop(Number(e.target.value))}>
            <option value="">…and fold in</option>
            {shown.filter((e) => e.id !== keep).map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
          </select>
          <button
            disabled={busy || !keep || !drop}
            onClick={() => run(async () => { await api('/entities/merge', 'POST', { keep, drop }); setDrop(''); reload() })}
          >
            Merge
          </button>
        </div>
      </details>
    </div>
  )
}

function Runs({ storyId, tick }: { storyId: number; tick: number }) {
  const [runs, reload, error] = useLoad(() => api<Run[]>(`/stories/${storyId}/runs`), [storyId, tick])
  const [run, actionError, busy] = useAction()
  return (
    <div className="stack">
      <small className="muted">
        The memory reader goes through the story every few turns, when a scene ends, and after a time skip, while you
        read. Nothing here slows down replies.
      </small>
      <div className="row">
        <button disabled={busy} onClick={() => run(async () => { await api(`/stories/${storyId}/extract`, 'POST'); reload() })}>
          Read what is waiting now
        </button>
      </div>
      <ErrorLine error={error || actionError} />
      {runs?.map((r) => (
        <div key={r.id} className="card" style={{ padding: '0.6rem 0.7rem' }}>
          <div className="row">
            <span className={`badge ${r.status === 'ok' ? 'sharp' : r.status === 'failed' ? '' : 'hazy'}`}>{r.status}</span>
            <small>{r.trigger} · {r.role ?? '?'} · {r.model ?? '?'}{r.attempts > 1 && ` · try ${r.attempts}`}</small>
            {r.stale ? <span className="badge hazy" title="A line it read was edited">stale</span> : null}
            <span className="spacer" />
            <button className="link" disabled={busy} onClick={() => run(async () => { await api(`/runs/${r.id}/reread`, 'POST', { role: 'reasoning' }); reload() })}>
              Read again carefully
            </button>
          </div>
          {r.error && <small className="error">{r.error}</small>}
          {r.warnings.length > 0 && (
            <details>
              <summary>{r.warnings.length} item{r.warnings.length === 1 ? '' : 's'} skipped</summary>
              <pre>{r.warnings.join('\n')}</pre>
            </details>
          )}
        </div>
      ))}
    </div>
  )
}
