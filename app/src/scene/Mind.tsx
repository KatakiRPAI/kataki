import { useState, type CSSProperties, type ReactNode } from 'react'
import { api, type Cast, type Message, type Mind as MindGraph, type MindNode, type Story } from '../api'
import { Avatar } from '../art'
import { twelve, useLibrary, useLoad } from '../hooks'
import { ErrorLine, Icon, Prose } from '../ui'

const COLUMNS: [MindNode['column'], string, string][] = [
  ['in', 'IN', 'Nothing reached them.'],
  ['sense', 'SENSE', 'Not recorded for this reply: it was written before the engine kept why they answered.'],
  ['inside', 'INSIDE', 'No prompt was logged for this reply.'],
  ['decide', 'DECIDE', 'No face was chosen: they have no expressions yet.'],
]
const W = 1000 // the graph's own width units; the SVG stretches them to the panel
const COL = W / 4
const NODE_W = 212 // of 250 per column
const NODE_H = 82
const GAP = 14
const TOP = 34 // below the column labels

const at = (col: number, row: number) => ({ x: col * COL + 12, y: TOP + row * (NODE_H + GAP) })

/** How one reply came about (docs/specs/2026-09-23-mind-graph.md): what came in, what came back to
 *  them, what they felt and doubted, the face they chose. Only what the engine recorded; gold is
 *  what reached the prompt, blue what was weighed and cut. `swap` switches the panel to Memory. */
export default function Mind({ story, cast, tick, swap }: { story: Story; cast: Cast; tick: number; swap: ReactNode }) {
  const { byId } = useLibrary()
  const [messages] = useLoad(() => api<Message[]>(`/stories/${story.id}/messages`), [story.id, tick])
  const replies = (messages ?? []).filter((m) => m.role === 'assistant' && !m.hidden)
  const speakers = cast.entities.filter((e) => e.is_ai && e.kind === 'character' && replies.some((m) => m.speaker_id === e.id))
  const narrates = replies.some((m) => m.speaker_id === null)
  const [picked, setPicked] = useState<number | null | undefined>()
  const who = picked !== undefined ? picked : (replies.at(-1)?.speaker_id ?? null)
  const reply = replies.findLast((m) => m.speaker_id === who)
  const [mind, , error] = useLoad(
    () => (reply ? api<MindGraph>(`/messages/${reply.id}/mind`) : Promise.resolve(undefined)),
    [reply?.id, tick],
  )
  const [open, setOpen] = useState<string>()
  const item = (id: number | null) => byId.get(cast.entities.find((e) => e.id === id)?.lib_item_id ?? -1)

  const placed = new Map<string, { x: number; y: number }>()
  const byColumn = COLUMNS.map(([column]) => (mind?.nodes ?? []).filter((n) => n.column === column))
  byColumn.forEach((nodes, col) => nodes.forEach((n, row) => placed.set(n.id, at(col, row))))
  const rows = Math.max(1, ...byColumn.map((c) => c.length))
  const height = TOP + rows * (NODE_H + GAP)
  const detail = mind?.nodes.find((n) => n.id === open)

  return (
    <section className="k-bs-panel ka-bs-mind" aria-label="Mind">
      <div className="k-bs-title">
        <span>MIND{reply && ` · LAST REPLY, ${twelve(reply.clock).toUpperCase()}`}</span>
        <span className="ka-row">
          <span className="ka-bs-group" role="tablist" aria-label="Whose mind">
            {speakers.map((e) => (
              <button key={e.id} type="button" role="tab" aria-selected={who === e.id} className="k-bs-btn ka-bs-person" onClick={() => setPicked(e.id)}>
                <Avatar item={item(e.id)} name={e.name} size={20} />
                {e.name}
              </button>
            ))}
            {narrates && (
              <button type="button" role="tab" aria-selected={who === null} className="k-bs-btn ka-bs-person" onClick={() => setPicked(null)}>
                <Icon name="feather" size={14} />
                Narrator
              </button>
            )}
          </span>
          {swap}
        </span>
      </div>
      <ErrorLine error={error} />
      {!reply && <p className="ka-bs-muted ka-mind__empty">No replies yet. Play a turn and its mind shows here.</p>}
      {mind && (
        <>
          <div className="ka-mind" style={{ height } as CSSProperties}>
            {COLUMNS.map(([column, label, none], col) => (
              <div key={column} className="ka-mind__column" style={{ left: `${(col * 100) / 4}%` }}>
                <span className="ka-mind__label">{label}</span>
                {!byColumn[col].length && <span className="ka-mind__none">{none}</span>}
                {column === 'inside' && !!mind.more.recall && (
                  <span className="ka-mind__more" style={{ top: TOP + byColumn[col].length * (NODE_H + GAP) }}>
                    + {mind.more.recall} more recalled
                  </span>
                )}
              </div>
            ))}
            <svg className="ka-mind__links" viewBox={`0 0 ${W} ${height}`} preserveAspectRatio="none" aria-hidden="true">
              {mind.links.map((l) => {
                const a = placed.get(l.from)
                const b = placed.get(l.to)
                if (!a || !b) return null // links to what was said are the Spoke box below
                const [x1, y1, x2, y2] = [a.x + NODE_W, a.y + NODE_H / 2, b.x, b.y + NODE_H / 2]
                const mid = (x1 + x2) / 2
                return (
                  <path key={`${l.from}-${l.to}`} className={`k-mind-edge${l.gold ? ' is-win' : ''}`}
                    d={`M${x1} ${y1} C${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`} vectorEffect="non-scaling-stroke" />
                )
              })}
            </svg>
            {mind.nodes.map((n) => {
              const p = placed.get(n.id)!
              return (
                <button key={n.id} type="button" aria-pressed={open === n.id}
                  className={`k-mind-node ka-mind__node${n.gold ? ' is-win' : ''}`}
                  style={{ left: `${(p.x / W) * 100}%`, top: p.y, width: `${(NODE_W / W) * 100}%`, '--a': n.weight ?? 0 } as CSSProperties}
                  onClick={() => setOpen((o) => (o === n.id ? undefined : n.id))}>
                  <span className="ka-mind__kind">
                    <span>{n.title.toUpperCase()}</span>
                    {n.weight !== null && <span>{n.weight.toFixed(2)}</span>}
                  </span>
                  <span className="ka-mind__text">{n.text}</span>
                  {n.weight !== null && <span className="k-mind-node__bar"><i /></span>}
                </button>
              )
            })}
          </div>
          {detail && <Detail node={detail} />}
          <div className="ka-mind__spoke">
            <span className="ka-mind__label">SPOKE</span>
            <span className="ka-mind__said"><Prose text={mind.spoke.text} /></span>
            <span className="ka-bs-muted">{[mind.spoke.model, mind.spoke.ms && `${(mind.spoke.ms / 1000).toFixed(1)} s`, mind.spoke.tokens && `${mind.spoke.tokens} tok`].filter(Boolean).join(' · ')}</span>
          </div>
          <p className="ka-bs-muted ka-mind__foot">
            Gold is what reached the prompt this reply was written from; blue was weighed and cut. Click any part to see what went into it.
          </p>
        </>
      )}
    </section>
  )
}

const WORDS: Record<string, string> = {
  A: 'activation', B: 'base (use and time)', S: 'relevance to the cue', G: 'spread from related memories', imp: 'importance',
  tier: 'clarity', rendered: 'in the prompt as', tone: 'tone', note: 'why',
}

/** What went into a node: a recall's numbers, a feeling's note, the whole line heard. */
function Detail({ node }: { node: MindNode }) {
  const rows = Object.entries(node.detail ?? {}).filter(([k, v]) => v !== null && v !== undefined && WORDS[k])
  return (
    <div className="ka-mind__detail" role="region" aria-label={`${node.title} in detail`}>
      <span className="ka-mind__label">{node.title.toUpperCase()}</span>
      <span>{node.text}</span>
      {rows.length > 0 && (
        <dl>
          {rows.map(([k, v]) => (
            <div key={k}><dt>{WORDS[k]}</dt><dd>{v === 'dropped' ? 'cut for the budget' : String(v)}</dd></div>
          ))}
        </dl>
      )}
      {node.kind === 'feeling' && !node.gold && (
        <span className="ka-bs-muted">Not in the prompt for this reply (written before feelings reached replies), so it didn't shape what they said.</span>
      )}
    </div>
  )
}
