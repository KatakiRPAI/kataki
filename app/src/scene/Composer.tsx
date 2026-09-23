import { useState, type CSSProperties } from 'react'
import { SKIPS, type CastEntity, type Story } from '../api'
import { Avatar } from '../art'
import { useLibrary } from '../hooks'
import { Icon, Menu } from '../ui'
import { readLine, type Mode, type Reading } from './auto'

export type Speaker = number | 'narrator' | null // null = whoever fits

/** What the composer asks for: a line and a reply (`reply`), or only a line (a thought, or time
 *  passing on its own). `narrate`: the user tells it, rather than their persona saying it. */
export type Send = { text: string | null; audience: number[] | null; skip: string | null; speaker: Speaker; reply: boolean; narrate: boolean }

export type Meter = { used: number; label: string }

/** Time to pass before the next line: [the words the engine reads, the label]. */
export type Skip = [string, string]

// the mode menu, as the design lists it: what it is, and how Auto spots it
const MODES: [Mode, string, string, string, string][] = [
  ['auto', 'spark', 'Auto', 'Reads your formatting', '*action* “speech” (thought)'],
  ['say', 'chat', 'Say', 'Speak out loud', 'plain text'],
  ['do', 'hand', 'Do', 'An action', '*like this*'],
  ['whisper', 'ear', 'Whisper', 'Only one person hears', '@Mira like this'],
  ['think', 'thought', 'Think', 'No one hears', '(like this)'],
  ['narrate', 'feather', 'Narrate', 'Direct the story', '>> like this'],
]

const listed = (names: string[]) =>
  names.length > 1 ? `${names.slice(0, -1).join(', ')} and ${names.at(-1)}` : (names[0] ?? '')

// Simple or Advanced is the user's, across stories; storage can be missing (private mode)
const KEY = 'kataki.composer.advanced'
const remembered = () => {
  try {
    return localStorage.getItem(KEY) === '1'
  } catch {
    return false
  }
}

/** Pass time: a few set steps, or years. Used by the composer's Advanced row and the clock. */
export function PassTime({ disabled, onPick, className = 'k-sbtn' }: { disabled: boolean; onPick: (s: Skip) => void; className?: string }) {
  const [years, setYears] = useState(6)
  return (
    <Menu label="Pass time" icon="clock" text="Pass time" className={className} disabled={disabled}>
      {SKIPS.map(([words, label]) => (
        <button key={words} type="button" onClick={() => onPick([words, label])}>{label}</button>
      ))}
      <div className="ka-years">
        <input type="number" min={1} max={99} value={years} aria-label="Years"
          onChange={(e) => setYears(Math.max(1, Math.min(99, Number(e.target.value) || 1)))} />
        <span>years later</span>
        <button type="button" onClick={() => onPick([`${years} years later`, `${years} years later`])}>Pass</button>
      </div>
    </Menu>
  )
}

/** Speak, act, whisper, think or narrate as the persona (or direct the story). Simple by default:
 *  the text, Continue, the mode chip and Send. Advanced adds who hears it, who answers, Pass time
 *  and the prompt's size. */
export default function Composer({ story, people, away, live, picked, onPick, skip, onSkip, writer, meter, onSend, onStop }: {
  story: Story
  people: CastEntity[] // the AI characters present
  away: CastEntity[] // the AI characters in the story but not here
  live: boolean
  picked: Speaker // who answers next; the character card sets it too, so the Scene owns it
  onPick: (s: Speaker) => void
  skip: Skip | null // time to pass first; the clock widget can set it too, so the Scene owns it
  onSkip: (s: Skip | null) => void
  writer: string // who is replying, for "Stopping keeps what Mira has written so far."
  meter?: Meter
  onSend: (s: Send) => void
  onStop: () => void
}) {
  const { byId } = useLibrary()
  const item = (e: CastEntity) => (e.lib_item_id ? byId.get(e.lib_item_id) : undefined)
  const [text, setText] = useState('')
  const [mode, setMode] = useState<Mode>('auto') // a pick other than Auto is for this line only
  const [whisperTo, setWhisperTo] = useState<number[]>([])
  const [advanced, setAdvanced] = useState(remembered)
  const speaker = typeof picked === 'number' && !people.some((e) => e.id === picked) ? null : picked

  const line = text.trim()
  const auto = readLine(line, people)
  const how: Reading = mode === 'auto' ? auto : { mode, text: line, label: '' }
  const audience =
    how.mode === 'think' ? []
    : how.mode === 'whisper' ? (how.to ? [how.to] : whisperTo.filter((id) => people.some((e) => e.id === id)))
    : null
  const hearers = audience === null ? people : people.filter((e) => audience.includes(e.id))
  const hears =
    how.mode === 'think' ? 'No one will hear this'
    : hearers.length === 0 ? (how.mode === 'whisper' ? 'Pick who hears the whisper' : 'No one is here to hear this')
    : hearers.length === 1 ? `Only ${hearers[0].name} will hear this`
    : `${listed(hearers.map((e) => e.name))} will hear this`
  const canSend = !live && (!!how.text || !!skip) && !(how.mode === 'whisper' && !audience?.length)

  const toggle = (on: boolean) => {
    setAdvanced(on)
    try {
      localStorage.setItem(KEY, on ? '1' : '0')
    } catch {
      /* not remembered, still switched */
    }
  }
  const choose = (m: Mode) => {
    setMode(m)
    if (m === 'whisper' && !whisperTo.length && people.length === 1) setWhisperTo([people[0].id])
  }
  const send = (s: Pick<Send, 'text' | 'audience' | 'reply'>, narrate = false) => {
    onSend({ ...s, skip: skip?.[0] ?? null, speaker, narrate })
    if (s.text) {
      setText('')
      setMode('auto')
    }
    onSkip(null)
  }
  const submit = () => {
    if (!canSend) return
    const said = how.text
    // a thought, or time passing with nothing said, is written without asking for a reply
    if (how.mode === 'think' || !said) send({ text: said || null, audience: said ? audience : null, reply: false })
    else if (how.mode === 'narrate') send({ text: said, audience: null, reply: true }, true)
    else send({ text: mode === 'do' && !/^\*[\s\S]*\*$/.test(said) ? `*${said}*` : said, audience, reply: true })
  }
  const proceed = () => send({ text: null, audience: null, reply: true })
  const chosen = MODES.find(([m]) => m === mode)!

  return (
    <div className={`k-composer ka-composer${advanced ? ' is-advanced' : ''}`}>
      <div className="k-composer__meter" role="img" aria-label={meter?.label ?? 'No prompt yet'} title={meter?.label}
        style={{ '--used': meter?.used ?? 0 } as CSSProperties}>
        <i />
      </div>
      <div className="k-composer__body">
        {advanced && (
          <div className="k-composer__advanced ka-composer__row ka-composer__top">
            <div className="ka-hears">
              {how.mode !== 'think' && hearers.length > 0 && (
                <span className="ka-hears__faces">
                  {hearers.map((e) => <Avatar key={e.id} item={item(e)} name={e.name} size={24} />)}
                </span>
              )}
              <span className="ka-hears__line">{hears}</span>
              {how.mode !== 'think' && away.length > 0 && (
                <span className="ka-away">
                  <Avatar item={item(away[0])} name={away[0].name} size={22} />
                  {listed(away.map((e) => e.name))} {away.length > 1 ? 'are' : 'is'} away
                </span>
              )}
            </div>
            <div className="ka-answers" role="group" aria-label="Who answers">
              <span className="ka-answers__label">Answers</span>
              <button type="button" className="k-sbtn" aria-pressed={speaker === null} onClick={() => onPick(null)}>
                <Icon name="users" size={14} />
                Whoever fits
              </button>
              {people.map((e) => (
                <button key={e.id} type="button" className="k-sbtn ka-pick" aria-pressed={speaker === e.id} onClick={() => onPick(e.id)}>
                  <Avatar item={item(e)} name={e.name} size={22} />
                  {e.name}
                </button>
              ))}
              <button type="button" className="k-sbtn" aria-pressed={speaker === 'narrator'} onClick={() => onPick('narrator')}>
                <Icon name="feather" size={14} />
                Narrator
              </button>
            </div>
          </div>
        )}
        {mode === 'whisper' && (
          <div className="ka-hears" role="group" aria-label="Who hears the whisper">
            {people.map((e) => (
              <button key={e.id} type="button" className="k-sbtn ka-pick" aria-pressed={whisperTo.includes(e.id)}
                onClick={() => setWhisperTo((w) => (w.includes(e.id) ? w.filter((id) => id !== e.id) : [...w, e.id]))}>
                <Avatar item={item(e)} name={e.name} size={22} />
                {e.name}
              </button>
            ))}
            {!people.length && <span className="ka-hears__line">No one is here to whisper to</span>}
          </div>
        )}
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
          <div className="ka-composer__actions">
            <div className="k-detail-toggle" role="group" aria-label="Composer detail">
              <button type="button" aria-pressed={!advanced} onClick={() => toggle(false)}>Simple</button>
              <button type="button" aria-pressed={advanced} onClick={() => toggle(true)}>Advanced</button>
            </div>
            <button type="button" className="ka-round" aria-label="Continue the story" title="Continue the story" disabled={live} onClick={proceed}>
              <Icon name="ff" size={15} />
            </button>
            {advanced && <PassTime disabled={live} onPick={onSkip} />}
            {skip && (
              <span className="k-sbtn ka-pending">
                <Icon name="clock" size={14} />
                {skip[1]}
                <button type="button" aria-label="Don't pass time" onClick={() => onSkip(null)}>
                  <Icon name="x" size={12} />
                </button>
              </span>
            )}
            {advanced && meter && <span className="ka-composer__tokens">{meter.label.split(' · ')[0]}</span>}
          </div>
          <div className="ka-composer__actions">
            <Menu label={`How you say it: ${mode === 'auto' ? `Auto${line ? `, ${auto.label}` : ''}` : chosen[2]}`} icon={chosen[1]}
              className="k-mode"
              text={
                <>
                  {chosen[2]}
                  {mode === 'auto' && line && <span className="k-mode__detected">· {auto.label}</span>}
                  <Icon name="down" size={12} />
                </>
              }>
              {MODES.map(([m, icon, label, what, syntax]) => (
                <button key={m} type="button" role="menuitemradio" aria-checked={mode === m} className="ka-modeitem" onClick={() => choose(m)}>
                  <span className="ka-modeitem__icon"><Icon name={icon} size={16} /></span>
                  <span className="ka-modeitem__what">
                    <strong>{label}</strong>
                    <small>{what}</small>
                  </span>
                  <code>{syntax}</code>
                  <span className="ka-modeitem__check">{mode === m && <Icon name="check" size={14} />}</span>
                </button>
              ))}
              <p className="ka-modeitem__foot">Auto works it out from how you write. Pick a mode to override it for this line.</p>
            </Menu>
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
        </div>
        {live && <span className="ka-composer__hint">Stopping keeps what {writer || 'they'} {writer ? 'has' : 'have'} written so far.</span>}
      </div>
    </div>
  )
}
