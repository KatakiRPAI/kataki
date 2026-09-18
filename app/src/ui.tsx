import { useCallback, useEffect, useState, type ReactNode } from 'react'

/** Load data, with a reload function and the last error. */
export function useLoad<T>(load: () => Promise<T>, deps: unknown[]): [T | undefined, () => void, string] {
  const [data, setData] = useState<T>()
  const [error, setError] = useState('')
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const reload = useCallback(() => {
    load().then(
      (d) => {
        setData(d)
        setError('')
      },
      (e: Error) => setError(e.message),
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

export function ErrorLine({ error }: { error: string }) {
  return error ? <p className="error" role="alert">{error}</p> : null
}

/** Story text: paragraphs, *actions* and **emphasis**. Rendered as elements, never as HTML. */
export function Prose({ text }: { text: string }) {
  return (
    <>
      {text.split(/\n{2,}/).map((para, i) => (
        <p key={i}>
          {para.split(/(\*\*[^*]+\*\*|\*[^*\n]+\*)/).map((part, j): ReactNode => {
            if (part.startsWith('**') && part.endsWith('**') && part.length > 4) return <strong key={j}>{part.slice(2, -2)}</strong>
            if (part.startsWith('*') && part.endsWith('*') && part.length > 2) return <em key={j}>{part.slice(1, -1)}</em>
            return part
          })}
        </p>
      ))}
    </>
  )
}
