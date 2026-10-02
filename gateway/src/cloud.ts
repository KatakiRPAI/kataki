// Cloud save for the desktop app (docs/specs/2026-10-02-kataki-online.md §8).
//
// A computer is linked to an account once: the desktop shows a code, the person approves it
// while signed in on the website, and the desktop is handed a token that opens these routes and
// nothing else. A snapshot is the whole library as the desktop's own `.kataki` file. The newest
// KEPT are kept; an upload that is not built on the newest one is refused unless it says to
// replace it, so one computer never silently overwrites what another sent.
//
// ponytail: snapshots are files on the gateway's own disk (KATAKI_CLOUD_DIR). Object storage
// (the deploy slice) swaps `put`/`get`/`drop` for a bucket; nothing else here changes.
import { createHash, randomBytes, randomInt } from 'node:crypto'
import { createReadStream, createWriteStream, mkdirSync, rmSync, statSync } from 'node:fs'
import type { IncomingMessage, ServerResponse } from 'node:http'
import { join } from 'node:path'
import { pipeline } from 'node:stream/promises'
import type { Pool } from 'pg'
import { USER } from './sign.ts'

export const KEPT = 5
export type CloudConfig = { pool: Pool; origin: string; dir: string; maxBytes: number }
export type Snapshot = { revision: number; bytes: number; holds: Record<string, number>; device: string; at: string }

const sealed = (secret: string) => createHash('sha256').update(secret).digest('hex')
const LETTERS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789' // no 0/O, 1/I/L: a code is read off one screen and typed on another
const code = () => Array.from({ length: 8 }, () => LETTERS[randomInt(LETTERS.length)]).join('')
const cleanName = (name: unknown) => (typeof name === 'string' ? name.replace(/[^\p{L}\p{N} ._()-]/gu, '').trim().slice(0, 60) : '') || 'A computer'
const file = (c: CloudConfig, user: string, revision: number) => join(c.dir, user, `${revision}.kataki`)

// --- linking a computer ----------------------------------------------------------------------

/** The desktop asks to be linked. It keeps `secret`; the person is shown `code`. Ten minutes. */
export async function startLink(c: CloudConfig, name: unknown): Promise<{ code: string; secret: string; url: string; expiresIn: number }> {
  await c.pool.query('DELETE FROM device_link WHERE expires_at < now()')
  const made = { code: code(), secret: randomBytes(32).toString('hex') }
  await c.pool.query("INSERT INTO device_link(code, secret_hash, name, expires_at) VALUES($1, $2, $3, now() + interval '10 minutes')", [made.code, sealed(made.secret), cleanName(name)])
  return { ...made, url: `${c.origin}/app/?link=${made.code}`, expiresIn: 600 }
}

/** The computer a code belongs to, for the signed-in person to recognise before approving. */
export async function linkName(c: CloudConfig, linkCode: string): Promise<string | null> {
  const { rows } = await c.pool.query('SELECT name FROM device_link WHERE code = $1 AND expires_at > now() AND user_id IS NULL', [linkCode.toUpperCase()])
  return rows[0]?.name ?? null
}

/** The signed-in person says yes to a code. False: no such code waiting. */
export async function approveLink(c: CloudConfig, user: string, linkCode: string): Promise<boolean> {
  const r = await c.pool.query('UPDATE device_link SET user_id = $1 WHERE code = $2 AND expires_at > now() AND user_id IS NULL', [user, linkCode.toUpperCase()])
  return r.rowCount === 1
}

/** The desktop asks whether it was approved. Its token is handed over once, and the link is gone. */
export async function pollLink(c: CloudConfig, secret: unknown): Promise<'gone' | 'waiting' | { token: string; device: string }> {
  if (typeof secret !== 'string') return 'gone'
  const { rows } = await c.pool.query('SELECT code, user_id, name, expires_at > now() AS live FROM device_link WHERE secret_hash = $1', [sealed(secret)])
  const link = rows[0]
  if (!link?.live) return 'gone'
  if (!link.user_id) return 'waiting'
  const token = `kd_${randomBytes(32).toString('hex')}`
  const id = randomBytes(8).toString('hex')
  await c.pool.query('INSERT INTO device(id, user_id, token_hash, name) VALUES($1, $2, $3, $4)', [id, link.user_id, sealed(token), link.name])
  await c.pool.query('DELETE FROM device_link WHERE code = $1', [link.code])
  return { token, device: id }
}

export const devices = async (c: CloudConfig, user: string) =>
  (await c.pool.query('SELECT id, name, created_at AS "createdAt", last_used_at AS "lastUsedAt" FROM device WHERE user_id = $1 ORDER BY created_at', [user])).rows

export async function unlink(c: CloudConfig, user: string, id: string): Promise<boolean> {
  return (await c.pool.query('DELETE FROM device WHERE user_id = $1 AND id = $2', [user, id])).rowCount === 1
}

/** Whose computer is asking, from its token. */
export async function deviceOf(c: CloudConfig, req: IncomingMessage): Promise<{ id: string; user: string; name: string } | null> {
  const said = /^Bearer (kd_[0-9a-f]{64})$/.exec(req.headers.authorization ?? '')?.[1]
  if (!said) return null
  const { rows } = await c.pool.query('UPDATE device SET last_used_at = now() WHERE token_hash = $1 RETURNING id, user_id, name', [sealed(said)])
  return rows[0] && USER.test(rows[0].user_id) ? { id: rows[0].id, user: rows[0].user_id, name: rows[0].name } : null
}

// --- snapshots -------------------------------------------------------------------------------

export async function newest(c: CloudConfig, user: string): Promise<Snapshot | null> {
  const { rows } = await c.pool.query('SELECT revision, bytes, holds, device, at FROM snapshot WHERE user_id = $1 ORDER BY revision DESC LIMIT 1', [user])
  return rows[0] ? { ...rows[0], bytes: Number(rows[0].bytes), at: new Date(rows[0].at).toISOString() } : null
}

const counts = (said: unknown): Record<string, number> => {
  const out: Record<string, number> = {}
  if (said && typeof said === 'object') for (const [k, v] of Object.entries(said).slice(0, 12)) if (/^[a-z]{1,20}$/.test(k) && Number.isInteger(v) && (v as number) >= 0) out[k] = v as number
  return out
}

/** Take an upload. 409 with what is there when it was not built on the newest snapshot (and
 *  did not say to replace it); 413 past the size limit. */
export async function upload(c: CloudConfig, who: { user: string; name: string }, req: IncomingMessage, base: number, force: boolean, holds: unknown): Promise<{ status: 200 | 409 | 413; snapshot: Snapshot | null }> {
  const have = await newest(c, who.user)
  if (!force && (have?.revision ?? 0) !== base) return { status: 409, snapshot: have }
  const revision = (have?.revision ?? 0) + 1
  const target = file(c, who.user, revision)
  mkdirSync(join(c.dir, who.user), { recursive: true })
  let bytes = 0
  try {
    await pipeline(req, async function* (source) {
      for await (const chunk of source) {
        bytes += chunk.length
        if (bytes > c.maxBytes) throw new Error('too big')
        yield chunk
      }
    }, createWriteStream(target))
  } catch (e) {
    rmSync(target, { force: true })
    if (bytes > c.maxBytes) return { status: 413, snapshot: have }
    throw e
  }
  if (!bytes) { rmSync(target, { force: true }); throw new Error('an empty upload') }
  await c.pool.query('INSERT INTO snapshot(user_id, revision, bytes, holds, device) VALUES($1, $2, $3, $4, $5)', [who.user, revision, bytes, JSON.stringify(counts(holds)), who.name])
  // only the newest few are kept
  const old = await c.pool.query('DELETE FROM snapshot WHERE user_id = $1 AND revision <= $2 RETURNING revision', [who.user, revision - KEPT])
  for (const { revision: gone } of old.rows) rmSync(file(c, who.user, gone), { force: true })
  return { status: 200, snapshot: await newest(c, who.user) }
}

/** Send the newest snapshot. False: there is none. */
export async function download(c: CloudConfig, user: string, res: ServerResponse): Promise<boolean> {
  const have = await newest(c, user)
  if (!have) return false
  const from = file(c, user, have.revision)
  res.writeHead(200, { 'content-type': 'application/zip', 'content-length': statSync(from).size, 'x-kataki-revision': String(have.revision), 'cache-control': 'no-store' })
  await pipeline(createReadStream(from), res)
  return true
}

/** An account that is deleted takes its computers and snapshots with it. */
export async function forgetCloud(c: CloudConfig, user: string): Promise<void> {
  if (!USER.test(user)) return
  await c.pool.query('DELETE FROM snapshot WHERE user_id = $1', [user])
  await c.pool.query('DELETE FROM device WHERE user_id = $1', [user])
  await c.pool.query('DELETE FROM device_link WHERE user_id = $1', [user])
  rmSync(join(c.dir, user), { recursive: true, force: true })
}
