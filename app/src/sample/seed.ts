// The sample world that ships with Kataki (README › The sample world): Liv and Cas to play as;
// Mike, Theo, Nico, Jae and Dani (a draft); Halcyon Coffee, Corvel Palace, the flat on Ardenne;
// the book Close to the Crown and its plots. Written into an empty library on first run.
import { api, upload, type Book, type Item } from '../api'
import cas from '../ds/art/cas.png'
import palace from '../ds/art/corvel-palace.png'
import ardenne from '../ds/art/flat-on-ardenne.png'
import halcyon from '../ds/art/halcyon-coffee.png'
import jae from '../ds/art/jae.png'
import liv from '../ds/art/liv.png'
import mike from '../ds/art/mike.png'
import nico from '../ds/art/nico.png'
import theo from '../ds/art/theo.png'
import world from './characters.json'
import books from './books-and-stories.json'
import places from './places.json'
import plots from './plots.json'

const ART: Record<string, string> = { liv, cas, mike, theo, nico, jae, 'halcyon-coffee': halcyon, 'corvel-palace': palace, 'flat-on-ardenne': ardenne }
// from how the boards speak of them ("Make him forget", "Mike has his doubts"); the rest stay "they"
const PRONOUNS: Record<string, 'she' | 'he' | 'they'> = { liv: 'she', mike: 'he', theo: 'he', jae: 'he' }

type Person = { id: string; name: string; face_focus?: string; tagline?: string; about?: string; tags?: string[]; also_known_as?: string[]; secret?: string; example_dialogue?: string[]; opening_line?: string; default?: boolean }

const picture = async (id: string) => (ART[id] ? (await upload(await (await fetch(ART[id])).blob())).name : undefined)

/** Seed the library; returns the default persona's id. Does nothing to a library that has anything in it. */
let running: Promise<number | undefined> | null = null // one seeding at a time, however often it is asked for
export function seedSampleWorld(): Promise<number | undefined> {
  return (running ??= seed().finally(() => { running = null }))
}
async function seed(): Promise<number | undefined> {
  const [items, stories] = await Promise.all([api<Item[]>('/library'), api<unknown[]>('/stories')])
  if (items.length || stories.length) return undefined
  const bookIds = new Map<string, number>()
  for (const b of (books as { id: string | null; name: string }[]).filter((x): x is { id: string; name: string } => !!x.id)) bookIds.set(b.id, (await api<Book>('/books', 'POST', { title: b.name })).id)
  const placeIds = new Map<string, number>()
  for (const p of places as { id: string; name: string; description: string; book?: string; times_of_day?: string[] }[]) {
    const made = await api<Item>('/library', 'POST', {
      kind: 'place', name: p.name, description: p.description,
      data: { image: await picture(p.id), time: p.times_of_day?.includes('dusk') ? 'dusk' : p.times_of_day?.[0], links: { book: p.book ? bookIds.get(p.book) : undefined } },
    })
    placeIds.set(p.id, made.id)
  }
  const person = async (c: Person, persona: boolean) => {
    const lines = c.example_dialogue ?? []
    return api<Item>('/library', 'POST', {
      kind: 'character', name: c.name.split(' ')[0], description: c.about ?? '', private: c.secret ?? '', tags: (c.tags ?? []).slice(0, 3),
      data: {
        persona: persona || undefined, source: 'shipped', tagline: c.tagline, pronouns: PRONOUNS[c.id] ?? 'they', aliases: [c.name, ...(c.also_known_as ?? [])],
        first_message: c.opening_line, lines, example_dialogue: lines.map((l) => `${c.name.split(' ')[0]}: ${l}`).join('\n'),
        portrait: await picture(c.id), focus: c.face_focus,
        places: (places as { id: string; known_by?: string[] }[]).filter((p) => p.known_by?.includes(c.id)).map((p) => placeIds.get(p.id)),
      },
    })
  }
  let first: number | undefined
  for (const p of world.personas as Person[]) { const made = await person(p, true); if (p.default) first = made.id }
  for (const c of world.characters as Person[]) await person(c, false)
  for (const p of plots as { name: string; premise: string; opening_narration: string; book?: string }[]) {
    await api('/library', 'POST', { kind: 'scenario', name: p.name, description: p.premise, data: { first_message: p.opening_narration, links: { book: p.book ? bookIds.get(p.book) : undefined } } })
  }
  if (first) await api('/settings', 'PUT', { persona: first })
  return first
}
