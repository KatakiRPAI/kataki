// Kataki online: the gateway in front of the engine holds the account
// (docs/specs/2026-10-02-kataki-online.md §5). The desktop and a self-hosted Kataki have no
// gateway, and nothing here changes them. Auth routes are called with fetch: no new dependency.

export type Me = { id: string; name: string; email: string; twoFactorEnabled?: boolean | null; deleteAt?: string | null }
export type Session = 'none' | 'signed-out' | Me // none: there is no gateway here

let me: Me | undefined
let here = '' // this browser's session, to mark it in the list of places signed in
export const thisSession = (): string => here
/** Who is signed in, once `session()` has said (undefined on the desktop and self-hosted). */
export const account = (): Me | undefined => me

/** Ask the gateway once, at start. Anything but its JSON answer means there is no gateway. */
export async function session(): Promise<Session> {
  if (window.kataki) return 'none'
  try {
    const r = await fetch('/api/auth/get-session')
    if (!r.ok || !r.headers.get('content-type')?.includes('json')) return 'none'
    const got = (await r.json()) as { user?: Me; session?: { token: string } } | null
    here = got?.session?.token ?? ''
    return got?.user ? (me = got.user) : 'signed-out'
  } catch {
    return 'none'
  }
}

export type AuthError = { code?: string; message?: string }

/** One of Better Auth's routes (a POST, or a GET with `body` left as "get"). Resolves to its
 *  JSON, or throws its `{code, message}`. */
export async function auth<T = unknown>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`/api/auth${path}`, body === 'get' ? undefined : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body ?? {}) })
  const got = await r.json().catch(() => null)
  if (!r.ok) throw (got ?? { message: `HTTP ${r.status}` }) as AuthError
  return got as T
}

export async function signOut(): Promise<void> {
  await auth('/sign-out').catch(() => {})
  location.reload()
}
