// A character as the handoff's DATA.md reads it, over the engine's library item.
// Field map: tagline → data.tagline, about → description, greeting → data.first_message,
// sample lines → data.lines (and data.example_dialogue for the engine), secret → private.
import type { Item, StorySummary } from './api'
import { utc } from './hooks'

export const isCharacter = (i: Item) => i.kind === 'character' && !i.data.persona
export const isPersona = (i: Item) => i.kind === 'character' && !!i.data.persona
/** No secret yet: a draft, which can still play (DATA.md › Character). */
export const isDraft = (i: Item) => !i.private.trim()
export const tagline = (i: Item) => i.data.tagline ?? i.description.split(/(?<=[.!?])\s/)[0] ?? ''

export function storiesWith(i: Item, stories: StorySummary[] | undefined) {
  return (stories ?? []).filter((s) => s.cast.some((c) => c.lib_item_id === i.id)).sort((a, b) => utc(b.last_at) - utc(a.last_at))
}

/** An `{he}/{him}/{his}` pick for ICU selects. */
export const pronoun = (i: Item | undefined) => i?.data.pronouns ?? 'they'

export type Group = { id: number; name: string; members: number[]; place: number | null }
