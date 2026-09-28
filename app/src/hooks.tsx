import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from 'react'
import { api, mediaUrl, type Item } from './api'

/** A draft kept in this browser, so leaving and coming back finds it as it was. null: nothing
 *  kept. Storage can be missing (private mode); the draft then lasts only while you stay. */
export function useKept(key: string): [string | null, (v: string | null) => void] {
  const [value, setValue] = useState(() => {
    try {
      return localStorage.getItem(key)
    } catch {
      return null
    }
  })
  const set = (v: string | null) => {
    setValue(v)
    try {
      if (v === null) localStorage.removeItem(key)
      else localStorage.setItem(key, v)
    } catch {
      /* kept while you stay */
    }
  }
  return [value, set]
}

/** Load data, with a reload function and the last error. Only the newest load may land, so a
 *  slow early response can never overwrite a later one. Reloading is awaitable: an action that
 *  reads what it just wrote has to wait for the fresh data, not race the next click against it. */
export function useLoad<T>(load: () => Promise<T>, deps: unknown[]): [T | undefined, () => Promise<void>, string] {
  const [data, setData] = useState<T>()
  const [error, setError] = useState('')
  const seq = useRef(0)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const reload = useCallback(() => {
    const mine = ++seq.current
    return load().then(
      (d) => {
        if (mine !== seq.current) return
        setData(d)
        setError('')
      },
      (e: Error) => {
        if (mine === seq.current) setError(e.message)
      },
    )
  }, deps)
  useEffect(() => {
    reload()
  }, [reload])
  return [data, reload, error]
}

/** Run an action, surfacing its error instead of losing it. */
export function useAction(): [
  (fn: () => Promise<unknown>) => Promise<void>,
  string,
  boolean,
  () => void,
] {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const run = useCallback(async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError('')
    try {
      await fn()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }, [])
  // One screen runs several things, and what went wrong with one is not news about the next:
  // a screen that closes what failed says so by forgetting it.
  const forget = useCallback(() => setError(''), [])
  return [run, error, busy, forget]
}

/** Call `fn` every `ms` while enabled, skipping ticks while the window is hidden. */
export function usePoll(fn: () => void, ms: number, enabled = true) {
  const latest = useRef(fn)
  latest.current = fn
  useEffect(() => {
    if (!enabled) return
    const id = setInterval(() => document.hidden || latest.current(), ms)
    return () => clearInterval(id)
  }, [ms, enabled])
}

// ---- the library: every item, loaded once and reloaded after any edit ----

type Library = { items: Item[]; byId: Map<number, Item>; loaded: boolean; reload: () => void; error: string }

const LibraryContext = createContext<Library>({ items: [], byId: new Map(), loaded: false, reload: () => {}, error: '' })

export function LibraryProvider({ children }: { children: ReactNode }) {
  const [items, reload, error] = useLoad(() => api<Item[]>('/library'), [])
  useArrivals(reload)
  const value = useMemo(
    () => ({ items: items ?? [], byId: new Map((items ?? []).map((i) => [i.id, i])), loaded: !!items, reload, error }),
    [items, reload, error],
  )
  return <LibraryContext.Provider value={value}>{children}</LibraryContext.Provider>
}

export const useLibrary = () => useContext(LibraryContext)

/** Something came in from outside and made friends or stories this screen has not read. Whatever
 *  is mounted asks for its data again: a screen that does not remount would otherwise show a
 *  library from before the file arrived. */
export const arrived = () => dispatchEvent(new Event('ka-arrived'))

export function useArrivals(fn: () => void) {
  const latest = useRef(fn)
  latest.current = fn
  useEffect(() => {
    const on = () => latest.current()
    addEventListener('ka-arrived', on)
    return () => removeEventListener('ka-arrived', on)
  }, [])
}

// ---- real time: outside a story, times are yours ("Played 2 hours ago"), not the story's ----
/** A SQLite UTC timestamp ("YYYY-MM-DD HH:MM:SS") as epoch ms. */
export const utc = (at: string) => Date.parse(at.replace(' ', 'T') + 'Z')
// ---- story time: 12-hour in the chat and widgets, the 24-hour clock and the count on hover ----
/** "19:02" (or a whole clock label, "Day 1, 19:02") -> "7:02 pm". */
export function twelve(clock: string): string {
  const [h, m] = clock.slice(-5).split(':').map(Number)
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'am' : 'pm'}`
}
/** A story date as it reads mid-sentence: "six years after the storm"; a bare count stays "Day 3". */
export const inline = (date: string) => (/^(Day|Year) /.test(date) ? date : date[0].toLowerCase() + date.slice(1))
/** The hover on a story time: "19:02 · Day 1 · the evening of the storm". */
export const fullTime = (clock: string, date: string) =>
  [clock.slice(-5), clock.slice(0, -7), inline(date)].filter((part, i, all) => part && all.indexOf(part) === i).join(' · ')

/** How a person shows: the sample world's own art by name, else their uploaded portrait. */
const SAMPLE = new Set(['liv', 'mike', 'theo', 'jae', 'nico', 'cas', 'dani'])
export function face(item: Item | undefined, name = item?.name ?? ''): { who?: string; src?: string; name: string; focus?: string } {
  const src = item?.data.portrait ? mediaUrl(item.data.portrait) : undefined
  const who = name.toLowerCase().split(' ')[0]
  return { who: !src && SAMPLE.has(who) ? who : undefined, src, name, focus: item?.data.focus }
}
/** A place's picture: the sample world's by name, else its upload. */
const PLACES: Record<string, string> = { 'halcyon coffee': 'halcyon-coffee', 'corvel palace': 'corvel-palace', 'the flat on ardenne': 'flat-on-ardenne' }
export function scenery(item: Item | undefined): { place?: string; src?: string } {
  const src = item?.data.image ? mediaUrl(item.data.image) : undefined
  return { place: !src && item ? PLACES[item.name.toLowerCase()] : undefined, src }
}

/** True while the window is narrower than `px` (CSS px, after zoom). */
export function useNarrow(px: number): boolean {
  const q = `(max-width: ${px - 1}px)`
  return useSyncExternalStore((f) => { const m = matchMedia(q); m.addEventListener('change', f); return () => m.removeEventListener('change', f) }, () => matchMedia(q).matches)
}
