// Backstage (Q1–Q5): SCENE.md › Backstage. A blueprint over the scene that reads only what the
// engine recorded: the mind behind a reply, one stage of it, the exact prompt, every memory, logs.
import { useState, type ReactNode } from 'react'
import { api, type CastEntity, type ContextLog, type KnownMemory, type Message, type Mind, type MindNode, type Run, type Story } from '../api'
import { K } from '../ds'
import { face, useLibrary, useLoad } from '../hooks'
import { t, type Key } from '../strings'

type View = 'mind' | 'prompt' | 'memories' | 'logs'
const VIEWS: View[] = ['mind', 'prompt', 'memories', 'logs']
const COLUMNS: [MindNode['column'], Key][] = [['in', 'bs.col.in'], ['sense', 'bs.col.sense'], ['inside', 'bs.col.inside'], ['decide', 'bs.col.decide']]
const KIND: Record<MindNode['kind'], string> = {
  heard: 'HEARD', saw: 'SAW', place: 'SCENE', time: 'TIME', attention: 'WHO', cue: 'CUE', recall: 'RECALL', belief: 'BELIEFS', feeling: 'FEELS', persona: 'YOU', expression: 'FACE',
}
const copy = (text: string) => navigator.clipboard?.writeText(text).catch(() => {})
const secs = (ms?: number | null) => (ms == null ? '' : `${(ms / 1000).toFixed(1)} s`)

export default function Backstage({ story, messages, cast, tick, focus, onForget }: {
  story: Story; messages: Message[]; cast: CastEntity[]; tick: number; focus?: number; onForget: (m: KnownMemory) => void
}) {
  const { byId } = useLibrary()
  const characters = cast.filter((e) => e.is_ai && e.kind === 'character')
  const [who, setWho] = useState<number | 'narrator'>(focus ?? characters.find((e) => e.present)?.id ?? characters[0]?.id ?? 'narrator')
  const replies = messages.filter((m) => m.role === 'assistant' && (who === 'narrator' ? m.speaker_id === null : m.speaker_id === who))
  const [turn, setTurn] = useState<number>()
  const reply = replies[(turn ?? replies.length) - 1]
  const [view, setView] = useState<View>('mind')
  const [node, setNode] = useState<MindNode>()
  const [mind] = useLoad(() => (reply ? api<Mind>(`/messages/${reply.id}/mind`) : Promise.resolve(undefined)), [reply?.id, tick])
  const [ctx] = useLoad(() => (reply ? api<ContextLog>(`/messages/${reply.id}/context`).catch(() => undefined) : Promise.resolve(undefined)), [reply?.id, tick])
  const [runs, reloadRuns] = useLoad(() => api<Run[]>(`/stories/${story.id}/runs`), [story.id, tick])
  const [known, reloadKnown] = useLoad(() => (typeof who === 'number' ? api<KnownMemory[]>(`/stories/${story.id}/memories?knower=${who}`) : Promise.resolve([])), [story.id, who, tick])
  const name = who === 'narrator' ? t('scene.narrator') : characters.find((e) => e.id === who)?.name ?? ''
  const lastRun = runs?.[0]
  const spoke = mind?.spoke
  const recalled = ctx?.memories.filter((m) => m.rendered !== 'dropped').length ?? 0

  return (
    <>
      <div className="bs" aria-hidden="true" />
      <div className={`bsx${view === 'mind' && !node ? '' : ' bsx--wide'}`} role="region" aria-label={t('bs.title')}>
        <div className="bcol">
          <K.BackstagePanel title={t('bs.engine')} status={lastRun?.error ? t('bs.bad') : t('bs.ok')}>
            <K.EngineRow job={t('bs.job.recall')} model={spoke?.model ?? '—'} stat={ctx ? t('bs.matched', { n: recalled, of: ctx.memories.length }) : t('bs.idle')} state={ctx ? 'ok' : 'idle'} />
            <K.EngineRow job={t('bs.job.reasoning')} model={spoke?.model ?? '—'} stat={reply?.think_ms ? secs(reply.think_ms) : t('bs.idle')} state={reply?.think_ms ? 'ok' : 'idle'} />
            <K.EngineRow job={t('bs.job.characters')} model={spoke?.model ?? '—'} stat={spoke?.ms ? secs(spoke.ms) : t('bs.idle')}
              detail={spoke?.tokens ? t('bs.tokens', { n: spoke.tokens }) : undefined} state={spoke ? 'ok' : 'idle'} />
            <K.EngineRow job={t('bs.job.reader')} model={lastRun?.model ?? '—'} stat={lastRun ? lastRun.status : t('bs.idle')}
              detail={lastRun?.filed ? t('bs.filed', { n: lastRun.filed }) : undefined}
              state={!lastRun ? 'idle' : lastRun.error ? 'bad' : lastRun.status === 'done' ? 'ok' : 'wait'} />
          </K.BackstagePanel>
          <K.BackstagePanel title={t('bs.whose')}>
            <div className="who-tabs" role="tablist" aria-label={t('bs.whose')}>
              {characters.map((e) => {
                const f = face(byId.get(e.lib_item_id ?? -1), e.name)
                return (
                  <button key={e.id} type="button" className="who-tab" role="tab" aria-selected={who === e.id} onClick={() => { setWho(e.id); setTurn(undefined); setNode(undefined) }}>
                    <K.Avatar who={f.who} src={f.src} name={e.name} size={26} away={!e.present} />{e.present ? e.name : t('bs.away', { name: e.name })}
                  </button>
                )
              })}
              <button type="button" className="who-tab" role="tab" aria-selected={who === 'narrator'} onClick={() => { setWho('narrator'); setTurn(undefined); setNode(undefined) }}>{t('scene.narrator')}</button>
            </div>
            {replies.length > 0 && (
              <div className="turn"><span>{t('bs.turn')}</span>
                <input type="range" min={1} max={replies.length} value={turn ?? replies.length} aria-label={t('bs.whichTurn')} onChange={(e) => { setTurn(Number(e.target.value)); setNode(undefined) }} />
                <span>{t('bs.of', { n: turn ?? replies.length, total: replies.length })}</span>
              </div>
            )}
          </K.BackstagePanel>
          <div className="bsfilter" role="toolbar" aria-label={t('bs.views')}>
            {VIEWS.map((v) => <button key={v} type="button" className="bsbtn" aria-pressed={view === v} onClick={() => { setView(v); setNode(undefined) }}>{t(`bs.v.${v}` as Key)}</button>)}
          </div>
        </div>

        {view === 'mind' && !node && (
          <K.BackstagePanel title={t('bs.mindOf', { name, n: turn ?? replies.length })} action={mind ? t('bs.copyJson') : undefined} actionIcon="link" onAction={() => copy(JSON.stringify(mind, null, 2))}>
            {!mind ? <span className="bs-t">{t('bs.noReply')}</span> : (
              <div className="mg" role="list" aria-label={t('bs.mindLabel', { name })}>
                {COLUMNS.map(([col, label], i) => (
                  <Fragment key={col} arrow={i > 0}>
                    <div className="mg__col" role="listitem"><span className="bs-t">{t(label)}</span>
                      {col === 'decide' ? (
                        <div className="decide is-won"><b>{spoke?.text.slice(0, 140)}</b><span>{t('bs.chosen')}</span></div>
                      ) : mind.nodes.filter((n) => n.column === col).map((n) => (
                        <button key={n.id} type="button" className="mg__node" onClick={() => setNode(n)}>
                          <K.MindNode kind={KIND[n.kind]} value={n.weight ?? 0} hot={n.gold}>{n.title}{n.text ? ` · ${n.text}` : ''}</K.MindNode>
                        </button>
                      ))}
                    </div>
                  </Fragment>
                ))}
              </div>
            )}
          </K.BackstagePanel>
        )}

        {view === 'mind' && node && (
          <K.BackstagePanel title={`${KIND[node.kind]} · ${name} · ${t('bs.turn')} ${turn ?? replies.length}`} action={t('bs.back')} actionIcon="left" onAction={() => setNode(undefined)}>
            <div className="bsrow"><span>{t('bs.what')}</span><span>{node.title}</span></div>
            {node.text && <div className="bsrow"><span>{t('bs.said')}</span><span>{node.text}</span></div>}
            <div className="bsrow"><span>{t('bs.strength')}</span><span>{(node.weight ?? 0).toFixed(2)}{node.gold ? ` · ${t('bs.reached')}` : ''}</span></div>
            {Object.entries(node.detail ?? {}).map(([k, v]) => <div key={k} className="bsrow"><span>{k}</span><span>{typeof v === 'string' ? v : JSON.stringify(v)}</span></div>)}
            <div className="row" style={{ gap: 8 }}><button type="button" className="bsbtn" onClick={() => copy(JSON.stringify(node, null, 2))}>{t('bs.copy')}</button></div>
          </K.BackstagePanel>
        )}

        {view === 'prompt' && (
          <K.BackstagePanel title={t('bs.promptOf', { name, n: turn ?? replies.length })} action={ctx?.prompt ? t('bs.copyAll') : undefined} actionIcon="link"
            onAction={() => copy((ctx?.prompt ?? []).map((p) => `[${p.role}]\n${p.content}`).join('\n\n'))}>
            {!ctx ? <span className="bs-t">{t('bs.noPrompt')}</span> : (
              <>
                <K.PromptBar label={t('scene.tokens', { used: ctx.est_tokens.toLocaleString('en'), limit: ctx.budget.toLocaleString('en') })}
                  meta={ctx.cached_tokens && ctx.actual_tokens ? t('bs.cache', { n: Math.round((100 * ctx.cached_tokens) / ctx.actual_tokens) }) : undefined}
                  segments={ctx.sections.map((s) => ({ name: s.name, value: s.tokens, limit: s.cap }))} />
                <span className="bs-t">{t('bs.readOnly')}</span>
                <pre className="pre bs-prompt">
                  {(ctx.prompt ?? []).map((p, i) => <span key={i}><span className="seg">── {p.role}</span>{p.content}{'\n'}</span>)}
                </pre>
              </>
            )}
          </K.BackstagePanel>
        )}

        {view === 'memories' && <Memories name={name} known={known ?? []} onForget={(m) => { onForget(m); setTimeout(reloadKnown, 300) }} />}

        {view === 'logs' && (
          <K.BackstagePanel title={t('bs.logs')} action={runs?.length ? t('bs.saveLog') : undefined} actionIcon="download"
            onAction={() => {
              const a = document.createElement('a')
              a.href = URL.createObjectURL(new Blob([(runs ?? []).map(logLine).join('\n')], { type: 'text/plain' }))
              a.download = `kataki-${story.id}.log`
              a.click()
            }}>
            <span className="bs-t">{t('bs.logsNote')}</span>
            {(runs ?? []).map((r) => (
              <div key={r.id} className={`logl${r.error ? ' logl--error' : r.warnings.length ? ' logl--warn' : ''}`}>
                <span>#{r.id}</span><span className="lv">{r.error ? 'error' : r.warnings.length ? 'warn' : 'info'}</span><span>{r.role ?? r.trigger}</span>
                <span>{[`${r.status} · lines ${r.from_message_id}–${r.to_message_id}`, r.model, r.filed ? `${r.filed} filed` : '', ...r.warnings, r.error].filter(Boolean).join(' · ')}</span>
                {r.role === 'utility' && r.status === 'ok' && (
                  <button type="button" className="bsbtn" title={t('bs.rereadCost')} onClick={() => api(`/runs/${r.id}/reread`, 'POST', { role: 'utility' }).then(reloadRuns)}>{t('bs.reread')}</button>
                )}
              </div>
            ))}
          </K.BackstagePanel>
        )}

        {view === 'mind' && !node && (
          <div className="bcol">
            <K.BackstagePanel title={t('bs.prompt')}>
              {ctx ? (
                <>
                  <div className="bsrow"><span>{t('bs.size')}</span><span>{t('scene.tokens', { used: ctx.est_tokens.toLocaleString('en'), limit: ctx.budget.toLocaleString('en') })}</span></div>
                  <div className="bsrow"><span>{t('bs.recalled')}</span><span>{recalled}</span></div>
                  {ctx.sections.map((s) => <div key={s.name} className="bsrow"><span>{s.name}</span><span>{s.tokens} / {s.cap}{s.evicted ? ` · ${s.evicted} dropped` : ''}</span></div>)}
                </>
              ) : <span className="bs-t">{t('bs.noPrompt')}</span>}
            </K.BackstagePanel>
            <K.BackstagePanel title={t('bs.reply')}>
              {spoke ? (
                <>
                  <div className="bsrow"><span>{t('bs.said')}</span><span>{spoke.text}</span></div>
                  <div className="bsrow"><span>{t('bs.tokensOut')}</span><span>{spoke.tokens ?? '—'}</span></div>
                  <div className="bsrow"><span>{t('bs.time')}</span><span>{secs(spoke.ms) || '—'}</span></div>
                  <div className="bsrow"><span>{t('bs.model')}</span><span>{spoke.model ?? '—'}</span></div>
                </>
              ) : <span className="bs-t">{t('bs.noReply')}</span>}
            </K.BackstagePanel>
          </div>
        )}
      </div>
    </>
  )
}

function Fragment({ arrow, children }: { arrow: boolean; children: ReactNode }) {
  return <>{arrow && <div className="mg__arrow" aria-hidden="true"><i /></div>}{children}</>
}

const logLine = (r: Run) => [`#${r.id}`, r.error ? 'error' : 'info', r.role ?? r.trigger, r.status, r.model ?? '', ...r.warnings, r.error ?? ''].filter(Boolean).join('\t')

/** Q4: every memory this character holds, with how sharp it is now. */
function Memories({ name, known, onForget }: { name: string; known: KnownMemory[]; onForget: (m: KnownMemory) => void }) {
  const [q, setQ] = useState('')
  const [kind, setKind] = useState<'all' | 'sharp' | 'hazy' | 'doubted'>('all')
  const test = { all: () => true, sharp: (m: KnownMemory) => m.tier === 'sharp', hazy: (m: KnownMemory) => m.tier === 'hazy', doubted: (m: KnownMemory) => m.belief < 0.7 }
  const shown = known.filter((m) => !m.hidden).filter(test[kind]).filter((m) => !q.trim() || `${m.gist} ${m.detail}`.toLowerCase().includes(q.trim().toLowerCase()))
  return (
    <K.BackstagePanel title={t('bs.memoriesOf', { name })}>
      <div className="row" style={{ gap: 8 }}>
        <input className="bsin" value={q} placeholder={t('bs.filter')} aria-label={t('bs.filter')} onChange={(e) => setQ(e.target.value)} />
        {(['all', 'sharp', 'hazy', 'doubted'] as const).map((k) => <button key={k} type="button" className="bsbtn" aria-pressed={kind === k} onClick={() => setKind(k)}>{t(`mem.${k}` as Key).toLowerCase()}</button>)}
      </div>
      <div className="mtable">
        <div className="mrow mrow--head"><span>{t('bs.m.memory')}</span><span>{t('bs.m.sharp')}</span><span>{t('bs.m.source')}</span><span>{t('bs.m.score')}</span><span /></div>
        {shown.map((m) => {
          const v = Math.round(100 / (1 + Math.exp(-(m.A + 3))))
          return (
            <div key={m.memory_id} className="mrow" style={m.tier === 'forgotten' ? { opacity: 0.55 } : undefined}>
              <span>{m.gist || m.detail}</span>
              <span className="sharp"><i style={{ width: Math.round(v * 0.6) }} />{m.belief < 0.7 ? t('mem.word.doubted') : m.tier}</span>
              <span>{m.told_by ? t('mem.told', { name: m.told_by }) : m.source}</span>
              <span>{m.A.toFixed(2)}</span>
              <span>{m.tier !== 'forgotten' && <button type="button" className="bsbtn" onClick={() => onForget(m)}>{t('bs.forget')}</button>}</span>
            </div>
          )
        })}
      </div>
    </K.BackstagePanel>
  )
}
