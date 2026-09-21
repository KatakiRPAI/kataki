import { useState } from 'react'
import { api, type Link, type Same } from '../api'
import { diveLink, useAction, useLoad } from '../hooks'
import { Dialog, ErrorLine, Field, Icon } from '../ui'

/** What one story is to another, in the words the engine uses for it. */
const KINDS: [Link['kind'], string, string][] = [
  ['continuation', 'It carries on from there', 'They remember that story here, as far back as the gap allows.'],
  ['shared_universe', 'They share a world', 'The same world at the same time; what happened there is known here.'],
  ['reference', 'It only nods to it', 'Kept as a note. Nothing is remembered across it.'],
]

/** How much time lies between two stories, as a span rather than a direction: which way round
 *  they run is the link's, not the gap's. */
const GAPS: [number, string][] = [
  [0, 'No time at all'],
  [60, 'An hour'],
  [1440, 'A day'],
  [7 * 1440, 'A week'],
  [30 * 1440, 'A month'],
  [365 * 1440, 'A year'],
  [6 * 365 * 1440, 'Six years'],
]

/** Which side of this story the other one falls on. `back` means the story you asked from is the
 *  later of the two, so the one named on the row came before it. */
const between = (link: Link) => {
  if (!link.offset_min) return 'at the same time'
  const span = GAPS.find(([m]) => m === link.offset_min)?.[1] ?? `${Math.round(link.offset_min / 1440)} days`
  return `${span.toLowerCase()} ${link.direction === 'back' ? 'before' : 'after'} this`
}

/** Where else this person is, and the offer to tie those stories together. Given `here`, it ties
 *  them to the story you are in; without one, you pick both ends. */
export default function Elsewhere({ item, name, here, scene, onChange }: {
  item: number
  name: string
  here?: number
  scene?: boolean // the Scene has its own buttons; the Sky's are the wrong colour on its dark
  onChange?: () => void
}) {
  const btn = scene ? 'k-sbtn' : 'k-btn k-btn--sm'
  const go = scene ? 'k-sbtn ka-sbtn--primary' : 'k-btn k-btn--dark'
  const [same] = useLoad(() => api<Same[]>(`/library/${item}/same`), [item])
  const [links, reloadLinks] = useLoad(
    () => (here ? api<Link[]>(`/stories/${here}/links`) : Promise.resolve([] as Link[])),
    [here],
  )
  const [run, error, busy, forget] = useAction()
  const [tying, setTying] = useState<Same>()

  const theirs = same ?? []
  const others = theirs.filter((s) => s.story_id !== here)
  // a link either way ties the two stories: which looks back at which is the dialog's question
  const tied = (story: number) =>
    (links ?? []).find((l) => l.from_story_id === story || l.to_story_id === story)

  const close = () => {
    setTying(undefined)
    forget()
  }
  const tie = (to: Same, form: HTMLFormElement) =>
    run(async () => {
      const data = new FormData(form)
      const kind = String(data.get('kind')) as Link['kind']
      const offset_min = Number(data.get('gap'))
      const back = data.get('way') === 'back' // this story carries on from theirs
      const [from_story_id, to_story_id] = back ? [here!, to.story_id] : [to.story_id, here!]
      await api(`/stories/${from_story_id}/links`, 'POST', { to_story_id, kind, offset_min })
      close()
      reloadLinks()
      onChange?.()
    })
  const untie = (link: Link) =>
    run(async () => {
      await api(`/links/${link.id}`, 'DELETE')
      reloadLinks()
      onChange?.()
    })

  if (same && others.length === 0)
    return (
      <p className="ka-muted ka-small">
        {theirs.length === 0
          ? `${name} is not in a story yet.`
          : here
            ? `${name} is only in this story so far.`
            : `${name} is only in one story so far.`}
      </p>
    )

  return (
    <>
      <ul className="ka-elsewhere">
        {others.map((s) => {
          const link = here ? tied(s.story_id) : undefined
          return (
            <li key={s.story_id} className="ka-elsewhere__row">
              <span className="ka-elsewhere__text">
                <a className="ka-elsewhere__title ka-ellipsis" {...diveLink(`/story/${s.story_id}`)}>
                  {s.story}
                </a>
                <span className="ka-muted ka-small">
                  {s.is_ai ? `as ${s.name}` : `you, as ${s.name}`}
                  {s.remembers > 0 && ` · holds ${s.remembers} ${s.remembers === 1 ? 'thing' : 'things'}`}
                  {link && ` · ${between(link)}`}
                </span>
              </span>
              {here &&
                (link ? (
                  <button type="button" className={btn} disabled={busy}
                    onClick={() => untie(link)} title={KINDS.find(([k]) => k === link.kind)?.[1]}>
                    <Icon name="link" size={14} />
                    Tied
                  </button>
                ) : (
                  <button type="button" className={btn} disabled={busy}
                    onClick={() => { forget(); setTying(s) }}>
                    <Icon name="link" size={14} />
                    Tie them
                  </button>
                ))}
            </li>
          )
        })}
      </ul>
      <ErrorLine error={error} />

      <Dialog open={!!tying} onClose={close} title={`Tie this story to “${tying?.story ?? ''}”`}>
        <p className="ka-muted">
          Tied, {name} brings what they remember of one into the other — as much of it as the time
          between them has left them.
        </p>
        <form
          className="ka-form"
          onSubmit={(e) => {
            e.preventDefault()
            if (tying) tie(tying, e.currentTarget)
          }}
        >
          <Field label="Which way">
            <select name="way" className="k-select" defaultValue="back">
              <option value="back">This story comes after “{tying?.story}”</option>
              <option value="forward">“{tying?.story}” comes after this one</option>
            </select>
          </Field>
          <Field label="What it is">
            <select name="kind" className="k-select" defaultValue="continuation">
              {KINDS.map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </Field>
          <Field label="How long between them">
            <select name="gap" className="k-select" defaultValue="0">
              {GAPS.map(([minutes, label]) => (
                <option key={minutes} value={minutes}>{label}</option>
              ))}
            </select>
          </Field>
          <ErrorLine error={error} />
          <div className="ka-row ka-row--end">
            <button type="button" className={btn} onClick={close}>Cancel</button>
            <button type="submit" className={go} disabled={busy}>Tie them together</button>
          </div>
        </form>
      </Dialog>
      {same && others.length > 0 && !here && (
        <p className="ka-muted ka-small">
          Open one of these stories to tie it to another {name} is in.
        </p>
      )}
      {!same && <p className="ka-muted ka-small">Looking…</p>}
    </>
  )
}
