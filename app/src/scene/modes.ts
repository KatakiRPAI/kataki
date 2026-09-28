// How a line is read (SCENE.md › How a line is read, P7). A parser, not a model: the markers
// are *do*, (whisper), _think_ and a leading > to narrate; plain text is said.
export type Mode = 'Auto' | 'Say' | 'Do' | 'Whisper' | 'Think' | 'Narrate'
export type Reading = { mode: Exclude<Mode, 'Auto'>; text: string; detected: string }

const WHOLE: [RegExp, Reading['mode']][] = [[/^\((.+)\)$/s, 'Whisper'], [/^_(.+)_$/s, 'Think'], [/^\*([^*]+)\*$/s, 'Do']]

/** What Auto makes of a line, and the label it shows ("Do + Say"). */
export function read(line: string): Reading {
  const text = line.trim()
  if (text.startsWith('>')) return { mode: 'Narrate', text: text.replace(/^>+\s*/, ''), detected: 'Narrate' }
  for (const [re, mode] of WHOLE) {
    const m = re.exec(text)
    if (m) return { mode, text: mode === 'Do' ? text : m[1].trim(), detected: mode }
  }
  const acts = /\*[^*]+\*/.test(text)
  const said = text.replace(/\*[^*]+\*/g, '').trim()
  return { mode: acts ? 'Do' : 'Say', text, detected: acts && said ? 'Do + Say' : acts ? 'Do' : text ? 'Say' : '' }
}

/** A mode picked from the menu, for this line only. */
export function force(line: string, mode: Mode): Reading {
  if (mode === 'Auto') return read(line)
  const text = line.trim().replace(/^>+\s*/, '').replace(/^\((.+)\)$/s, '$1').replace(/^_(.+)_$/s, '$1')
  return { mode, text: mode === 'Do' && !/^\*[\s\S]*\*$/.test(text) ? `*${text}*` : text, detected: mode }
}
