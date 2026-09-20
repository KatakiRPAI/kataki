import { useState, type CSSProperties } from 'react'
import { api, type Cast, type ContextLog, type Entity, type KnownMemory, type Run, type Story, type Version } from '../api'
import { Avatar, pronounsOf } from '../art'
import { useAction, useLibrary, useLoad } from '../hooks'
import { Dialog, ErrorLine, Icon } from '../ui'

type Tier = 'sharp' | 'hazy' | 'forgotten'
type StoryMemory = { id: number; detail: string; gist: string; pinned: number; knowers: number[] }

/** The engine's clock label (clock.label): "Day 3, 14:20" or "Year 7, Day 1, 09:30". */
function clockLabel(storyTime: number, epoch: number) {
  const total = storyTime + epoch
  const days = Math.floor(total / 1440)
  const minute = total % 1440
  const time = `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`
  const years = Math.floor(days / 365)
  const clock = `Day ${(days % 365) + 1}, ${time}`
  return years ? `Year ${years + 1}, ${clock}` : clock
}

const n = (x: number) => x.toLocaleString('en')

/** Backstage: what each character remembers, the last prompt, the cast as the memory reader sees
 *  it, and the reads themselves. `tick` moves when the story's version does. */
export default function Backstage({ story, cast, tick, focus, onChange }: { story: Story; cast: Cast; tick: number; focus?: number; onChange: () => void }) {
  return (
    <div className="k-backstage ka-backstage">
      <Memory story={story} cast={cast} tick={tick} focus={focus} />
      <div className="ka-backstage__side">
        <Prompt story={story} tick={tick} />
        <CastPanel story={story} tick={tick} onChange={onChange} />
        <Reading story={story} tick={tick} />
      </div>
    </div>
  )
}

function Memory({ story, cast, tick, focus }: { story: Story; cast: Cast; tick: number; focus?: number }) {
  const { byId } = useLibrary()
  const people = cast.entities.filter((e) => e.kind === 'character').sort((a, b) => Number(a.persona) - Number(b.persona))
  const [picked, setPicked] = useState<number | undefined>(focus) // the peek card opens on its character
  const who = people.find((e) => e.id === picked) ?? people[0]
  const [tier, setTier] = useState<Tier | 'all'>('all')
  const [memories, reload, error] = useLoad(
    () => (who ? api<KnownMemory[]>(`/stories/${story.id}/memories?knower=${who.id}`) : Promise.resolve([])),
    [story.id, who?.id, tick],
  )
  const [run, actionError, busy] = useAction()
  const patch = (id: number, body: object) =>
    run(async () => {
      await api(`/memories/${id}`, 'PATCH', body)
      reload()
    })
  const item = (e?: { lib_item_id: number | null }) => (e?.lib_item_id ? byId.get(e.lib_item_id) : undefined)
  const [she, learned] = { she: ['she', 'SHE'], he: ['he', 'HE'], they: ['they', 'THEY'] }[pronounsOf(item(who))]
  const all = memories ?? []
  const count = (t: Tier) => all.filter((m) => m.tier === t).length
  const shown = tier === 'all' ? all : all.filter((m) => m.tier === tier)
  return (
    <section className="k-bs-panel ka-bs-memory" aria-label="Memory">
      <div className="k-bs-title">
        <span>MEMORY</span>
        <span className="ka-bs-muted">As each memory would come back if it came up now.</span>
      </div>
      <div className="ka-bs-bar">
        <div className="ka-bs-group" role="tablist" aria-label="Whose memory">
          {people.map((e, i) => (
            <button key={e.id} type="button" className="k-bs-btn ka-bs-person" role="tab"
              id={`bs-tab-${e.id}`} aria-selected={e.id === who?.id} aria-controls="bs-memory"
              tabIndex={e.id === who?.id ? 0 : -1}
              onKeyDown={(k) => {
                const step = k.key === 'ArrowRight' ? 1 : k.key === 'ArrowLeft' ? -1 : 0
                if (!step) return
                const next = people[(i + step + people.length) % people.length]
                setPicked(next.id)
                document.getElementById(`bs-tab-${next.id}`)?.focus()
              }}
              onClick={() => setPicked(e.id)}>
              <Avatar item={item(e)} name={e.name} size={24} />
              {e.name}
            </button>
          ))}
        </div>
        <div className="ka-bs-group" role="group" aria-label="Clarity">
          {(['all', 'sharp', 'hazy', 'forgotten'] as const).map((t) => (
            <button key={t} type="button" className="k-bs-btn" aria-pressed={tier === t} onClick={() => setTier(t)}>
              {t} {t === 'all' ? all.length : count(t)}
            </button>
          ))}
        </div>
      </div>
      <div className="k-bs-row ka-bs-head" aria-hidden="true">
        <span>TIER</span>
        <span>MEMORY · STORY TIME</span>
        <span>HOW {learned} LEARNED IT</span>
        <span>WEIGHT</span>
        <span />
      </div>
      <div className="ka-bs-scroll" id="bs-memory" role="tabpanel" aria-labelledby={who ? `bs-tab-${who.id}` : undefined}>
        {shown.map((m) => (
          <div key={m.memory_id} className={`k-bs-row${m.hidden ? ' is-hidden' : ''}`}>
            <span className={`k-bs-tier k-bs-tier--${m.tier}`}>{m.tier}</span>
            <span className="ka-bs-text">
              <span className={m.tier === 'forgotten' ? 'ka-bs-dim' : undefined}>{m.tier === 'hazy' ? m.gist : m.detail}</span>
              {m.tier === 'hazy' && <s className="ka-bs-was">was sharp: {m.detail}</s>}
              <span className="ka-bs-time">{clockLabel(m.story_time, story.epoch_offset_min)}</span>
            </span>
            <span className="ka-bs-how">
              {m.source === 'told' ? `told by ${m.told_by ?? 'someone'}` : m.source}
              {m.tier !== 'forgotten' && (
                <>
                  <br />
                  {m.belief < 0.7 && <span className="ka-bs-doubt">doubted · </span>}
                  recall {m.A.toFixed(2)}
                </>
              )}
            </span>
            <span className="ka-bs-weight">
              <span className="k-importance" aria-hidden="true">
                {Array.from({ length: 10 }, (_, i) => <i key={i} className={i < m.importance ? 'on' : undefined} />)}
              </span>
              importance {m.importance}
            </span>
            <span className="ka-bs-acts">
              <button type="button" className="k-bs-btn ka-bs-icon" aria-label={m.pinned ? 'Unpin' : 'Pin'} aria-pressed={!!m.pinned}
                disabled={busy} onClick={() => patch(m.memory_id, { pinned: !m.pinned })}>
                <Icon name="pushpin" size={14} />
              </button>
              <button type="button" className="k-bs-btn ka-bs-icon" aria-label={m.hidden ? 'Unhide' : 'Hide'} aria-pressed={!!m.hidden}
                disabled={busy} onClick={() => patch(m.memory_id, { hidden: !m.hidden })}>
                <Icon name={m.hidden ? 'eye' : 'eyeoff'} size={14} />
              </button>
            </span>
          </div>
        ))}
        {memories && !shown.length && (
          <p className="ka-bs-empty">{all.length ? `Nothing ${tier} here.` : 'Nothing yet. Memory is read from the story every few turns.'}</p>
        )}
      </div>
      <div className="ka-bs-foot">
        <Icon name="pushpin" size={13} />
        Pinned facts sit in every prompt.
        <ErrorLine error={error || actionError} />
      </div>
      <WriteMemory story={story} cast={cast} knower={who?.id} she={she} onSaved={reload} />
    </section>
  )
}

function WriteMemory({ story, cast, knower, she, onSaved }: { story: Story; cast: Cast; knower?: number; she: string; onSaved: () => void }) {
  const [run, error, busy] = useAction()
  const [detail, setDetail] = useState('')
  const [importance, setImportance] = useState(5)
  const [who, setWho] = useState<string>('')
  const [pinned, setPinned] = useState(false)
  const target = who || String(knower ?? 'common')
  const people = cast.entities.filter((e) => e.kind === 'character')
  const save = () =>
    run(async () => {
      const common = target === 'common'
      await api(`/stories/${story.id}/memories`, 'POST', { detail: detail.trim(), importance, knower_ids: common ? [] : [Number(target)], common, pinned })
      setDetail('')
      onSaved()
    })
  return (
    <form className="ka-bs-write" onSubmit={(e) => { e.preventDefault(); if (detail.trim()) save() }}>
      <span className="ka-bs-label">WRITE A MEMORY</span>
      <label className="ka-bs-field">
        <span className="k-sr">Memory text</span>
        <input value={detail} placeholder={`What does ${she} know?`} onChange={(e) => setDetail(e.target.value)} />
      </label>
      <div className="ka-bs-line">
        <label className="ka-bs-inline">
          importance
          <input type="range" min={1} max={10} value={importance} onChange={(e) => setImportance(Number(e.target.value))} />
          {importance}
        </label>
        <label className="ka-bs-inline">
          who knows
          <select value={target} onChange={(e) => setWho(e.target.value)}>
            {people.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
            <option value="common">Everyone knows it</option>
          </select>
        </label>
        <label className="ka-bs-inline">
          <input type="checkbox" checked={pinned} onChange={(e) => setPinned(e.target.checked)} />
          keep it in every prompt
        </label>
        <button type="submit" className="k-bs-btn k-bs-btn--primary ka-bs-save" disabled={busy || !detail.trim()}>
          <Icon name="plus" size={13} />
          Save memory
        </button>
      </div>
      <ErrorLine error={error} />
    </form>
  )
}

const PARTS = ['rules', 'cards', 'memory', 'examples', 'history', 'tail']

function Prompt({ story, tick }: { story: Story; tick: number }) {
  const [log, , error] = useLoad(() => api<ContextLog>(`/stories/${story.id}/context`), [story.id, tick])
  const [everything] = useLoad(() => api<StoryMemory[]>(`/stories/${story.id}/memories`), [story.id, tick])
  const [full, setFull] = useState(false)
  const text = new Map((everything ?? []).map((m) => [m.id, m]))
  const recalled = log?.memories.filter((m) => m.rendered !== 'dropped') ?? []
  const dropped = log?.memories.filter((m) => m.rendered === 'dropped') ?? []
  const evicted = log?.sections.filter((s) => s.evicted > 0) ?? []
  const short = (id: number) => {
    const m = text.get(id)
    const words = (m?.gist || m?.detail || `memory ${id}`).replace(/[.!?]$/, '')
    return words.length > 30 ? `${words.slice(0, 28)}…` : words
  }
  const cut = [
    ...evicted.map((s) => `${s.evicted} ${s.name === 'history' ? 'old lines' : s.name}`),
    ...(dropped.length ? [`${dropped.length} ${dropped.length === 1 ? 'memory' : 'memories'} (no room)`] : []),
  ]
  return (
    <section className="k-bs-panel ka-bs-prompt" aria-label="Prompt">
      <div className="k-bs-title">
        <span>PROMPT</span>
        <button type="button" className="k-bs-btn" disabled={!log?.prompt} onClick={() => setFull(true)}>
          <Icon name="eye" size={13} />
          full prompt
        </button>
      </div>
      {error || !log ? (
        <p className="ka-bs-empty">{error ? 'No prompt yet. Take a turn first.' : ''}</p>
      ) : (
        <div className="ka-bs-body">
          <div className="ka-bs-between">
            <span>~{n(log.est_tokens)} / {n(log.budget)} tokens</span>
            <span className="ka-bs-muted">
              {log.actual_tokens != null && `counted ${n(log.actual_tokens)}`}
              {log.actual_tokens != null && log.cached_tokens != null && ` · cache reuse ${Math.round((100 * log.cached_tokens) / Math.max(1, log.actual_tokens))}%`}
            </span>
          </div>
          <div className="k-tokenbar" role="img" aria-label={log.sections.map((s) => `${s.name} ${s.tokens}`).join(', ')}>
            {log.sections.map((s) => (
              <span key={s.name} style={{ width: `${(100 * s.tokens) / Math.max(1, log.budget)}%`, background: `var(--k-bs-part-${PARTS.includes(s.name) ? s.name : 'rules'})` }} />
            ))}
          </div>
          <div className="ka-bs-legend">
            {log.sections.map((s) => (
              <span key={s.name} className={s.tokens > s.cap ? 'is-over' : undefined}>
                <i style={{ '--part': `var(--k-bs-part-${PARTS.includes(s.name) ? s.name : 'rules'})` } as CSSProperties} />
                {s.name} {n(s.tokens)} <span className="ka-bs-muted">/ {n(s.cap)}</span>
              </span>
            ))}
          </div>
          <p className="ka-bs-note">
            recalled {recalled.length}
            {recalled.map((m) => ` · ${m.A.toFixed(2)} ${short(m.memory_id)}${text.get(m.memory_id)?.pinned ? ' (pinned)' : ''}`).join('')}
            <br />
            cut: {cut.length ? cut.join(' · ') : 'nothing'}
          </p>
        </div>
      )}
      <Dialog open={full} onClose={() => setFull(false)} title="The full prompt" className="ka-bs-dialog">
        {log?.prompt?.map((p, i) => (
          <details key={i} open={i === log.prompt!.length - 1}>
            <summary>{p.role} · {n(p.content.length)} characters</summary>
            <pre>{p.content}</pre>
          </details>
        ))}
      </Dialog>
    </section>
  )
}

const KIND_ICON: Record<string, string> = { place: 'map-pin', item: 'key', faction: 'shield', other: 'help' }

function CastPanel({ story, tick, onChange }: { story: Story; tick: number; onChange: () => void }) {
  const { byId } = useLibrary()
  const [entities, reload, error] = useLoad(() => api<Entity[]>(`/stories/${story.id}/entities`), [story.id, tick])
  const [merging, setMerging] = useState(false)
  const shown = entities?.filter((e) => !e.hidden) ?? []
  return (
    <section className="k-bs-panel ka-bs-cast" aria-label="Cast">
      <div className="k-bs-title">
        <span>CAST</span>
        <button type="button" className="k-bs-btn" disabled={shown.length < 2} onClick={() => setMerging(true)}>
          <Icon name="merge" size={13} />
          these two are the same
        </button>
      </div>
      <div className="ka-bs-scroll">
        {shown.map((e) => {
          const latest = new Map(e.flags.map((f) => [f.key, f])) // later rows win: the current value
          const flags = [...latest.values()].filter((f) => f.value).map((f) => `${f.key}: ${f.value}`)
          const also = e.aliases.filter((a) => a !== e.name)
          const lib = e.lib_item_id
          return (
            <div key={e.id} className="ka-bs-entity">
              {e.kind === 'character' ? <Avatar item={lib ? byId.get(lib) : undefined} name={e.name} size={24} /> : <Icon name={KIND_ICON[e.kind] ?? 'help'} size={18} />}
              <span className="ka-bs-name">{e.name}</span>
              <span className="ka-bs-muted">{e.id === story.persona?.id ? 'persona' : e.kind}</span>
              <span className="ka-bs-flags">
                {flags.join(' · ') || <span className="ka-bs-muted">{e.summary.split('\n')[0] || '—'}</span>}
                {also.length > 0 && <span className="ka-bs-muted"> · also {also.join(', ')}</span>}
              </span>
              {e.run_id ? <span className="ka-bs-found" title="Found by reading the story">found</span> : <span />}
            </div>
          )
        })}
      </div>
      <ErrorLine error={error} />
      <Dialog open={merging} onClose={() => setMerging(false)} title="These two are the same" className="ka-bs-dialog">
        <Merge entities={shown} onDone={() => { setMerging(false); reload(); onChange() }} />
      </Dialog>
    </section>
  )
}

// mounted fresh each time the dialog opens
function Merge({ entities, onDone }: { entities: Entity[]; onDone: () => void }) {
  const [run, error, busy] = useAction()
  const [keep, setKeep] = useState<number>()
  const [drop, setDrop] = useState<number>()
  return (
    <form className="ka-stack" onSubmit={(e) => {
      e.preventDefault()
      if (keep && drop) run(async () => { await api('/entities/merge', 'POST', { keep, drop }); onDone() })
    }}>
      <p className="ka-muted">Everything known about the second moves to the first, and its name becomes another name for them.</p>
      <label className="ka-bs-inline">
        keep
        <select value={keep ?? ''} onChange={(e) => setKeep(Number(e.target.value) || undefined)}>
          <option value="">choose…</option>
          {entities.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
        </select>
      </label>
      <label className="ka-bs-inline">
        fold in
        <select value={drop ?? ''} onChange={(e) => setDrop(Number(e.target.value) || undefined)}>
          <option value="">choose…</option>
          {entities.filter((e) => e.id !== keep).map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
        </select>
      </label>
      <ErrorLine error={error} />
      <div className="ka-row ka-row--end">
        <button type="submit" className="k-bs-btn k-bs-btn--primary" disabled={busy || !keep || !drop}>
          <Icon name="merge" size={13} />
          Merge
        </button>
      </div>
    </form>
  )
}

const TRIGGERS: Record<string, string> = {
  cadence: 'every few turns',
  scene: 'the scene ended',
  skip: 'after a time skip',
  evict: 'lines leaving the window',
  manual: 'you asked',
}
const STATUS: Record<string, string> = { ok: 'done', failed: 'failed', pending: 'waiting', running: 'reading', cancelled: 'stopped' }

function Reading({ story, tick }: { story: Story; tick: number }) {
  const [runs, reload, error] = useLoad(() => api<Run[]>(`/stories/${story.id}/runs`), [story.id, tick])
  const [version, reloadVersion] = useLoad(() => api<Version>(`/stories/${story.id}/version`), [story.id, tick])
  const [run, actionError, busy] = useAction()
  const [picked, setPicked] = useState<number>()
  const chosen = runs?.find((r) => r.id === picked) ?? runs?.[0]
  const latest = runs?.[0]
  const act = (fn: () => Promise<unknown>) =>
    run(async () => {
      await fn()
      reload()
      reloadVersion()
    })
  return (
    <section className="k-bs-panel ka-bs-reading" aria-label="Reading">
      <div className="k-bs-title">
        <span>READING</span>
        <span className="ka-bs-muted">{latest ? `memory reader · ${latest.model ?? latest.role ?? '?'}` : 'memory reader'}</span>
      </div>
      <div className="ka-bs-scroll">
        {!!version?.waiting && (
          <div className="ka-bs-run">
            <i className="ka-bs-dot is-waiting" />
            <span />
            <span className="ka-bs-status is-waiting">waiting</span>
            <span>{version.waiting} new {version.waiting === 1 ? 'line' : 'lines'}</span>
          </div>
        )}
        {runs?.map((r) => (
          <button key={r.id} type="button" className="ka-bs-run" aria-pressed={r.id === chosen?.id} onClick={() => setPicked(r.id)}>
            <i className={`ka-bs-dot is-${r.status}`} />
            <span>#{r.id}</span>
            <span className={`ka-bs-status is-${r.status}`}>{STATUS[r.status] ?? r.status}</span>
            <span>
              {[TRIGGERS[r.trigger] ?? r.trigger, `${r.attempts} ${r.attempts === 1 ? 'attempt' : 'attempts'}`, `${r.filed} filed`, r.warnings.length ? `${r.warnings.length} skipped` : '']
                .filter(Boolean).join(' · ')}
              {r.error && <span className="ka-bs-error"> · {r.error}</span>}
            </span>
            {r.stale ? <span className="ka-bs-stale" title="A line it read was edited">stale</span> : <span />}
          </button>
        ))}
        {runs && !runs.length && !version?.waiting && <p className="ka-bs-empty">Nothing read yet.</p>}
      </div>
      <ErrorLine error={error || actionError} />
      <div className="ka-bs-actions">
        <button type="button" className="k-bs-btn k-bs-btn--primary" disabled={busy} onClick={() => act(() => api(`/stories/${story.id}/extract`, 'POST'))}>
          <Icon name="refresh" size={13} />
          Read what is waiting now
        </button>
        <button type="button" className="k-bs-btn" disabled={busy || !chosen} onClick={() => chosen && act(() => api(`/runs/${chosen.id}/reread`, 'POST', { role: 'reasoning' }))}>
          <Icon name="search" size={13} />
          Read #{chosen?.id ?? '…'} again carefully
        </button>
      </div>
    </section>
  )
}
