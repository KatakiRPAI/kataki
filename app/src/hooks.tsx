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
 *  slow early response can never overwrite a later one. */
export function useLoad<T>(load: () => Promise<T>, deps: unknown[]): [T | undefined, () => void, string] {
  const [data, setData] = useState<T>()
  const [error, setError] = useState('')
  const seq = useRef(0)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const reload = useCallback(() => {
    const mine = ++seq.current
    load().then(
      (d) => {
        if (mine !== seq.current) return
        setData(d)
        setError('')
      },
      (e: Error) => mine === seq.current && setError(e.message),
    )
  }, deps)
  useEffect(reload, [reload])
  return [data, reload, error]
}

/** Run an action, surfacing its error instead of losing it. */
export function useAction(): [(fn: () => Promise<unknown>) => Promise<void>, string, boolean] {
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
  return [run, error, busy]
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
  const value = useMemo(
    () => ({ items: items ?? [], byId: new Map((items ?? []).map((i) => [i.id, i])), loaded: !!items, reload, error }),
    [items, reload, error],
  )
  return <LibraryContext.Provider value={value}>{children}</LibraryContext.Provider>
}

export const useLibrary = () => useContext(LibraryContext)

/** Dive into a scene: App plays the clouds parting, then goes to `to`. */
export const dive = (to: string) => dispatchEvent(new CustomEvent('ka-dive', { detail: to }))

/** Props that make a link dive instead of jumping (it still has a real href). */
export const diveLink = (to: string) => ({
  href: href(to),
  onClick: (e: { preventDefault: () => void }) => {
    e.preventDefault()
    dive(to)
  },
})
