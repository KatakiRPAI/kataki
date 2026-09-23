import { useEffect, useRef, useState, type CSSProperties } from 'react'
import { api, type CastEntity, type Feelings, type Person, type Pronouns } from '../api'
import { Avatar, paletteOf, pronounsOf } from '../art'
import { href, useLibrary, useLoad } from '../hooks'
import Elsewhere from '../sky/Elsewhere'
import { Icon } from '../ui'

// How each relationship reads: warm ones sit in amber, cold ones in the doubt colour.
const COLD = ['resents', 'distrusts', 'doubts', 'fears', 'hates', 'blames', 'avoids']

const HER = { she: 'her', he: 'his', they: 'their' } // on ___ mind
const HER_TOO = { she: 'her', he: 'him', they: 'them' } // let ___ answer next
const SHE = { she: 'she', he: 'he', they: 'they' }
const KNOWS = { she: 'knows', he: 'knows', they: 'know' }
const FEELS = { she: 'feels', he: 'feels', they: 'feel' }

const STATE_ICON: Record<string, string> = {
  holding: 'hand',
  wearing: 'user',
  where: 'map-pin',
  injury: 'alert',
}

const sentence = (s: string) => s[0].toUpperCase() + s.slice(1)

/** A tier, as the scene shows clarity everywhere else: solid for sharp, dashed for hazy. */
function Tier({ tier }: { tier: string }) {
  return <span className={`ka-tier is-${tier}`}>{tier.toUpperCase()}</span>
}

/** Everything the story knows about one character right now, over the stage. Esc closes it; so
 *  does a click anywhere else. */
export default function Peek({ story, entity, at, tick, busy, onClose, onAnswer, onMove, onBackstage, onWidget, about }: {
  story: number
  entity: CastEntity
  at: { x: number; y: number }
  tick: number // the scene refreshed: read the room again
  busy: boolean
  onClose: () => void
  onAnswer: () => void
  onMove: () => void
  onBackstage: () => void
  onWidget?: () => void // "Add as widget"; none when they already have one
  about?: string // who "you" is (the persona), for how they feel about you
}) {
  const { byId } = useLibrary()
  const [people, , error] = useLoad(() => api<Person[]>(`/stories/${story}/people`), [story, entity.id, tick])
  const [revealed, setRevealed] = useState(false)
  const card = useRef<HTMLDivElement>(null)
  const close = useRef(onClose)
  close.current = onClose
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null
    card.current?.focus() // the card itself, so a keyboard starts at the top of it, not on Close
    // Escape backs out of whatever is over the card before it closes the card itself, the same
    // way reading mode reads it — a dialog opened from here owns the first press.
    const leave = (e: KeyboardEvent) =>
      e.key === 'Escape' && !document.querySelector('dialog[open], :popover-open') && close.current()
    const elsewhere = (e: MouseEvent) => card.current?.contains(e.target as Node) || close.current()
    addEventListener('keydown', leave)
    addEventListener('pointerdown', elsewhere)
    return () => {
      removeEventListener('keydown', leave)
      removeEventListener('pointerdown', elsewhere)
      opener?.focus?.() // back to whoever you looked at
    }
  }, [])

  const person = people?.find((p) => p.id === entity.id)
  const item = entity.lib_item_id ? byId.get(entity.lib_item_id) : undefined
  const they = pronounsOf(item)
  const name = entity.name
  // who they are, in as few words as they wrote: the first sentence of the first line
  const role = (item?.description || entity.summary || '').split('\n')[0].split(/(?<=\.)\s/)[0].replace(/\.$/, '')
  const state = person?.state ?? []
  const rows: [string, string, boolean][] = [
    ...state.filter((f) => f.key.toLowerCase() !== 'where').map((f): [string, string, boolean] => [f.key, f.value, f.private]),
    ...(person?.where ? [['Where', person.where, false] as [string, string, boolean]] : []),
  ]
  const knows = person?.about_you
  const faded = knows ? knows.hazy + knows.forgotten : 0

  return (
    <div
      ref={card}
      className="k-peek ka-peek"
      style={{ '--x': `${at.x}px`, '--y': `${at.y}px`, '--ink': paletteOf(item, name).ink } as CSSProperties}
      role="dialog"
      aria-label={`${name}, right now`}
      tabIndex={-1}
    >
      <div className="ka-peek__head">
        <Avatar item={item} name={name} size={56} className="ka-peek__face" />
        <span className="ka-peek__who">
          <span className="ka-peek__name">{name}</span>
          <span className="ka-peek__role">{[role, entity.present ? 'present' : 'away'].filter(Boolean).join(' · ')}</span>
        </span>
        {onWidget && (
          <button type="button" className="ka-peek__widget" onClick={onWidget}>
            <Icon name="plus" size={14} />
            Add as widget
          </button>
        )}
        <button type="button" className="ka-peek__close" aria-label="Close" onClick={onClose}>
          <Icon name="x" size={16} />
        </button>
      </div>

      {error && <p className="ka-peek__note">{error}</p>}
      {!people && <p className="ka-peek__note">Reading the room…</p>}

      {person && (
        <>
          <div className="ka-peek__block">
            <span className="ka-peek__eyebrow">Right now</span>
            {rows.length === 0 && <span className="ka-peek__none">Nothing the reader has noticed yet.</span>}
            {rows.map(([key, value, hidden]) => (
              <div key={key} className="ka-peek__row">
                <span className="ka-peek__icon"><Icon name={STATE_ICON[key.toLowerCase()] ?? 'spark'} size={15} /></span>
                <span className="ka-peek__key">{sentence(key)}</span>
                <span className="ka-peek__value">
                  {value}
                  {hidden && <Icon name="lock" size={12} />}
                </span>
              </div>
            ))}
          </div>

          {about && entity.is_ai && <FeelsAboutYou story={story} entity={entity} tick={tick} they={they} />}

          <div className="ka-peek__block">
            <span className="ka-peek__eyebrow">On {HER[they]} mind</span>
            {person.on_mind ? (
              <div className="ka-peek__mind">
                <Tier tier={person.on_mind.tier} />
                <span className="ka-peek__thought">{person.on_mind.text}</span>
              </div>
            ) : (
              <span className="ka-peek__none">Nothing {SHE[they]} {KNOWS[they]} is close to hand.</span>
            )}
          </div>

          {knows && (
            <div className="ka-peek__block">
              <div className="ka-peek__blockhead">
                <span className="ka-peek__eyebrow">What {SHE[they]} {KNOWS[they]} about you</span>
                <button type="button" className="ka-peek__more" onClick={onBackstage}>
                  {knows.count} {knows.count === 1 ? 'memory' : 'memories'}
                  {faded > 0 && ` · ${faded} faded`}
                </button>
              </div>
              {knows.samples.length === 0 && <span className="ka-peek__none">Nothing about you yet.</span>}
              {knows.samples.map((s) => (
                <div key={s.memory_id} className="ka-peek__row ka-peek__row--sample">
                  <Tier tier={s.tier} />
                  <span className="ka-peek__sample">
                    {s.text}
                    {s.belief < 0.75 && <span className="ka-peek__doubt"> Doubted.</span>}
                  </span>
                </div>
              ))}
            </div>
          )}

          {person.relationships.length > 0 && (
            <div className="ka-peek__chips">
              {person.relationships.map((r) => (
                <span key={`${r.rel}-${r.other_id}`} className={`ka-peek__chip${COLD.includes(r.rel) ? ' is-cold' : ''}`} title={r.note ?? undefined}>
                  {sentence(r.rel)} {r.other}
                </span>
              ))}
            </div>
          )}

          {person.secret && (
            <div className="ka-peek__secret">
              <Icon name="lock" size={16} />
              <span className="ka-peek__who">
                <span className="ka-peek__eyebrow">Only {name} knows this</span>
                <span className={`ka-peek__secrettext${revealed ? ' is-shown' : ''}`}>{person.secret}</span>
              </span>
              <button type="button" className="ka-peek__reveal" onClick={() => setRevealed((r) => !r)}>
                {revealed ? 'Hide' : 'Reveal'}
              </button>
            </div>
          )}

          {entity.lib_item_id && (
            <div className="ka-peek__block">
              <span className="ka-peek__eyebrow">Where else {name} is</span>
              <Elsewhere item={entity.lib_item_id} name={name} here={story} scene />
            </div>
          )}

          <div className="ka-peek__acts">
            <button type="button" className="ka-peek__answer" disabled={busy || !entity.present} onClick={onAnswer}>
              Let {HER_TOO[they]} answer next
            </button>
            <button type="button" className="ka-peek__act" disabled={busy} onClick={onMove}>
              {entity.present ? 'Send away' : 'Bring back'}
            </button>
            {entity.lib_item_id && (
              <a className="ka-peek__act ka-peek__act--icon" href={href(`/friend/${entity.lib_item_id}/edit`)} aria-label={`Edit ${name}`}>
                <Icon name="edit" size={16} />
              </a>
            )}
          </div>
        </>
      )}
    </div>
  )
}

const BARS: ['warmth' | 'trust' | 'doubt', string, string][] = [
  ['warmth', 'Warmth', 'var(--k-scene-sage)'],
  ['trust', 'Trust', 'var(--k-scene-amber)'],
  ['doubt', 'Doubt', 'var(--k-scene-lilac)'],
]

/** Warmth, trust and doubt toward you, as of the last memory read. They are counts (a warm feeling
 *  +1, a cold one -1; doubt is how many of your claims they disbelieve), drawn on a short scale:
 *  a bar never claims to be a measurement, and its hover says what it counts. */
function FeelsAboutYou({ story, entity, tick, they }: { story: number; entity: CastEntity; tick: number; they: Pronouns }) {
  const [got] = useLoad(() => api<Feelings>(`/stories/${story}/feelings?who=${entity.id}`), [story, entity.id, tick])
  const now = got?.points.at(-1)
  if (!now) return null
  const width = (k: 'warmth' | 'trust' | 'doubt') =>
    k === 'doubt' ? Math.min(now.doubt, 4) / 4 : (Math.max(-2, Math.min(2, now[k])) + 2) / 4
  const said = (k: 'warmth' | 'trust' | 'doubt') =>
    k === 'doubt' ? `${now.doubt} of your claims doubted` : `${now[k] > 0 ? '+' : ''}${now[k]}, counted from what memory has read`
  return (
    <div className="ka-peek__block">
      <span className="ka-peek__eyebrow">How {SHE[they]} {FEELS[they]} about you</span>
      {BARS.map(([k, label, color]) => (
        <div key={k} className="ka-peek__bar" title={said(k)}>
          <span>{label}</span>
          <span className="ka-peek__track"><i style={{ width: `${width(k) * 100}%`, background: color }} /></span>
        </div>
      ))}
    </div>
  )
}
