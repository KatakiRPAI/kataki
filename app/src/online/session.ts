// Kataki online: the gateway in front of the engine holds the account
// (docs/specs/2026-10-02-kataki-online.md §5). The desktop and a self-hosted Kataki have no
// gateway, and nothing here changes them. Auth routes are called with fetch: no new dependency.

export type Me = { id: string; name: string; email: string; username?: string | null; twoFactorEnabled?: boolean | null; deleteAt?: string | null }
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
/** Refused because the sign-in is more than ten minutes old: signing in again clears it. */
export const stale = (x: unknown): boolean => (x as AuthError | null)?.code === 'SESSION_NOT_FRESH'

/** One of Better Auth's routes (a POST, or a GET with `body` left as "get"). Resolves to its
 *  JSON, or throws its `{code, message}`. */
export async function auth<T = unknown>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`/api/auth${path}`, body === 'get' ? undefined : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body ?? {}) })
  const got = await r.json().catch(() => null)
  if (!r.ok) throw (got ?? { message: `HTTP ${r.status}` }) as AuthError
  return got as T
}

// Passkeys use what the browser has built in (WebAuthn's JSON helpers); a browser without them
// is simply not offered passkeys.
type Json = Record<string, unknown>
const helpers = () => window.PublicKeyCredential as unknown as { parseCreationOptionsFromJSON?: (o: Json) => CredentialCreationOptions['publicKey']; parseRequestOptionsFromJSON?: (o: Json) => CredentialRequestOptions['publicKey'] } | undefined
export const passkeysWork = (): boolean => !!helpers()?.parseCreationOptionsFromJSON && !!helpers()?.parseRequestOptionsFromJSON
const asJson = (made: Credential | null): Json => { if (!made) throw new Error('cancelled'); return (made as unknown as { toJSON: () => Json }).toJSON() }

/** Add a passkey on this device to the signed-in account. */
export async function addPasskey(name: string): Promise<void> {
  const options = await auth<Json>(`/passkey/generate-register-options?name=${encodeURIComponent(name)}`, 'get')
  const made = await navigator.credentials.create({ publicKey: helpers()!.parseCreationOptionsFromJSON!(options) })
  await auth('/passkey/verify-registration', { response: asJson(made), name })
}

/** Sign in with a passkey on this device. */
export async function passkeySignIn(): Promise<void> {
  const options = await auth<Json>('/passkey/generate-authenticate-options', 'get')
  // the device must check it is you (the gateway refuses a sign-in where it did not)
  const made = await navigator.credentials.get({ publicKey: helpers()!.parseRequestOptionsFromJSON!({ ...options, userVerification: 'required' }) })
  await auth('/passkey/verify-authentication', { response: asJson(made) })
}

export async function signOut(): Promise<void> {
  await auth('/sign-out').catch(() => {})
  location.reload()
}
