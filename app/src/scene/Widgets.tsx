import { useEffect, useRef, useState, type CSSProperties, type PointerEvent, type ReactNode } from 'react'
import type { CastEntity, Expression, Item, Story, StoryUi, WidgetSpec } from '../api'
import { Avatar, Figure, MIDDAY, Room, SunArc, timeOfDay, type TimeOfDay } from '../art'
import { fullTime, twelve } from '../hooks'
import { Icon } from '../ui'

/** The place behind everything, blurred and dimmed under the chat. Relighting crossfades two
 *  stacked rooms over 600 ms, opacity only (1.5). */
export function Place({ item, minute }: { item?: Item; minute: number }) {
  const tod = timeOfDay(minute)
  const [leaving, setLeaving] = useState<TimeOfDay>()
  const lit = useRef(tod)
  useEffect(() => {
    if (lit.current === tod) return
    setLeaving(lit.current)
    lit.current = tod
    const done = setTimeout(() => setLeaving(undefined), 600)
    return () => clearTimeout(done)
  }, [tod])
  return (
    <div className="k-place ka-backdrop">
      <Room item={item} minute={minute} />
      {leaving && <Room key={leaving} item={item} minute={MIDDAY[leaving]} className="ka-room--leaving" />}
      <span className="k-place__vignette" />
    </div>
  )
}

/** The chip under a character's name: the face they last spoke with, coloured by feeling. */
const FACES: Record<Expression, [string, string]> = {
  neutral: ['calm', 'var(--k-scene-sage)'],
  smiling: ['smiling', 'var(--k-scene-sage)'],
  wary: ['wary', 'var(--k-scene-rose)'],
  surprised: ['surprised', 'var(--k-scene-sky)'],
  doubtful: ['doubtful', 'var(--k-scene-lilac)'],
}

/** Where a character's card opens: beside the widget, on whichever side has room. */
const beside = (el: Element) => {
  const box = el.getBoundingClientRect()
  return { x: box.left > innerWidth / 2 ? box.left - 448 : box.right + 16, y: box.top + 120 }
}

const ADDABLE: [WidgetSpec['kind'], string, string, string][] = [
  ['character', 'user', 'Character', 'Pick who. Add as many as you like.'],
  ['clock', 'clock', 'Story clock', 'Time, and how it relates to the story'],
  ['place', 'image', 'Place', 'The scene, full colour'],
  ['cast', 'users', 'Cast', 'Everyone here, as faces'],
  ['notes', 'edit', 'Notes', 'Your own notes for this story'],
  ['nearby', 'users', 'Could join', 'Who might come in next'],
]

// "Could join" is one widget, not a character, so removing it is remembered by this stand-in
// in `dismissed` (which otherwise holds the characters whose widget you removed)
const NEARBY_OFF = -1

/** Before you arrange anything: a widget for each character here, and the clock. */
const defaults = (people: CastEntity[]): WidgetSpec[] => [
  ...people.map((e): WidgetSpec => ({ id: `c${e.id}`, kind: 'character', entity: e.id, pinned: true })),
  { id: 'clock', kind: 'clock', pinned: true },
  { id: 'nearby', kind: 'nearby', pinned: true },
]

let made = 0
const freshId = (kind: string) => `${kind}-${Date.now().toString(36)}-${made++}`

/** Whether this character has a widget: one you placed, or the one everyone here gets unless you
 *  removed theirs. The same rule the board draws by. */
export function hasWidget(story: Story, people: CastEntity[], id: number): boolean {
  const widgets = story.ui.widgets ?? defaults(people)
  if (widgets.some((w) => w.kind === 'character' && w.entity === id)) return true
  return people.some((e) => e.id === id) && !(story.ui.dismissed ?? []).includes(id)
}

/** The layout with a pinned widget for this character added (the card's "Add as widget"). */
export function withCharacter(story: Story, people: CastEntity[], id: number): Partial<StoryUi> {
  const widgets = story.ui.widgets ?? defaults(people)
  return {
    widgets: [...widgets, { id: freshId('character'), kind: 'character', entity: id, pinned: true }],
    dismissed: (story.ui.dismissed ?? []).filter((x) => x !== id),
  }
}

type Grab = Record<'onPointerDown' | 'onPointerMove' | 'onPointerUp', (e: PointerEvent<HTMLElement>) => void>
type Box = { left: number; top: number; width: number; height: number }
type Drag = { id: string; dx: number; dy: number; x: number; y: number; slot: Box; others: Box[]; guides: { x?: number; y?: number } }

const SNAP = 6 // px: how close an edge or centre must come to another's to line up with it

/** Line a dragged box up with the others: the nearest edge or centre within SNAP, per axis. */
function snap(x: number, y: number, w: number, h: number, others: Box[]) {
  let best = { x, y, gx: undefined as number | undefined, gy: undefined as number | undefined, dx: SNAP + 1, dy: SNAP + 1 }
  for (const o of others) {
    for (const [mine, theirs] of [[x, o.left], [x + w / 2, o.left + o.width / 2], [x + w, o.left + o.width], [x, o.left + o.width], [x + w, o.left]])
      if (Math.abs(mine - theirs) < best.dx) best = { ...best, x: x + theirs - mine, gx: theirs, dx: Math.abs(mine - theirs) }
    for (const [mine, theirs] of [[y, o.top], [y + h / 2, o.top + o.height / 2], [y + h, o.top + o.height], [y, o.top + o.height], [y + h, o.top]])
      if (Math.abs(mine - theirs) < best.dy) best = { ...best, y: y + theirs - mine, gy: theirs, dy: Math.abs(mine - theirs) }
  }
  return { x: best.x, y: best.y, guides: { x: best.gx, y: best.gy } }
}

/** Every widget around the chat, and Edit widgets: drag anywhere, pin, remove, add, reset. The
 *  layout is the story's (saved on Done); new arrivals get a widget of their own, unpinned once
 *  you have made a layout, unless you removed theirs. */
export function WidgetBoard({ story, people, everyone, itemOf, faces, stateOf, arriving, chapter, rolling, passTime, nearby, editing, onDone, onPeek, onSave }: {
  story: Story
  people: CastEntity[] // the AI characters here, lead first
  everyone: CastEntity[] // every AI character in the story, here or not
  itemOf: (e: { lib_item_id: number | null }) => Item | undefined
  faces: Map<number, Expression>
  stateOf: (id: number) => 'thinking' | 'writing' | undefined
  arriving?: number
  chapter?: string
  rolling: boolean
  passTime: ReactNode
  nearby: (shown: number[]) => ReactNode // who could come in, for the "Could join" widget
  editing: boolean
  onDone: () => void
  onPeek: (id: number, at: { x: number; y: number }) => void
  onSave: (ui: Partial<StoryUi>) => void
}) {
  const saved = story.ui.widgets
  const [draft, setDraft] = useState<{ widgets: WidgetSpec[]; dismissed: number[] } | null>(null)
  const base = draft ?? { widgets: saved ?? defaults(people), dismissed: story.ui.dismissed ?? [] }
  const widgets = [...base.widgets]
  for (const e of people)
    if (!widgets.some((w) => w.kind === 'character' && w.entity === e.id) && !base.dismissed.includes(e.id))
      widgets.push({ id: `c${e.id}`, kind: 'character', entity: e.id, pinned: !saved })
  if (!widgets.some((w) => w.kind === 'nearby') && !base.dismissed.includes(NEARBY_OFF))
    widgets.push({ id: 'nearby', kind: 'nearby', pinned: true }) // layouts saved before it existed

  // editing works on a draft of what is on screen; Done saves it, and Esc is Done
  useEffect(() => {
    setDraft(editing ? { widgets, dismissed: base.dismissed } : null)
    setAdding(null)
  }, [editing]) // eslint-disable-line react-hooks/exhaustive-deps
  const done = () => {
    if (draft) onSave(draft)
    onDone()
  }
  const doneRef = useRef(done)
  doneRef.current = done
  useEffect(() => {
    if (!editing) return
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && doneRef.current()
    addEventListener('keydown', esc)
    return () => removeEventListener('keydown', esc)
  }, [editing])
  const change = (fn: (ws: WidgetSpec[]) => WidgetSpec[], dismissed?: (d: number[]) => number[]) =>
    setDraft((d) => d && { widgets: fn(d.widgets), dismissed: dismissed ? dismissed(d.dismissed) : d.dismissed })
  const [adding, setAdding] = useState<'list' | 'who' | null>(null)
  const add = (kind: WidgetSpec['kind'], entity?: number) => {
    const off = kind === 'nearby' ? NEARBY_OFF : entity
    change((ws) => [...ws, { id: freshId(kind), kind, entity, pinned: true, at: freeSpot() }], (d) => d.filter((id) => id !== off))
    setAdding(null)
  }
  // a new widget lands on top, in the first gap clear of the others and the chat, not tucked
  // behind a widget you placed
  const freeSpot = () => {
    const s = layer.current!.getBoundingClientRect()
    const taken = [...document.querySelectorAll('.ka-widget, .k-chat, .ka-editbar, .ka-addwidget')].map((el) => el.getBoundingClientRect())
    const clear = (x: number, y: number) => !taken.some((r) => x < r.right && x + 272 > r.left && y < r.bottom && y + 180 > r.top)
    for (let y = s.top + 84; y < s.bottom - 180; y += 24)
      for (let x = s.left + 24; x < s.right - 296; x += 24)
        if (clear(x, y)) return { x: (x - s.left) / s.width, y: (y - s.top) / s.height }
    return { x: 0.5 - 136 / s.width, y: 0.3 }
  }

  // dragging: the widget follows the pointer, its old place shows as an empty slot, and where it
  // lands is kept as a fraction of the window so it holds at any size
  const layer = useRef<HTMLDivElement>(null)
  const [drag, setDrag] = useState<Drag | null>(null)
  const grab = (w: WidgetSpec): Grab => ({
    onPointerDown: (e: PointerEvent<HTMLElement>) => {
      if (!editing || e.button !== 0 || (e.target as Element).closest('.k-widget__edit')) return
      const r = e.currentTarget.getBoundingClientRect()
      const s = layer.current!.getBoundingClientRect()
      e.currentTarget.setPointerCapture(e.pointerId)
      const at = { left: r.left - s.left, top: r.top - s.top, width: r.width, height: r.height }
      const others = [...document.querySelectorAll('.ka-widget')].filter((el) => el !== e.currentTarget).map((el) => {
        const o = el.getBoundingClientRect()
        return { left: o.left - s.left, top: o.top - s.top, width: o.width, height: o.height }
      })
      setDrag({ id: w.id, dx: e.clientX - r.left, dy: e.clientY - r.top, x: at.left, y: at.top, slot: at, others, guides: {} })
    },
    onPointerMove: (e: PointerEvent<HTMLElement>) => {
      if (drag?.id !== w.id) return
      const s = layer.current!.getBoundingClientRect()
      const lined = snap(e.clientX - s.left - drag.dx, e.clientY - s.top - drag.dy, drag.slot.width, drag.slot.height, drag.others)
      setDrag({ ...drag, ...lined })
    },
    onPointerUp: () => {
      if (drag?.id !== w.id) return
      const s = layer.current!.getBoundingClientRect()
      const x = Math.max(0, Math.min(drag.x, s.width - drag.slot.width))
      const y = Math.max(0, Math.min(drag.y, s.height - 60))
      change((ws) => ws.map((v) => (v.id === w.id ? { ...v, at: { x: x / s.width, y: y / s.height } } : v)))
      setDrag(null)
    },
  })

  const render = (w: WidgetSpec) => {
    const who = w.entity === undefined ? undefined : everyone.find((e) => e.id === w.entity)
    if (w.kind === 'character' && !who) return null // no longer in the story
    const here = !!who && people.some((e) => e.id === who.id)
    const dragging = drag?.id === w.id
    const style: CSSProperties | undefined = dragging
      ? { left: drag.x, top: drag.y }
      : w.at ? ({ '--x': w.at.x, '--y': w.at.y } as CSSProperties) : undefined
    const frame = { w, editing, dragging, style, grab: grab(w) }
    const flip = (ws: WidgetSpec[]) => ws.map((v) => (v.id === w.id ? { ...v, pinned: !v.pinned } : v))
    const toggle = () => (editing ? change(flip) : onSave({ widgets: flip(widgets), dismissed: base.dismissed }))
    const gone = w.kind === 'nearby' ? NEARBY_OFF : w.kind === 'character' ? w.entity : undefined
    const remove = () => change((ws) => ws.filter((v) => v.id !== w.id), (d) => (gone !== undefined ? [...d, gone] : d))
    const edit = { onPin: toggle, onRemove: remove }
    if (w.kind === 'character' && who && !here) {
      return (
        <Frame key={w.id} {...frame} {...edit} label={who.name} pulse="" row>
          <button type="button" className="ka-cwidget ka-cwidget--row" tabIndex={editing ? -1 : 0}
            onClick={(e) => onPeek(who.id, beside(e.currentTarget))}>
            <Avatar item={itemOf(who)} name={who.name} size={40} />
            <span className="ka-nearby__who">
              <strong>{who.name}</strong>
              <span>away</span>
            </span>
          </button>
        </Frame>
      )
    }
    if (w.kind === 'character' && who) {
      const state = stateOf(who.id)
      const face = faces.get(who.id)
      const [word, color] = state ? [`${state}…`, 'var(--k-scene-sky)'] : face ? FACES[face] : []
      const line = (itemOf(who)?.description || who.summary).split('\n')[0]
      const joined = who.id === arriving
      return (
        <Frame key={w.id} {...frame} {...edit} label={who.name} pulse={`${face}|${state}|${joined}|${w.pinned}`} wake={joined} pin>
          <button type="button" className={`ka-cwidget${joined ? ' is-joined' : ''}`} aria-label={`${who.name}: open their card`}
            tabIndex={editing ? -1 : 0} onClick={(e) => onPeek(who.id, beside(e.currentTarget))}>
            <span className="k-widget__art ka-cwidget__art">
              <Figure item={itemOf(who)} name={who.name} expression={face} />
              {joined && <span className="ka-cwidget__joined">Joined</span>}
            </span>
            <span className="ka-cwidget__body">
              <span className="ka-cwidget__name">
                {who.name}
                {word && <span className="k-expr" style={{ '--c': color } as CSSProperties}>{word}</span>}
              </span>
              {line && <span className="ka-cwidget__line">{line}</span>}
            </span>
          </button>
        </Frame>
      )
    }
    if (w.kind === 'clock') {
      return (
        <Frame key={w.id} {...frame} {...edit} label="Story clock" pulse={story.clock} className="ka-clock">
          <span className="ka-clock__top">
            <span key={story.clock} className={`k-clock__time ka-clock__time${rolling ? ' is-rolling' : ''}`} tabIndex={0}
              data-tip={fullTime(story.clock, story.date)}>
              {twelve(story.clock)}
            </span>
            <SunArc minute={story.minute_of_day} />
          </span>
          <strong className="ka-clock__label">{story.date}</strong>
          <span className="ka-clock__foot">
            <span>{[story.place?.name ?? 'Nowhere yet', chapter].filter(Boolean).join(' · ')}</span>
            {passTime}
          </span>
        </Frame>
      )
    }
    if (w.kind === 'place')
      return (
        <Frame key={w.id} {...frame} {...edit} label="Place" pulse={String(story.place?.id)} className="ka-placewidget">
          <span className="ka-placewidget__room"><Room item={story.place ? itemOf(story.place) : undefined} minute={story.minute_of_day} /></span>
          <strong>{story.place?.name ?? 'Nowhere yet'}</strong>
        </Frame>
      )
    if (w.kind === 'nearby')
      return (
        <Frame key={w.id} {...frame} {...edit} label="Could join" pulse="" className="ka-nearbywidget">
          <span className="ka-castwidget__title">Could join</span>
          {nearby(widgets.flatMap((v) => (v.kind === 'character' && v.entity !== undefined ? [v.entity] : [])))}
        </Frame>
      )
    if (w.kind === 'cast')
      return (
        <Frame key={w.id} {...frame} {...edit} label="Cast" pulse={people.map((e) => e.id).join()} className="ka-castwidget">
          <span className="ka-castwidget__title">Here</span>
          <span className="ka-castwidget__faces">
            {people.map((e) => (
              <button key={e.id} type="button" aria-label={`${e.name}: open their card`} tabIndex={editing ? -1 : 0}
                onClick={(c) => onPeek(e.id, beside(c.currentTarget))}>
                <Avatar item={itemOf(e)} name={e.name} size={40} />
              </button>
            ))}
            {!people.length && <span className="ka-muted">No one but you</span>}
          </span>
        </Frame>
      )
    return (
      <Frame key={w.id} {...frame} {...edit} label="Notes" pulse="" className="ka-noteswidget">
        <label className="ka-castwidget__title" htmlFor={w.id}>Notes</label>
        <textarea id={w.id} key={story.ui.notes} defaultValue={story.ui.notes ?? ''} rows={4} placeholder="Anything you want to keep in mind…"
          tabIndex={editing ? -1 : 0} onBlur={(e) => e.target.value !== (story.ui.notes ?? '') && onSave({ notes: e.target.value })} />
      </Frame>
    )
  }

  const free = widgets.filter((w) => w.at || drag?.id === w.id)
  const column = (left: boolean) => widgets.filter((w) => !free.includes(w) && (w.kind === 'clock') === left)
  return (
    <>
      <aside className="ka-widgets ka-widgets--right" aria-label="Widgets">
        {column(false).map(render)}
      </aside>
      <aside className="ka-widgets ka-widgets--left" aria-label="More widgets">{column(true).map(render)}</aside>
      <div className="ka-widgets ka-widgets--free" ref={layer}>
        {drag && <span className="k-widget-slot" style={drag.slot} />}
        {drag?.guides.x !== undefined && <span className="ka-guide ka-guide--v" style={{ left: drag.guides.x }} />}
        {drag?.guides.y !== undefined && <span className="ka-guide ka-guide--h" style={{ top: drag.guides.y }} />}
        {free.map(render)}
      </div>
      {editing && (
        <>
          <div className="ka-editbar k-sglass" role="toolbar" aria-label="Editing widgets">
            <Icon name="layers" size={16} />
            <strong>Editing widgets</strong>
            <span className="ka-editbar__hint">Drag anywhere · pinned ones stay visible, unpinned ones appear when something happens</span>
            <button type="button" className="k-sbtn" onClick={() => setDraft({ widgets: defaults(people), dismissed: [] })}>Reset layout</button>
            <button type="button" className="k-send" onClick={done}>Done</button>
          </div>
          <div className="ka-addwidget">
            <button type="button" className="ka-addwidget__open" aria-expanded={!!adding} onClick={() => setAdding((a) => (a ? null : 'list'))}>
              <Icon name="plus" size={15} />
              Add widget
            </button>
            {adding && (
              <div className="k-menu ka-addwidget__menu" role="menu" aria-label="Add a widget">
                <strong className="ka-addwidget__title">Add a widget</strong>
                {ADDABLE.map(([kind, icon, name, what]) => (
                  <button key={kind} type="button" role="menuitem" className="ka-modeitem" aria-checked={kind === 'character' && adding === 'who'}
                    onClick={() => (kind === 'character' ? setAdding('who') : add(kind))}>
                    <span className="ka-modeitem__icon"><Icon name={icon} size={16} /></span>
                    <span className="ka-modeitem__what"><strong>{name}</strong><small>{what}</small></span>
                    <Icon name="plus" size={14} />
                  </button>
                ))}
                {adding === 'who' && (
                  <div className="ka-addwidget__who" role="group" aria-label="Character widget for">
                    <span>Character widget for…</span>
                    <span className="ka-row">
                      {everyone.map((e) => (
                        <button key={e.id} type="button" className="k-sbtn ka-pick" onClick={() => add('character', e.id)}>
                          <Avatar item={itemOf(e)} name={e.name} size={22} />
                          {e.name}
                        </button>
                      ))}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </>
  )
}

/** One widget: its card, the edit handles, and showing itself for a few seconds when something
 *  happens (`pulse` changes) if it is unpinned. `wake`: show on arrival too. */
function Frame({ w, editing, dragging, style, grab, label, pulse, wake, row, pin, className = '', onPin, onRemove, children }: {
  w: WidgetSpec
  editing: boolean
  dragging: boolean
  style?: CSSProperties
  grab: Grab
  label: string
  pulse: string
  wake?: boolean
  row?: boolean
  className?: string
  onPin: () => void
  onRemove: () => void
  pin?: boolean // a pin on the card itself, outside edit mode (character widgets)
  children: ReactNode
}) {
  const [showing, setShowing] = useState(false)
  const last = useRef<string | null>(wake ? null : pulse)
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined)
  useEffect(() => {
    if (last.current === pulse) return
    last.current = pulse
    setShowing(true)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setShowing(false), 6000)
  }, [pulse])
  useEffect(() => () => clearTimeout(timer.current), [])
  const classes = ['k-widget', 'ka-widget', row && 'k-widget--row', !w.pinned && 'is-unpinned', showing && 'is-showing', dragging && 'is-dragging', w.at && 'is-placed', className]
  return (
    <section className={classes.filter(Boolean).join(' ')} style={style} aria-label={label} {...grab}>
      {editing && (
        <>
          <span className="k-widget__handle" aria-hidden="true"><Icon name="drag" size={14} /></span>
          <span className="k-widget__edit">
            <button type="button" aria-pressed={w.pinned} aria-label={w.pinned ? `Unpin ${label}` : `Pin ${label}`} onClick={onPin}>
              <Icon name="pushpin" size={14} />
            </button>
            <button type="button" className="is-remove" aria-label={`Remove ${label}`} onClick={onRemove}>
              <Icon name="x" size={14} />
            </button>
          </span>
        </>
      )}
      {pin && !editing && (
        <button type="button" className="k-widget__pin" aria-pressed={w.pinned} aria-label={w.pinned ? `Unpin ${label}` : `Pin ${label}`}
          title={w.pinned ? 'Pinned: always shown' : 'Unpinned: shows when something happens'} onClick={onPin}>
          <Icon name="pushpin" size={14} />
        </button>
      )}
      {children}
    </section>
  )
}
