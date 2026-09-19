import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react'

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
