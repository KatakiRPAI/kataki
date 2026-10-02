// Leaving, and taking your data with you (docs/specs/2026-10-02-kataki-online.md G5).
//
// An account that asks to be deleted is signed out everywhere at once and removed GRACE_DAYS
// later; signing in before then and saying "keep it" undoes it. When the day comes the engine
// forgets the library first (it refuses while usage is unbilled), then the account goes. The
// ledger's rows stay: they are payment records, and hold only an id that no longer names anyone.
import { request } from 'node:http'
import type { Pool } from 'pg'
import type { Auth, Send } from './auth.ts'
import { balance } from './ledger.ts'
import { signed } from './sign.ts'

export const GRACE_DAYS = 14
export const FORGET = '/_gateway/forget' // the engine's route for this; never proxied for a browser

export type AccountConfig = { auth: Auth; pool: Pool; origin: string; engine: string; secret: string; send: Send }
type Who = { id: string; name: string; email: string }

const day = (d: Date) => d.toISOString().slice(0, 10)

/** Set the account to be deleted, and sign it out everywhere. Returns the day it goes. */
export async function askToDelete(c: AccountConfig, who: Who, now = new Date()): Promise<Date> {
  const at = new Date(now.getTime() + GRACE_DAYS * 86_400_000)
  await c.pool.query('UPDATE "user" SET "deleteAt" = $1 WHERE id = $2', [at, who.id])
  await (await c.auth.$context).internalAdapter.deleteUserSessions(who.id)
  void c.send(who.email, 'Your Kataki account is set to be deleted', `Your Kataki account, with its stories, characters and pictures, will be deleted on ${day(at)}.\n\nChanged your mind? Sign in at ${c.origin}/app/ before then and choose "Keep my account".\n\nIf you did not ask for this, sign in now, keep the account, and change your password.`)
  return at
}

export async function keep(c: AccountConfig, who: Who): Promise<void> {
  await c.pool.query('UPDATE "user" SET "deleteAt" = NULL WHERE id = $1', [who.id])
  void c.send(who.email, 'Your Kataki account is staying', 'Your Kataki account is no longer set to be deleted. Nothing was removed.')
}

/** Everything the gateway holds about an account, for the person it is about. The library has
 *  its own export (Settings › Data). */
export async function exportOf(c: AccountConfig, who: Who): Promise<object> {
  const rows = async (sql: string) => (await c.pool.query(sql, [who.id])).rows
  const [user] = await rows('SELECT id, name, email, "emailVerified", "createdAt", adult, "twoFactorEnabled", "deleteAt" FROM "user" WHERE id = $1')
  return {
    exported: new Date().toISOString(),
    account: user,
    signInMethods: await rows('SELECT "providerId", "createdAt" FROM account WHERE "userId" = $1 ORDER BY "createdAt"'),
    sessions: await rows('SELECT "createdAt", "expiresAt", "ipAddress", "userAgent" FROM session WHERE "userId" = $1 ORDER BY "createdAt"'),
    balanceMicroDollars: Number(await balance(c.pool, who.id)),
    credit: await rows('SELECT micros, reason, at FROM credit WHERE user_id = $1 ORDER BY id'),
    usage: await rows('SELECT usage_id, micros, role, model, prompt_tokens, cached_tokens, completion_tokens, estimated, used_at FROM usage WHERE user_id = $1 ORDER BY used_at'),
  }
}

/** Ask the engine to delete this user's library. Its status: 200 gone, 409 not yet. */
function forget(c: AccountConfig, user: string): Promise<number> {
  const engine = new URL(c.engine)
  return new Promise((done, failed) => {
    const up = request({ host: engine.hostname, port: engine.port, path: FORGET, method: 'POST', headers: signed(c.secret, user, 'stable', 'POST', FORGET) }, (r) => {
      r.resume()
      done(r.statusCode ?? 502)
    })
    up.on('error', failed)
    up.end()
  })
}

/** Remove every account whose day has come. Returns how many went; one that could not go yet
 *  (the engine is down, or still has usage to bill) waits for the next sweep. */
export async function sweep(c: AccountConfig, now = new Date()): Promise<number> {
  const due = (await c.pool.query('SELECT id FROM "user" WHERE "deleteAt" <= $1', [now])).rows as { id: string }[]
  const { internalAdapter } = await c.auth.$context
  let gone = 0
  for (const { id } of due) {
    try {
      if ((await forget(c, id)) !== 200) continue
      await internalAdapter.deleteUserSessions(id)
      await internalAdapter.deleteAccounts(id)
      await internalAdapter.deleteUser(id)
      gone++
    } catch (e) {
      console.error('gateway: could not delete an account yet:', e instanceof Error ? e.message : e)
    }
  }
  return gone
}
