import { useState, type CSSProperties } from 'react'
import type { CastEntity, Story } from '../api'
import { Avatar } from '../art'
import { useLibrary } from '../hooks'
import { Icon, Menu } from '../ui'

type Mode = 'say' | 'do' | 'whisper' | 'think'
export type Speaker = number | 'narrator' | null // null = whoever fits

/** What the composer asks for: a line and a reply (`reply`), or only a line (a thought, or time
 *  passing on its own). */
export type Send = { text: string | null; audience: number[] | null; skip: string | null; speaker: Speaker; reply: boolean }

export type Meter = { used: number; label: string }

const MODES: [Mode, string, string][] = [
  ['say', 'chat', 'Say'],
  ['do', 'hand', 'Do'],
  ['whisper', 'ear', 'Whisper'],
  ['think', 'thought', 'Think'],
]

// Phrases the engine's clock reads (clock.parse_skip); the label is also the marker line.
const SKIPS: [string, string][] = [
  ['a few hours later', 'A few hours later'],
  ['the next morning', 'The next morning'],
  ['a week later', 'A week later'],
]

const listed = (names: string[]) =>
  names.length > 1 ? `${names.slice(0, -1).join(', ')} and ${names.at(-1)}` : (names[0] ?? '')

/** Speak, act, whisper or think as the persona (or direct the story); pass time; pick who answers. */
export default function Composer({ story, people, away, live, writer, meter, onSend, onStop }: {
  story: Story
  people: CastEntity[] // the AI characters present
  away: CastEntity[] // the AI characters in the story but not here
  live: boolean
  writer: string // who is replying, for "Stopping keeps what Mira has written so far."
  meter?: Meter
  onSend: (s: Send) => void
  onStop: () => void
}) {
  const { byId } = useLibrary()
  const item = (e: CastEntity) => (e.lib_item_id ? byId.get(e.lib_item_id) : undefined)
  const [text, setText] = useState('')
  const [mode, setMode] = useState<Mode>('say')
  const [whisperTo, setWhisperTo] = useState<number[]>([])
  const [skip, setSkip] = useState<[string, string] | null>(null)
  const [years, setYears] = useState(6)
  const [picked, setPicked] = useState<Speaker>(null)
  const speaker = typeof picked === 'number' && !people.some((e) => e.id === picked) ? null : picked

  const audience = mode === 'think' ? [] : mode === 'whisper' ? whisperTo.filter((id) => people.some((e) => e.id === id)) : null
  const hearers = audience === null ? people : people.filter((e) => audience.includes(e.id))
  const hears =
    mode === 'think' ? 'No one will hear this'
    : hearers.length === 0 ? (mode === 'whisper' ? 'Pick who hears the whisper' : 'No one is here to hear this')
    : hearers.length === 1 ? `Only ${hearers[0].name} will hear this`
    : `${listed(hearers.map((e) => e.name))} will hear this`
  const line = text.trim()
  const canSend = !live && (!!line || !!skip) && !(mode === 'whisper' && !audience?.length)

  const choose = (m: Mode) => {
    setMode(m)
    if (m === 'whisper' && !whisperTo.length && people.length === 1) setWhisperTo([people[0].id])
  }
  const send = (s: Pick<Send, 'text' | 'audience' | 'reply'>) => {
    onSend({ ...s, skip: skip?.[0] ?? null, speaker })
    if (s.text) setText('')
    setSkip(null)
  }
  const submit = () => {
    if (!canSend) return
    // a thought, or time passing with nothing said, is written without asking for a reply
    if (mode === 'think' || !line) send({ text: line || null, audience: line ? audience : null, reply: false })
    else send({ text: mode === 'do' && !/^\*[\s\S]*\*$/.test(line) ? `*${line}*` : line, audience, reply: true })
  }
  const proceed = () => send({ text: null, audience: null, reply: true })

  return (
    <div className="k-composer ka-composer">
      <div className="k-composer__meter" role="img" aria-label={meter?.label ?? 'No prompt yet'} title={meter?.label}
        style={{ '--used': meter?.used ?? 0 } as CSSProperties}>
        <i />
      </div>
      <div className="k-composer__body">
        <div className="ka-composer__row">
          <div className="ka-hears">
            {mode === 'whisper' ? (
              people.map((e) => (
                <button key={e.id} type="button" className="k-sbtn ka-pick" aria-pressed={whisperTo.includes(e.id)}
                  onClick={() => setWhisperTo((w) => (w.includes(e.id) ? w.filter((id) => id !== e.id) : [...w, e.id]))}>
                  <Avatar item={item(e)} name={e.name} size={22} />
                  {e.name}
                </button>
              ))
            ) : mode !== 'think' && hearers.length > 0 ? (
              <span className="ka-hears__faces">
                {hearers.map((e) => <Avatar key={e.id} item={item(e)} name={e.name} size={24} />)}
              </span>
            ) : null}
            <span className="ka-hears__line">{hears}</span>
            {mode !== 'think' && away.length > 0 && (
              <span className="ka-away">
                <Avatar item={item(away[0])} name={away[0].name} size={22} />
                {listed(away.map((e) => e.name))} {away.length > 1 ? 'are' : 'is'} away
              </span>
            )}
          </div>
          <div className="ka-composer__actions">
            {skip && (
              <span className="k-sbtn ka-pending">
                <Icon name="clock" size={14} />
                {skip[1]}
                <button type="button" aria-label="Don't pass time" onClick={() => setSkip(null)}>
                  <Icon name="x" size={12} />
                </button>
              </span>
            )}
            <Menu label="Pass time" icon="clock" text="Pass time" className="k-sbtn" disabled={live}>
              {SKIPS.map(([words, label]) => (
                <button key={words} type="button" onClick={() => setSkip([words, label])}>{label}</button>
              ))}
              <div className="ka-years">
                <input type="number" min={1} max={99} value={years} aria-label="Years"
                  onChange={(e) => setYears(Math.max(1, Math.min(99, Number(e.target.value) || 1)))} />
                <span>years later</span>
                <button type="button" onClick={() => setSkip([`${years} years later`, `${years} years later`])}>Pass</button>
              </div>
            </Menu>
            <button type="button" className="k-sbtn" disabled={live} onClick={proceed}>
              <Icon name="ff" size={15} />
              Continue
            </button>
          </div>
        </div>
        <label className="ka-composer__text">
          <span className="k-sr">Your line</span>
          <textarea
            rows={2}
            value={text}
            placeholder={story.persona ? `Speak or act as ${story.persona.name}…` : 'Direct the story…'}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault()
                submit()
              }
            }}
          />
        </label>
        <div className="ka-composer__row">
          <div className="k-modes" role="group" aria-label="How you say it">
            {MODES.map(([m, icon, label]) => (
              <button key={m} type="button" aria-pressed={mode === m} onClick={() => choose(m)}>
                <Icon name={icon} size={14} />
                {label}
              </button>
            ))}
          </div>
          {live ? (
            <button type="button" className="k-stop" onClick={onStop}>
              <Icon name="stop" size={16} />
              Stop
            </button>
          ) : (
            <button type="button" className="k-send" disabled={!canSend} onClick={submit}>
              Send
              <Icon name="send" size={16} />
            </button>
          )}
        </div>
        <div className="ka-composer__row ka-answers" role="group" aria-label="Who answers">
          <span className="ka-answers__label">Who answers</span>
          <button type="button" className="k-sbtn" aria-pressed={speaker === null} onClick={() => setPicked(null)}>
            <Icon name="users" size={14} />
            Whoever fits
          </button>
          {people.map((e) => (
            <button key={e.id} type="button" className="k-sbtn ka-pick" aria-pressed={speaker === e.id} onClick={() => setPicked(e.id)}>
              <Avatar item={item(e)} name={e.name} size={22} />
              {e.name}
            </button>
          ))}
          <button type="button" className="k-sbtn" aria-pressed={speaker === 'narrator'} onClick={() => setPicked('narrator')}>
            <Icon name="feather" size={14} />
            Narrator
          </button>
        </div>
        {live && <span className="ka-composer__hint">Stopping keeps what {writer || 'they'} {writer ? 'has' : 'have'} written so far.</span>}
      </div>
    </div>
  )
}
