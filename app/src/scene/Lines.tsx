// The story's rows (SCENE.md › Lines): title cards, notes on who came and went, lines with their
// tools, edits in place, reactions and recalls, and markers where lines were hidden.
import { useState, type ReactNode } from 'react'
import type { Cast, Delivery, Item, LineSignal, Message, Signals, Story } from '../api'
import { K } from '../ds'
import { face, fullTime, twelve } from '../hooks'
import { t } from '../strings'
import { kind } from './modes'
import { later } from './time'

export type LineActions = {
  swipe: (m: Message, step: 1 | -1) => void
  retake: (m: Message) => void
  save: (m: Message, text: string) => void
  rewrite: (m: Message, text: string) => void
  hide: (m: Message, hidden: boolean) => void
  undoSkip: (m: Message) => void
  undoPresence: (id: number) => void
  menu: (at: Element | { clientX: number; clientY: number }, m: Message) => void
}

const REACT_KIND = { memory: 'memory', belief: 'belief', feeling: 'feeling', warm: 'warm', mood: 'mood' } as const

export type Play = { id: number; upto: number; typing: boolean } // a new text reply, bubble by bubble

export default function Lines({ story, messages, cast, signals, advanced, busy, editing, onEditing, colour, itemOf, act, reading, found, play }: {
  story: Story
  messages: Message[]
  cast: Cast
  signals?: Signals
  advanced: boolean
  busy: boolean
  editing?: number
  onEditing: (id?: number) => void
  colour: (m: Message) => string
  itemOf: (entityId: number | null) => Item | undefined
  act: LineActions
  reading?: boolean
  found?: number
  play?: Play
}) {
  const entity = (id: number | null) => cast.entities.find((e) => e.id === id)
  const name = (id: number) => entity(id)?.name ?? '?'
  const list = (ids: number[]) => new Intl.ListFormat('en', { type: 'conjunction' }).format(ids.map(name))
  const shown = messages.filter((m) => m.role !== 'system' || m.skip_minutes > 0)
  const lastSkip = [...messages].reverse().find((m) => m.skip_minutes > 0)
  const skipUndoable = lastSkip && messages.at(-1)?.id === lastSkip.id ? lastSkip.id : undefined
  const lastReply = messages.findLast((m) => m.role === 'assistant')
  const out: ReactNode[] = []
  let hidden: Message[] = []
  const flushHidden = () => {
    if (!hidden.length || reading) return (hidden = [])
    const group = hidden
    out.push(
      <div key={`hid-${group[0].id}`} className="hid">
        <K.Icon name="eyeoff" size={14} />
        <span>{t('scene.hidden', { n: group.length })}</span>
        <button type="button" onClick={() => group.forEach((m) => act.hide(m, false))}>{t('scene.showIt')}</button>
      </div>,
    )
    hidden = []
  }

  out.push(<K.TitleCard key="start">{[story.place?.name, story.start_date].filter(Boolean).join(' · ')}</K.TitleCard>)
  messages.forEach((m, i) => {
    if (m.hidden && m.role !== 'system') return hidden.push(m)
    flushHidden()
    const newScene = m.role === 'system' && i > 0 && m.scene_id !== messages[i - 1].scene_id
    if (m.skip_minutes > 0)
      out.push(
        <K.TitleCard key={`skip-${m.id}`} undo={!reading && m.id === skipUndoable} onUndo={() => act.undoSkip(m)}>
          {later(m.skip_minutes)}
        </K.TitleCard>,
      )
    if (newScene) out.push(<K.TitleCard key={`scene-${m.id}`}>{t('card.scene', { place: m.text.replace(/^—\s*|\s*—$/g, ''), when: m.date })}</K.TitleCard>)
    if (m.role !== 'system') {
      const signal = signals?.lines[m.id]
      out.push(
        <Line key={m.id} m={m} story={story} signal={signal} advanced={advanced && !reading} busy={busy} reading={reading}
          colour={colour(m)} editing={editing === m.id} dim={editing !== undefined && m.id > editing}
          after={shown.length - 1 - shown.indexOf(m)} newest={m.id === lastReply?.id} flash={m.id === found}
          onEditing={(on) => onEditing(on ? m.id : undefined)} act={act} name={name} list={list} itemOf={itemOf}
          texting={story.talk === 'text'} play={play?.id === m.id ? play : undefined} />,
      )
    }
    for (const c of cast.changes.filter((c) => c.message_id === m.id)) {
      const e = entity(c.entity_id)
      const f = face(itemOf(c.entity_id), e?.name)
      out.push(
        <K.StoryNote key={`p-${c.id}`} who={f.who} src={f.src} name={f.name} away={!c.present} onUndo={reading ? undefined : () => act.undoPresence(c.id)}>
          {t(c.present ? 'note.joins' : 'note.left', { name: e?.name ?? '?' })}
        </K.StoryNote>,
      )
    }
  })
  flushHidden()
  return <>{out}</>
}

/** A texting story's line as a phone thread's bubbles: the reply's planned bursts (a typo, then
 *  its `*word` correction), else one bubble a line. `upto`/`typing`: a new reply still playing. */
export function Bubbles({ text, delivery, upto, typing }: { text: string; delivery?: Delivery | null; upto?: number; typing?: boolean }) {
  const bursts = delivery?.mode === 'text' && delivery.bursts.length ? delivery.bursts
    : text.split('\n').filter((l) => l.trim()).map((l) => ({ text: l, correction: false }))
  return (
    <div className="txt__thread">
      {bursts.slice(0, upto ?? bursts.length).map((b, i) => <span key={i} className={b.correction ? 'txt__b txt__b--fix' : 'txt__b'}>{b.text}</span>)}
      {typing && <span className="txt__b txt__typing" role="status" aria-label={t('txt.typing')}><i /><i /><i /></span>}
    </div>
  )
}

function Line({ m, story, signal, advanced, busy, reading, colour, editing, dim, after, newest, flash, onEditing, act, name, list, itemOf, texting, play }: {
  m: Message; story: Story; signal?: LineSignal; advanced: boolean; busy: boolean; reading?: boolean
  colour: string; editing: boolean; dim: boolean; after: number; newest: boolean; flash: boolean
  onEditing: (on: boolean) => void; act: LineActions; name: (id: number) => string; list: (ids: number[]) => string
  itemOf: (entityId: number | null) => Item | undefined; texting: boolean; play?: Play
}) {
  const [draft, setDraft] = useState(m.text)
  const [allReacts, setAllReacts] = useState(false)
  // No speaker means narration, whoever wrote it: it is shown without a name.
  const how = kind(m)
  const who = m.speaker ?? t('scene.narrator')
  const [take, takes] = m.swipe
  const isReply = m.role === 'assistant' && m.parent_id !== null
  const fresh = newest && isReply && take === takes
  const marks = [m.edited && t('line.edited'), m.finish === 'stopped' && t('line.stopped')].filter(Boolean).join(' · ')
  const time = [twelve(m.clock), marks].filter(Boolean).join(' · ')

  if (editing) {
    return (
      <K.EditLine speaker={String(m.speaker_id)} color={colour} name={who} time={twelve(m.clock)} text={m.text} value={draft} onChange={setDraft}
        after={after > 0 ? after : undefined} warn={t('edit.warn', { n: after })} warnMore={t('edit.warnMore')}
        onCancel={() => { setDraft(m.text); onEditing(false) }}
        onSave={() => { if (draft.trim() && draft !== m.text) act.save(m, draft.trim()); onEditing(false) }}
        onRegenerate={after > 0 || m.role === 'user' ? () => { if (draft.trim()) { onEditing(false); act.rewrite(m, draft.trim()) } } : undefined} />
    )
  }
  const callouts = signal?.callouts ?? []
  const reacts = allReacts ? callouts : callouts.slice(0, 3)
  const tools = reading ? undefined : (
    <K.LineTools take={takes > 1 || isReply ? `${take}/${takes}` : undefined} disabled={busy}
      onPrev={takes > 1 && take > 1 ? () => act.swipe(m, -1) : undefined}
      onNext={fresh ? () => act.retake(m) : take < takes ? () => act.swipe(m, 1) : undefined}
      nextLabel={fresh ? t('line.newTake') : t('line.nextTake')}
      onEdit={() => { setDraft(m.text); onEditing(true) }} onHide={() => act.hide(m, true)}
      editLabel={t('line.edit')} hideLabel={t('line.hide')}
      onMore={(e: { currentTarget: Element }) => act.menu(e.currentTarget, m)} />
  )
  const recall = signal?.recall
  const receipts = advanced ? signal?.receipts ?? [] : []
  // a Texting story: said lines are bubbles (yours on the right); narration, thoughts and whispers stay prose
  const bubbles = texting && !how
  return (
    <div className={[flash && 'line-flash', bubbles && (m.role === 'user' ? 'txt txt--me' : 'txt')].filter(Boolean).join(' ') || undefined}>
      <K.ChatLine id={`line-${m.id}`} speaker={String(m.speaker_id ?? m.role)} color={colour} name={who} time={time}
        mode={how} modeNote={how === 'whisper' ? t('line.whisper', { names: list(m.audience ?? []) }) : how === 'think' ? t('line.thought') : undefined}
        exact={m.clock.slice(-5)} timeDetail={fullTime(m.clock, m.date)} text={bubbles ? '' : m.text} dim={dim} tools={tools}
        recalled={!!recall} thought={m.think_ms ? t('scene.thought', { s: Math.max(1, Math.round(m.think_ms / 1000)) }) : undefined}
        onContextMenu={reading ? undefined : (e: MouseEvent) => { e.preventDefault(); act.menu(e, m) }}
        onKeyDown={(e: KeyboardEvent) => { if (e.key === 'F10' && e.shiftKey) { e.preventDefault(); act.menu(e.currentTarget as Element, m) } }}>
        {bubbles && <Bubbles text={m.text} delivery={m.delivery} upto={play?.upto} typing={play?.typing} />}
        {!reading && recall && recall.items[0] && (recall.items[0].tier === 'hazy' || /vaguely|strain/i.test(recall.title)) && (
          <K.RecallBox title={recall.title} memory={recall.items[0].text}
            meta={t('recall.meta', { tier: recall.items[0].tier, how: recall.items[0].how })} />
        )}
        {receipts.map((r) => {
          const f = face(itemOf(r.id), name(r.id))
          const heard = r.state !== 'absent'
          return (
            <span key={r.id} className={`heard${heard ? '' : ' heard--no'}`}>
              <K.Avatar who={f.who} src={f.src} name={f.name} size={20} away={!heard} />
              {t(heard ? 'line.heard' : 'line.notThere', { name: f.name })}
            </span>
          )
        })}
        {!reading && reacts.map((c, i) => {
          const f = face(itemOf(c.who[0] ?? null), c.who[0] ? name(c.who[0]) : '')
          return <K.Reaction key={i} kind={REACT_KIND[c.tone]} who={f.who} avatarSrc={f.src} name={f.name || undefined} soft={c.faded}>{c.text}</K.Reaction>
        })}
        {!reading && !allReacts && callouts.length > 3 && (
          <button type="button" className="k-react k-react--more" onClick={() => setAllReacts(true)}>{t('line.moreReacts', { n: callouts.length - 3 })}</button>
        )}
      </K.ChatLine>
    </div>
  )
}
