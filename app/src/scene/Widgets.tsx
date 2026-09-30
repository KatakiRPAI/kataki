// Widgets (SCENE.md › Widgets, P3): characters, the clock, the place, the cast and notes. Pinned
// ones always show; unpinned ones only when something happens to them. Edit widgets moves them
// anywhere (8 px steps), pins, removes and adds. The layout is per story, in `story.ui.widgets`.
import { useRef, useState, type ReactNode } from 'react'
import type { CastEntity, Item, Story, StoryUi, WidgetSpec } from '../api'
import { K } from '../ds'
import { face, fullTime, scenery, twelve, useNarrow } from '../hooks'
import { openMenu, toast, type MenuItem } from '../overlay'
import { t, type Key } from '../strings'

type Kind = WidgetSpec['kind']
const STEP = 8

/** What shows when a story has never been arranged: everyone here, then the clock. */
export function defaults(present: CastEntity[]): WidgetSpec[] {
  return [...present.map((e) => ({ id: `c${e.id}`, kind: 'character' as const, entity: e.id, pinned: true })), { id: 'clock', kind: 'clock', pinned: true }]
}

export function Board({ story, people, everyone, itemOf, speaking, active, editing, onDone, onSave, onPassTime, onOpen, busy, detail, onAnswer, onMove, onArrange, onSetTime }: {
  story: Story
  people: CastEntity[] // here now
  everyone: CastEntity[] // every character in the story
  itemOf: (e: { lib_item_id: number | null }) => Item | undefined
  speaking?: number // answering now
  active: number[] // spoke or reacted in the last line: unpinned widgets for them show
  editing: boolean
  onDone: () => void
  onSave: (ui: StoryUi) => void
  onPassTime: () => void
  onOpen: (entity: number) => void
  busy: boolean
  detail?: (entity: number) => string | undefined // "fond of you", from what the engine stored
  onAnswer: (entity: number) => void // WidgetMenus (M2)
  onMove: (entity: number) => void // here ↔ away
  onArrange: () => void // Edit all widgets
  onSetTime: () => void
}) {
  const saved = story.ui.widgets
  const [draft, setDraft] = useState<WidgetSpec[]>()
  const widgets = (editing ? draft : undefined) ?? saved ?? defaults(people)
  const [notes, setNotes] = useState(story.ui.notes ?? '')
  const [moving, setMoving] = useState<{ id: string; x: number; y: number } | null>(null)
  const [picked, setPicked] = useState<string>()
  const compact = useNarrow(1280)
  const start = useRef<{ px: number; py: number; x: number; y: number }>(undefined)
  const edit = (next: WidgetSpec[]) => setDraft(next)
  if (editing && !draft) setDraft(widgets)

  const place = story.place ? itemOf(story.place) : undefined
  const entity = (id?: number) => everyone.find((e) => e.id === id)
  const visible = (w: WidgetSpec) => editing || w.pinned || (w.kind === 'character' && (w.entity === speaking || active.includes(w.entity ?? -1)))
  const at = (w: WidgetSpec) => (moving?.id === w.id ? { x: moving.x, y: moving.y } : w.at ? { x: w.at.x * innerWidth, y: w.at.y * innerHeight } : null)
  const set = (id: string, change: Partial<WidgetSpec>) => edit(widgets.map((w) => (w.id === id ? { ...w, ...change } : w)))
  const snap = (v: number) => Math.round(v / STEP) * STEP
  const drop = (id: string, x: number, y: number) => set(id, { at: { x: snap(x) / innerWidth, y: snap(y) / innerHeight } })

  const body = (w: WidgetSpec): ReactNode => {
    const common = { edit: editing, pinned: w.pinned, onPin: () => (editing ? set(w.id, { pinned: !w.pinned }) : onSave({ widgets: widgets.map((x) => (x.id === w.id ? { ...x, pinned: !x.pinned } : x)) })), onRemove: () => edit(widgets.filter((x) => x.id !== w.id)) }
    if (w.kind === 'character') {
      const e = entity(w.entity)
      if (!e) return null
      const f = face(itemOf(e), e.name)
      const here = e.present
      const p = itemOf(e)?.data.pronouns ?? 'they'
      const presence = t(here ? 'w.here' : 'w.away')
      const more = detail?.(e.id)
      const status = w.entity === speaking ? t('w.choosing', { p }) : more ? t('w.status', { presence, detail: more }) : presence
      return here && !compact
        ? <K.CharacterWidget {...common} who={f.who} src={f.src} focus={f.focus} zoom={f.zoom} name={e.name} thinking={w.entity === speaking} status={status} onOpen={() => onOpen(e.id)} alt={itemOf(e)?.data.alt} />
        : <K.CharacterRowWidget {...common} who={f.who} src={f.src} focus={f.focus} zoom={f.zoom} name={e.name} away={!here} status={here ? status : t('w.away')} onOpen={() => onOpen(e.id)} />
    }
    if (w.kind === 'clock')
      return <K.ClockWidget {...common} time={twelve(story.clock)} rel={story.date} place={story.place?.name ?? ''} exact={story.clock.slice(-5)}
        detail={fullTime(story.clock, story.date)} kind={story.minute_of_day >= 1200 || story.minute_of_day < 360 ? 'night' : 'dusk'} onPassTime={onPassTime} disabled={busy} />
    if (w.kind === 'place') {
      const s = scenery(place)
      const src = s.src ?? (s.place ? K.ART[s.place]?.src ?? undefined : undefined)
      return (
        <K.Widget {...common} label={t('w.k.place')}>
          {src && <div className="wplace"><img src={src} alt={place?.name ?? ''} /></div>}
          <div className="wnotes"><b>{story.place?.name ?? t('place.nowhere')}</b><span className="scene-t">{story.date}</span></div>
        </K.Widget>
      )
    }
    if (w.kind === 'cast')
      return (
        <K.Widget {...common} label={t('w.k.cast')}>
          <div className="wnotes"><b>{t('w.k.cast')}</b>
            <K.AvatarStack people={people.map((e) => ({ ...face(itemOf(e), e.name) }))} size={34} max={8} />
          </div>
        </K.Widget>
      )
    if (w.kind === 'notes')
      return (
        <K.Widget {...common} label={t('w.notes')}>
          <div className="wnotes"><b>{t('w.notes')}</b>
            <textarea className="wnotes__field" value={notes} placeholder={t('w.notesPlaceholder')} rows={3} disabled={editing}
              onChange={(e) => setNotes(e.target.value)} onBlur={() => notes !== (story.ui.notes ?? '') && onSave({ notes })} />
            <span className="scene-t">{t('w.notesOnly')}</span>
          </div>
        </K.Widget>
      )
    return null
  }

  // CharacterWidgetMenu, ClockMenu, WidgetMenu (MenusScene, M2): right-click a widget
  const keep = (next: WidgetSpec[]) => onSave({ widgets: next })
  const pin = (w: WidgetSpec): MenuItem => ({ label: t(w.pinned ? 'wm.unpin' : 'wm.pin'), detail: w.pinned && w.kind === 'character' ? t('wm.unpinDetail') : undefined, icon: 'pushpin', onSelect: () => keep(widgets.map((x) => (x.id === w.id ? { ...x, pinned: !x.pinned } : x))) })
  const drop1 = (w: WidgetSpec): MenuItem => ({ label: t('wm.remove'), icon: 'x', onSelect: () => keep(widgets.filter((x) => x.id !== w.id)) })
  const widgetMenu = (w: WidgetSpec): MenuItem[] => {
    const e = entity(w.entity)
    if (w.kind === 'character' && e) {
      const p = itemOf(e)?.data.pronouns ?? 'they'
      return [
        { label: t('wm.open', { name: e.name }), icon: 'user', onSelect: () => onOpen(e.id) },
        { label: t('cc.answer', { p }), icon: 'chat', disabled: !e.present, onSelect: () => onAnswer(e.id) },
        { label: t(e.present ? 'cc.away' : 'wm.back', { p }), icon: 'arrow', onSelect: () => onMove(e.id) },
        pin(w), { divider: true }, drop1(w),
      ]
    }
    if (w.kind === 'clock') return [
      { label: t('wm.pass'), icon: 'clock', disabled: busy, onSelect: onPassTime },
      { label: t('wm.realDate'), detail: fullTime(story.clock, story.date), icon: 'eye', onSelect: () => toast(fullTime(story.clock, story.date), {}, 5000) },
      { label: t('wm.setTime'), icon: 'refresh', onSelect: onSetTime },
      { divider: true }, drop1(w),
    ]
    return [pin(w), { label: t('wm.move'), icon: 'drag', shortcut: ['Space'], onSelect: onArrange }, { divider: true }, drop1(w), { label: t('wm.all'), icon: 'grid', shortcut: ['Ctrl', 'E'], onSelect: onArrange }]
  }
  const add = (kind: Kind, entityId?: number) => edit([...widgets, { id: `${kind}${entityId ?? ''}-${Date.now()}`, kind, entity: entityId, pinned: true }])
  const addMenu = (el: Element) => openMenu(el, [
    ...everyone.filter((e) => !widgets.some((w) => w.entity === e.id)).map((e) => ({ label: e.name, detail: t('w.k.characterSub'), icon: 'user' as const, onSelect: () => add('character', e.id) })),
    ...(['clock', 'place', 'cast', 'notes'] as Kind[]).filter((k) => !widgets.some((w) => w.kind === k)).map((k) => ({
      label: t(`w.k.${k}` as Key), detail: t(`w.k.${k}Sub` as Key), icon: ({ clock: 'clock', place: 'image', cast: 'users', notes: 'edit' } as const)[k as 'clock'], onSelect: () => add(k),
    })),
  ], t('w.addTitle'))

  const cell = (w: WidgetSpec) => {
    const pos = at(w)
    return (
      <div key={w.id} className={`wcell${editing ? ' is-edit' : ''}${picked === w.id ? ' is-picked' : ''}`} tabIndex={editing ? 0 : undefined}
        onContextMenu={editing ? undefined : (e) => { e.preventDefault(); openMenu(e, widgetMenu(w)) }}
        style={pos ? { position: 'fixed', left: pos.x, top: pos.y, zIndex: moving?.id === w.id ? 30 : 26 } : undefined}
        onPointerDown={editing ? (e) => {
          if ((e.target as Element).closest('button')) return
          const r = e.currentTarget.getBoundingClientRect()
          start.current = { px: e.clientX, py: e.clientY, x: r.left, y: r.top }
          e.currentTarget.setPointerCapture(e.pointerId)
          setMoving({ id: w.id, x: r.left, y: r.top })
        } : undefined}
        onPointerMove={editing ? (e) => { const s = start.current; if (s && moving?.id === w.id) setMoving({ id: w.id, x: s.x + e.clientX - s.px, y: s.y + e.clientY - s.py }) } : undefined}
        onPointerUp={editing ? () => { if (moving?.id === w.id) drop(w.id, moving.x, moving.y); setMoving(null); start.current = undefined } : undefined}
        onKeyDown={editing ? (e) => {
          const r = e.currentTarget.getBoundingClientRect()
          if (e.key === ' ') { e.preventDefault(); setPicked(picked === w.id ? undefined : w.id); return }
          if (e.key === 'Escape' && picked === w.id) { e.preventDefault(); e.stopPropagation(); setPicked(undefined); return }
          const step = e.shiftKey ? 64 : STEP
          const d = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[e.key]
          if (d && picked === w.id) { e.preventDefault(); drop(w.id, r.left + d[0], r.top + d[1]) }
        } : undefined}>
        {body(w)}
      </div>
    )
  }
  const shown = widgets.filter(visible)
  // below 1280 (R1) everyone is a row and the clock and music join them in one column
  const right = shown.filter((w) => !w.at && (compact || w.kind === 'character'))
  const left = compact ? [] : shown.filter((w) => !w.at && w.kind !== 'character')
  const free = shown.filter((w) => w.at)
  return (
    <>
      {editing && (
        <>
          <div className="dots" />
          <div className="editbar" role="region" aria-label={t('w.editing')}>
            <K.Icon name="layers" size={18} />
            <div style={{ flex: 1 }}><b style={{ fontSize: 14 }}>{t('w.editing')}</b><div className="scene-t">{t('w.editHint')}</div></div>
            <button type="button" className="k-btn k-btn--scene-ghost" onClick={() => edit(defaults(people))}>{t('w.reset')}</button>
            <button type="button" className="k-btn k-btn--scene-ghost" style={{ display: 'inline-flex', gap: 6 }} onClick={(e) => addMenu(e.currentTarget)}>
              <K.Icon name="plus" size={14} />{t('w.add')}
            </button>
            <button type="button" className="k-btn k-btn--scene-send" onClick={() => { onSave({ widgets }); setDraft(undefined); onDone() }}>{t('w.done')}</button>
          </div>
        </>
      )}
      <div className="scene__right">{right.map(cell)}</div>
      <div className="scene__left">{left.map(cell)}</div>
      {free.map(cell)}
    </>
  )
}
