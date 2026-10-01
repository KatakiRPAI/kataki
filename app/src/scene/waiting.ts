// Lines sent while a reply is still being written wait here, in the window only (the engine has
// no queue: it takes one turn at a time). They go out in order when the turn frees up.
import type { Mode } from './modes.ts'

export type Waiting = { id: number; text: string; mode: Mode }

let n = 0
export const add = (q: Waiting[], text: string, mode: Mode): Waiting[] => [...q, { id: ++n, text, mode }]
export const drop = (q: Waiting[], id: number) => q.filter((w) => w.id !== id)
/** New words or a new way to read them; a line edited down to nothing is taken out. */
export const change = (q: Waiting[], id: number, to: Partial<Pick<Waiting, 'text' | 'mode'>>) =>
  to.text !== undefined && !to.text.trim() ? drop(q, id) : q.map((w) => (w.id === id ? { ...w, ...to, text: (to.text ?? w.text).trim() } : w))
/** One place earlier. */
export const sooner = (q: Waiting[], id: number) => {
  const i = q.findIndex((w) => w.id === id)
  return i < 1 ? q : [...q.slice(0, i - 1), q[i], q[i - 1], ...q.slice(i + 1)]
}
