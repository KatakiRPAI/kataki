// Every shortcut, its default and where it works (KEYBOARD.md). Labels are strings sc.{id}. Overrides live in the `shortcuts`
// setting as { actionId: "Ctrl+Shift+R" }; an empty string means "Not set".
import { pref } from './prefs'

export type Where = 'anywhere' | 'story'
export const SHORTCUTS: [id: string, keys: string, where: Where][] = [
  ['search', 'Ctrl+K', 'anywhere'], ['newStory', 'Ctrl+N', 'anywhere'],
  ['newCharacter', 'Ctrl+Shift+N', 'anywhere'], ['persona', 'Ctrl+P', 'anywhere'],
  ['settings', 'Ctrl+,', 'anywhere'], ['focusSearch', '/', 'anywhere'],
  ['feedback', 'Ctrl+Shift+F', 'anywhere'], ['goHome', 'G H', 'anywhere'],
  ['goStories', 'G S', 'anywhere'], ['goCharacters', 'G C', 'anywhere'],
  ['goWorld', 'G W', 'anywhere'], ['goYou', 'G Y', 'anywhere'],
  ['sendPass', 'Ctrl+Enter', 'story'], ['regenerate', 'Ctrl+R', 'story'],
  ['continue', 'Ctrl+J', 'story'], ['backstage', 'Ctrl+B', 'story'],
  ['find', 'Ctrl+F', 'story'], ['mute', 'Ctrl+M', 'story'],
  ['widgets', 'Ctrl+E', 'story'], ['reading', 'Ctrl+Shift+R', 'story'],
]
const RESERVED = new Set(['Alt+F4', 'Ctrl+Alt+Delete', 'Alt+Tab', 'F11', 'Ctrl+=', 'Ctrl+-', 'Ctrl+0', 'Ctrl+C', 'Ctrl+V', 'Ctrl+X', 'Ctrl+A', 'Ctrl+Z', 'Escape', 'Enter', 'Tab'])

export const keysOf = (id: string): string => {
  const own = pref<Record<string, string>>('shortcuts', {})[id]
  return own ?? SHORTCUTS.find((s) => s[0] === id)?.[1] ?? ''
}
/** "Ctrl+Shift+R" → ["Ctrl", "Shift", "R"]; a sequence "G H" → ["G", "then", "H"]. */
export const parts = (keys: string) => (keys.includes(' ') ? keys.split(' ').flatMap((k, i) => (i ? ['then', k] : [k])) : keys ? keys.split('+') : [])

/** The combination a key press makes, or null for a modifier alone. */
export function combo(e: KeyboardEvent): string | null {
  if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) return null
  const key = e.key.length === 1 ? e.key.toUpperCase() : e.key
  return [e.ctrlKey || e.metaKey ? 'Ctrl' : '', e.altKey ? 'Alt' : '', e.shiftKey && key.length > 1 || e.shiftKey && /[A-Z]/.test(key) ? 'Shift' : '', key].filter(Boolean).join('+')
}
export const reserved = (keys: string) => RESERVED.has(keys) || keys.startsWith('Meta+')
export const holder = (keys: string, except: string) => SHORTCUTS.find(([id]) => id !== except && keysOf(id) === keys)

/** Does this key press trigger the action? (Sequences are matched by the page, not here.) */
export const is = (e: KeyboardEvent, id: string) => { const k = keysOf(id); return !!k && !k.includes(' ') && combo(e) === k }
