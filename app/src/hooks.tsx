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
import { api, type Item } from './api'

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

// ---- router: the hash is the route, e.g. #/friend/3/edit?step=2 ----

export type Route = { path: string; parts: string[]; query: URLSearchParams }

export function parse(hash: string): Route {
  const [path, query = ''] = hash.replace(/^#/, '').split('?')
  const clean = path || '/'
  return { path: clean, parts: clean.split('/').filter(Boolean), query: new URLSearchParams(query) }
}

export const href = (path: string) => '#' + path

export const go = (path: string) => {
  location.hash = path
}

const onHashChange = (cb: () => void) => {
  addEventListener('hashchange', cb)
  return () => removeEventListener('hashchange', cb)
}

export function useRoute(): Route {
  const hash = useSyncExternalStore(onHashChange, () => location.hash)
  return useMemo(() => parse(hash), [hash])
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

/** Dive into a scene: App plays the clouds parting, then goes to `to`. */
export const dive = (to: string) => dispatchEvent(new CustomEvent('ka-dive', { detail: to }))

/** Someone moving in or out of a scene: a story character who is away, a library friend, or
 *  someone here (to send away). */
export type Moving = { kind: 'away' | 'friend' | 'here'; id: number }

/** Where the Scene's cloud button floats back up to: the last Sky page shown. */
export const lastSky = { path: '/home' }

// ---- real time: outside a story, times are yours ("Played 2 hours ago"), not the story's ----
/** A SQLite UTC timestamp ("YYYY-MM-DD HH:MM:SS") as epoch ms. */
export const utc = (at: string) => Date.parse(at.replace(' ', 'T') + 'Z')
const RELATIVE = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [['year', 31_536_000], ['month', 2_592_000], ['week', 604_800], ['day', 86_400], ['hour', 3_600], ['minute', 60]]
/** "just now", "5 minutes ago", "yesterday", "last week". */
export function ago(at: string): string {
  const s = (Date.now() - utc(at)) / 1000
  const [unit, size] = UNITS.find(([, size]) => s >= size) ?? []
  return unit ? RELATIVE.format(-Math.floor(s / size!), unit) : 'just now'
}
/** The exact local time, for a hover: "Today, 7:12 pm" or "22 Sept 2026, 7:12 pm". */
export function exact(at: string): string {
  const d = new Date(utc(at))
  const time = d.toLocaleTimeString('en-GB', { hour: 'numeric', minute: '2-digit', hour12: true })
  return `${d.toDateString() === new Date().toDateString() ? 'Today' : d.toLocaleDateString('en-GB', { dateStyle: 'medium' })}, ${time}`
}

/** Leave a scene: the reverse of the dive, up to the last Sky page. */
export const rise = () => dispatchEvent(new CustomEvent('ka-rise', { detail: lastSky.path }))

/** Props that make a link dive instead of jumping (it still has a real href). */
export const diveLink = (to: string) => ({
  href: href(to),
  onClick: (e: { preventDefault: () => void }) => {
    e.preventDefault()
    dive(to)
  },
})

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
