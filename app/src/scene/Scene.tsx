import { useEffect, useRef } from 'react'
import { api, type Cast, type CastEntity, type Message, type Story, type Version } from '../api'
import { SunArc } from '../art'
import { href, rise, useLoad, usePoll } from '../hooks'
import { ErrorLine, Icon, Menu } from '../ui'
import Lines from './Lines'
import Stage from './Stage'

/** Who is on stage: the AI characters present, the last to speak first. */
function onStage(cast: Cast, messages: Message[]): CastEntity[] {
  const present = cast.entities.filter((e) => e.present && e.is_ai && e.kind === 'character')
  const spoke = messages.findLast((m) => m.role === 'assistant' && present.some((e) => e.id === m.speaker_id))
  const lead = present.find((e) => e.id === spoke?.speaker_id) ?? present[0]
  return lead ? [lead, ...present.filter((e) => e !== lead)] : []
}

const listed = (names: string[]) => (names.length > 1 ? `${names.slice(0, -1).join(', ')} and ${names.at(-1)}` : names[0])

/** A story, played: the stage, the top bar and the conversation. */
export default function Scene({ id, line }: { id: number; line?: number }) {
  // One guarded load of everything the scene shows; every change calls it again.
  const [data, refreshAll, error] = useLoad(
    () =>
      Promise.all([
        api<Story>(`/stories/${id}`),
        api<Message[]>(`/stories/${id}/messages`),
        api<Cast>(`/stories/${id}/cast`),
      ]).then(([story, messages, cast]) => ({ story, messages, cast })),
    [id],
  )

  // Memory reads in the background: when the version moves, what the scene shows may have too.
  const version = useRef('')
  usePoll(() => {
    api<Version>(`/stories/${id}/version`).then(({ v }) => {
      if (version.current && v !== version.current) refreshAll()
      version.current = v
    }, () => {})
  }, 3000)

  // Open at the newest line, or at the deep-linked one.
  const convo = useRef<HTMLDivElement>(null)
  const count = data?.messages.length ?? 0
  useEffect(() => {
    const target = line ? document.getElementById(`line-${line}`) : null
    if (target) {
      target.scrollIntoView({ block: 'center' })
    } else if (convo.current) {
      convo.current.scrollTop = convo.current.scrollHeight
    }
  }, [line, count])

  if (!data) {
    return (
      <div className="k-scene ka-scene">
        <ErrorLine error={error} />
      </div>
    )
  }
  const { story, messages, cast } = data
  const people = onStage(cast, messages)
  const missing = !!line && !messages.some((m) => m.id === line)
  const who = [
    people.length ? `with ${listed(people.map((e) => e.name))}` : 'alone',
    story.persona ? `as ${story.persona.name}` : 'directing',
  ].join(' · ')

  return (
    <div className="k-scene ka-scene">
      <Stage story={story} people={people} />
      <header className="k-topbar ka-topbar">
        <div className="ka-topbar__side">
          <button type="button" className="k-scene-round k-sglass" onClick={rise} aria-label="Float back up to the Sky">
            <Icon name="cloud" size={20} />
          </button>
          <div className="ka-topbar__title">
            <h1>{story.title}</h1>
            <span>{who}</span>
          </div>
        </div>
        <div className="k-scene-pill k-sglass">
          <SunArc minute={story.minute_of_day} />
          {story.place && <strong>{story.place.name}</strong>}
          <span className="ka-topbar__clock">{story.clock}</span>
        </div>
        <div className="ka-topbar__side ka-topbar__side--end">
          <Menu label="Story menu" className="k-scene-round k-sglass">
            <a href={href('/classic')}>Open in classic view</a>
          </Menu>
        </div>
      </header>
      <div className="k-convo-scrim" />
      <div className="k-convo ka-convo" ref={convo}>
        <Lines story={story} messages={messages} cast={cast} flash={line} onChange={refreshAll} />
        {missing && <p className="k-sysnote">That line is no longer in this version of the story.</p>}
        <ErrorLine error={error} />
      </div>
    </div>
  )
}
