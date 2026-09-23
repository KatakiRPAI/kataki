export type Mode = 'auto' | 'say' | 'do' | 'whisper' | 'think' | 'narrate'
export type Reading = { mode: Exclude<Mode, 'auto'>; text: string; to?: number; label: string }

/** What Auto makes of a line from how it is written: `>> …` narrates, `(…)` is a thought no one
 *  hears, `@Mira …` whispers to someone here, `*…*` is an action ("Do + Say" with speech beside
 *  it), anything else is said. The markers that only choose the mode come off the text. */
export function readLine(line: string, people: { id: number; name: string }[]): Reading {
  const t = line.trim()
  if (t.startsWith('>>')) return { mode: 'narrate', text: t.slice(2).trim(), label: 'Narrate' }
  if (/^\([\s\S]*\)$/.test(t)) return { mode: 'think', text: t.slice(1, -1).trim(), label: 'Think' }
  if (t.startsWith('@')) {
    // longest name first, so "@Master Oren" is not read as someone called "Master"
    const who = [...people]
      .sort((a, b) => b.name.length - a.name.length)
      .find((p) => t.slice(1, p.name.length + 1).toLowerCase() === p.name.toLowerCase() && !/\w/.test(t[p.name.length + 1] ?? ''))
    if (who) return { mode: 'whisper', text: t.slice(who.name.length + 1).replace(/^[\s,:]+/, ''), to: who.id, label: `Whisper to ${who.name}` }
  }
  if (/\*[^*]+\*/.test(t)) return { mode: 'do', text: t, label: t.replace(/\*[^*]*\*/g, '').trim() ? 'Do + Say' : 'Do' }
  return { mode: 'say', text: t, label: 'Say' }
}
