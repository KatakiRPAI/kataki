// How a line is read (SCENE.md › How a line is read, P7). A parser, not a model: the markers
// are *do*, (whisper), _think_ and a leading > to narrate; plain text is said.
// A whole-line thought or whisper wins (punctuation outside the markers doesn't count); a line
// that mixes them is read span by span: *acts* and _thoughts_ inside what is said.
export type Mode = 'Auto' | 'Say' | 'Do' | 'Whisper' | 'Think' | 'Narrate'
export type Reading = { mode: Exclude<Mode, 'Auto'>; text: string; detected: string }

/** Spans inside a line. `_x_` only at word edges, so snake_case and a_b stay words. */
export const ACT = /\*([^*\n]+)\*/g
export const THINK = /(?<![\w*])_([^_\n]+?)_(?!\w)/g
const PUNCT = /^[\s.,!?;:…"'“”‘’—–-]*$/u
const WHISPER = /^\(([\s\S]+)\)([.,!?…]*)$/
const has = (re: RegExp, s: string) => s.search(re) >= 0 // search ignores a /g regex's lastIndex

/** What Auto makes of a line, and the label it shows ("Do + Say + Think"). */
export function read(line: string): Reading {
  const text = line.trim()
  if (text.startsWith('>')) return { mode: 'Narrate', text: text.replace(/^>+\s*/, ''), detected: 'Narrate' }
  const w = WHISPER.exec(text)
  if (w) return { mode: 'Whisper', text: (w[1].trim() + w[2]).trim(), detected: 'Whisper' }
  const acts = has(ACT, text)
  const thinks = has(THINK, text)
  const said = text.replace(ACT, '').replace(THINK, '')
  if (thinks && !acts && PUNCT.test(said)) return { mode: 'Think', text: text.replace(THINK, '$1'), detected: 'Think' }
  const says = !PUNCT.test(said)
  const detected = [acts && 'Do', says && 'Say', thinks && 'Think'].filter(Boolean).join(' + ')
  return { mode: acts ? 'Do' : 'Say', text, detected }
}

/** A line cut into its spans with the markers kept, for where the text must stay as typed
 *  (the composer's highlight layer sits over the very same characters). */
const MARK = new RegExp(`${ACT.source}|${THINK.source}`, 'g')
export function spans(line: string): { text: string; as?: 'act' | 'think' }[] {
  const out: { text: string; as?: 'act' | 'think' }[] = []
  let at = 0
  for (const m of line.matchAll(MARK)) {
    if (m.index > at) out.push({ text: line.slice(at, m.index) })
    out.push({ text: m[0], as: m[0][0] === '*' ? 'act' : 'think' })
    at = m.index + m[0].length
  }
  if (at < line.length) out.push({ text: line.slice(at) })
  return out
}

/** A mode picked from the menu, for this line only. */
export function force(line: string, mode: Mode): Reading {
  const auto = read(line)
  if (mode === 'Auto') return auto
  const text = ['Think', 'Whisper', 'Narrate'].includes(auto.mode) ? auto.text : line.trim()
  return { mode, text: mode === 'Do' && !has(ACT, text) ? `*${text}*` : text, detected: mode }
}

/** How a stored line was meant, from what the engine keeps: no speaker = narration,
 *  an empty audience = a thought, a named audience = a whisper; otherwise it was said aloud. */
export function kind(m: { speaker_id: number | null; audience?: number[] | null }): 'narrate' | 'think' | 'whisper' | undefined {
  if (m.speaker_id === null) return 'narrate'
  if (m.audience?.length === 0) return 'think'
  if (m.audience?.length) return 'whisper'
}
