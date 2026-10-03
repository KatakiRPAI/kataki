// The gateway's HTTP surface (docs/specs/2026-10-02-kataki-online.md §1):
//   /api/auth/*        Better Auth
//   /api/me            who is signed in, and their balance
//   /api/usage         what they spent lately, by day, and what they added
//   /allow, /usage     the engine asks (its bearer key)
//   /app/*             the web build
//   everything else    a signed request to the engine, for whoever the session says
import { timingSafeEqual } from 'node:crypto'
import { createReadStream, existsSync, statSync } from 'node:fs'
import { request, type IncomingMessage, type RequestListener, type ServerResponse } from 'node:http'
import { extname, join, normalize, sep } from 'node:path'
import { fromNodeHeaders, toNodeHandler } from 'better-auth/node'
import type { Pool } from 'pg'
import { askToDelete, exportOf, FORGET, keep, removeBackupEmail, setBackupEmail, verifyBackupEmail } from './account.ts'
import type { Auth, Send } from './auth.ts'
import { approveLink, deviceOf, devices, download, KEPT, LIMITS, linkName, newest, over, pollLink, startLink, unlink, upload, type CloudConfig } from './cloud.ts'
import { allow, balance, bill, grant, spending } from './ledger.ts'
import type { Prices } from './money.ts'
import { signed, USER } from './sign.ts'
import { AMOUNTS, cancel, checkoutOf, settle, startTopup, testCheckoutPage, type Payments, type TopupConfig } from './topup.ts'

export type GatewayConfig = {
  auth: Auth
  pool: Pool
  origin: string // the gateway's own origin: what a request that changes something must come from
  engine: string // http://127.0.0.1:8788, `kataki serve --hosted`
  secret: string // KATAKI_GATEWAY_SECRET: signs requests to the engine
  key: string // KATAKI_GATEWAY_KEY: what the engine shows on /allow and /usage
  prices: Prices
  web?: string // the web build's folder (app/dist-web)
  starter?: bigint // micro-dollars given once to a new account
  social?: string[] // the services an account can sign in with (auth.ts › Social)
  send: Send // mail (auth.ts)
  payments?: Payments // how credit is bought (topup.ts); absent: it cannot be, yet
  cloud?: { dir: string; maxBytes: number; limits?: CloudConfig['limits'] } // where snapshots from the desktop are kept (cloud.ts); absent: no cloud save
}

const TYPES: Record<string, string> = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2', '.ico': 'image/x-icon', '.map': 'application/json',
}
// never passed on to the engine: who you are is ours to say, and the session is ours to keep
const DROPPED = /^(cookie|authorization|host|connection|keep-alive|transfer-encoding|upgrade|proxy-.*|te|trailer|x-kataki-.*)$/

function json(res: ServerResponse, status: number, body: unknown): void {
  res.writeHead(status, { 'content-type': 'application/json', 'cache-control': 'no-store' }).end(JSON.stringify(body))
}

async function body(req: IncomingMessage, max = 65_536): Promise<unknown> {
  let text = ''
  for await (const chunk of req) {
    text += chunk
    if (text.length > max) throw new Error('too big')
  }
  return JSON.parse(text)
}

export function createGateway(c: GatewayConfig): RequestListener {
  const authHandler = toNodeHandler(c.auth)
  const granted = new Set<string>() // accounts whose starting credit was looked at by this process
  const engine = new URL(c.engine)
  const cloud: CloudConfig | null = c.cloud ? { pool: c.pool, origin: c.origin, ...c.cloud } : null
  const paying: TopupConfig | null = c.payments ? { pool: c.pool, origin: c.origin, payments: c.payments } : null

  const fromEngine = (req: IncomingMessage): boolean => {
    const said = Buffer.from(req.headers.authorization ?? '')
    const want = Buffer.from(`Bearer ${c.key}`)
    return said.length === want.length && timingSafeEqual(said, want)
  }

  function serve(res: ServerResponse, path: string): void {
    const root = normalize(c.web!)
    let file = normalize(join(root, decodeURIComponent(path.slice('/app/'.length))))
    if (file !== root && !file.startsWith(root + sep)) return json(res, 404, { detail: 'not found' })
    // the app routes in the browser: a path that is no file is the app itself
    if (!existsSync(file) || !statSync(file).isFile()) file = join(root, 'index.html')
    const hashed = /[-.][0-9a-zA-Z_-]{8,}\.\w+$/.test(file) // Vite's content-hashed assets never change
    res.writeHead(200, { 'content-type': TYPES[extname(file)] ?? 'application/octet-stream', 'cache-control': hashed ? 'public, max-age=31536000, immutable' : 'no-cache' })
    createReadStream(file).pipe(res)
  }

  function proxy(req: IncomingMessage, res: ServerResponse, user: string): void {
    const headers: Record<string, string | string[]> = {}
    for (const [k, v] of Object.entries(req.headers)) if (v !== undefined && !DROPPED.test(k)) headers[k] = v
    // ponytail: every account is on the stable channel; a `channel` on the account when beta accounts exist
    Object.assign(headers, signed(c.secret, user, 'stable', req.method!, req.url!))
    const up = request({ host: engine.hostname, port: engine.port, path: req.url, method: req.method, headers }, (r) => {
      res.writeHead(r.statusCode ?? 502, r.headers)
      r.pipe(res) // unbuffered: a reply streams as the engine writes it
    })
    up.on('error', () => { if (!res.headersSent) json(res, 502, { detail: 'Kataki is not answering.', code: 'ENGINE_DOWN' }); else res.end() })
    res.on('close', () => up.destroy()) // Stop, or a closed tab, ends the engine's work on it too
    req.pipe(up)
  }

  return async (req, res) => {
    try {
      const url = new URL(req.url ?? '/', c.origin)
      const path = url.pathname
      if (path.startsWith('/api/auth/')) return void (await authHandler(req, res))
      if (path === '/allow' || path === '/usage') {
        if (!fromEngine(req)) return json(res, 401, { detail: 'not the engine' })
        if (path === '/allow' && req.method === 'GET') return json(res, 200, { ok: await allow(c.pool, url.searchParams.get('user') ?? '', Number(url.searchParams.get('estimate'))) })
        if (path === '/usage' && req.method === 'POST') {
          let row: unknown
          try { row = await body(req) } catch { return json(res, 400, { detail: 'not a usage row' }) }
          const status = row && typeof row === 'object' ? await bill(c.pool, c.prices, row as Record<string, unknown>) : 422
          return json(res, status, { ok: status === 200 })
        }
        return json(res, 405, { detail: 'method not allowed' })
      }
      if (path === '/') return void res.writeHead(302, { location: '/app/' }).end()
      // what the sign-in screen may offer; nothing secret
      if (path === '/api/providers') return json(res, 200, { social: c.social ?? [], payments: paying ? { amounts: AMOUNTS, test: paying.payments.processor === 'test' } : null })
      // the test processor's own pages (KATAKI_PAYMENTS=test): stand-ins for a real hosted checkout
      const testing = paying?.payments.processor === 'test' && /^\/test-checkout\/([0-9a-f]{24})(\/pay|\/cancel)?$/.exec(path)
      if (paying && testing) {
        const [, id, act] = testing
        if (!act && req.method === 'GET') {
          const checkout = await checkoutOf(paying, null, id)
          return checkout ? void res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' }).end(testCheckoutPage(checkout)) : json(res, 404, { detail: 'not found' })
        }
        if (act && req.method === 'POST') {
          if (act === '/pay') await settle(paying, id, `test-${id}`)
          else await cancel(paying, id)
          return void res.writeHead(303, { location: `/app/settings/account?topup=${id}` }).end()
        }
      }
      // the link mailed to a backup address: opened wherever that mailbox is read, signed in or not
      if (path === '/api/account/backup-email/verify' && req.method === 'GET') {
        const ok = await verifyBackupEmail(c, url.searchParams.get('token') ?? '')
        return void res.writeHead(302, { location: ok ? '/app/settings/account' : '/app/?error=INVALID_TOKEN' }).end()
      }
      if (c.web && (path === '/app' || path.startsWith('/app/')) && (req.method === 'GET' || req.method === 'HEAD')) return serve(res, path === '/app' ? '/app/' : path)

      // Cloud save: the desktop app talks to these itself, with no browser and no cookie.
      if (cloud && path === '/api/device/start' && req.method === 'POST') {
        const said = (await body(req).catch(() => null)) as { name?: unknown } | null
        return json(res, 200, await startLink(cloud, said?.name))
      }
      if (cloud && path === '/api/device/poll' && req.method === 'POST') {
        const got = await pollLink(cloud, ((await body(req).catch(() => null)) as { secret?: unknown } | null)?.secret)
        return got === 'gone' ? json(res, 410, { detail: 'That link has expired.' }) : got === 'waiting' ? json(res, 202, { waiting: true }) : json(res, 200, got)
      }
      if (cloud && (path === '/api/cloud' || path.startsWith('/api/cloud/'))) {
        const device = await deviceOf(cloud, req) // a linked computer's token: these routes and nothing else
        if (!device) return json(res, 401, { detail: 'This computer is not linked to an account.', code: 'UNLINKED' })
        if (path === '/api/cloud' && req.method === 'GET') {
          const owner = (await c.pool.query('SELECT name, "deleteAt" FROM "user" WHERE id = $1', [device.user])).rows[0]
          const snapshot = await newest(cloud, device.user)
          const limits = cloud.limits ?? LIMITS
          return json(res, 200, { account: owner?.name ?? '', device: device.name, snapshot, maxBytes: cloud.maxBytes, kept: KEPT, free: limits.free, pricePerGbMonth: limits.microsPerGbMonth / 1e6, over: snapshot ? over(limits, snapshot.holds) : [], balance: Number(await balance(c.pool, device.user)) })
        }
        if (path === '/api/cloud' && req.method === 'PUT') {
          let holds: unknown = null
          try { holds = JSON.parse(url.searchParams.get('holds') ?? 'null') } catch { /* it says nothing about itself */ }
          const got = await upload(cloud, device, req, Number(url.searchParams.get('base') ?? 0), url.searchParams.get('force') === '1', holds)
          return json(res, got.status, { snapshot: got.snapshot, ...(got.status === 409 ? { code: 'NEWER' } : got.status === 413 ? { code: 'TOO_BIG', maxBytes: cloud.maxBytes } : got.status === 402 ? { code: 'NEEDS_CREDIT', over: got.over, free: (cloud.limits ?? LIMITS).free } : {}) })
        }
        if (path === '/api/cloud/download' && req.method === 'GET') return (await download(cloud, device.user, res)) ? undefined : json(res, 404, { detail: 'Nothing has been saved to the cloud yet.' })
        if (path === '/api/cloud/device' && req.method === 'DELETE') { await unlink(cloud, device.user, device.id); return json(res, 200, { ok: true }) }
        return json(res, 404, { detail: 'not found' })
      }

      const session = await c.auth.api.getSession({ headers: fromNodeHeaders(req.headers) })
      // the id names a folder on the engine's disk: one that could not is never sent
      if (!session?.user.emailVerified || !USER.test(session.user.id)) return json(res, 401, { detail: 'Sign in to continue.', code: 'SIGNED_OUT' })
      const user = session.user.id
      // a request that changes something comes from our own pages, never from another site
      if (req.method !== 'GET' && req.method !== 'HEAD' && req.headers.origin !== c.origin) return json(res, 403, { detail: 'wrong origin' })
      if (c.starter && !granted.has(user)) {
        await grant(c.pool, user, c.starter, 'starter', `starter:${user}`)
        granted.add(user)
      }
      const backupEmail = session.user.backupEmail ?? null
      const backupEmailVerified = !!session.user.backupEmailVerified
      const who = { id: user, name: session.user.name, email: session.user.email, backupEmail, backupEmailVerified }
      const deleteAt = session.user.deleteAt ?? null
      if (path === '/api/usage') return json(res, 200, await spending(c.pool, user))
      if (path === '/api/me') return json(res, 200, { user: { id: user, name: who.name, email: who.email }, balance: Number(await balance(c.pool, user)), deleteAt, backupEmail, backupEmailVerified })
      if (path === '/api/account/backup-email' && req.method === 'POST') {
        let said: unknown
        try { said = await body(req) } catch { said = null }
        return (await setBackupEmail(c, who, (said as { email?: unknown } | null)?.email)) ? json(res, 200, { ok: true }) : json(res, 422, { detail: 'That address cannot be the backup email.' })
      }
      if (path === '/api/account/backup-email' && req.method === 'DELETE') { await removeBackupEmail(c, who); return json(res, 200, { ok: true }) }
      if (path === '/api/account/export' && req.method === 'GET') {
        res.writeHead(200, { 'content-type': 'application/json', 'content-disposition': 'attachment; filename="kataki-account.json"', 'cache-control': 'no-store' })
        return void res.end(JSON.stringify(await exportOf(c, who), null, 2))
      }
      if (path === '/api/account/keep' && req.method === 'POST') { await keep(c, who); return json(res, 200, { ok: true }) }
      if (path === '/api/account/delete' && req.method === 'POST') {
        // only from a sign-in of the last ten minutes: a session left open on a shared computer cannot do this
        const fresh = Date.now() - new Date(session.session.createdAt).getTime() < 600_000
        if (!fresh) return json(res, 403, { detail: { code: 'FRESH', message: 'Sign in again to do this.' } })
        return json(res, 200, { deleteAt: await askToDelete(c, who) })
      }
      // adding credit (topup.ts): open a checkout, then come back and see how it went
      if (path === '/api/topup' && req.method === 'POST') {
        if (!paying) return json(res, 503, { detail: 'Credit cannot be bought here yet.', code: 'NO_PROCESSOR' })
        const said = (await body(req).catch(() => null)) as { dollars?: unknown } | null
        const made = await startTopup(paying, user, said?.dollars)
        return made ? json(res, 200, made) : json(res, 400, { detail: `Choose one of: ${AMOUNTS.map((a) => `$${a}`).join(', ')}.` })
      }
      if (paying && path.startsWith('/api/topup/') && req.method === 'GET') {
        const checkout = await checkoutOf(paying, user, path.slice('/api/topup/'.length))
        return checkout ? json(res, 200, checkout) : json(res, 404, { detail: 'not found' })
      }
      // linking a computer: approved here, by the signed-in person, and listed and removed here
      if (cloud && path === '/api/device/link' && req.method === 'GET') {
        const name = await linkName(cloud, url.searchParams.get('code') ?? '')
        return name ? json(res, 200, { name }) : json(res, 404, { detail: 'That code is not waiting. Ask for a new one on your computer.' })
      }
      if (cloud && path === '/api/device/approve' && req.method === 'POST') {
        const said = (await body(req).catch(() => null)) as { code?: unknown } | null
        return (await approveLink(cloud, user, String(said?.code ?? ''))) ? json(res, 200, { ok: true }) : json(res, 404, { detail: 'That code is not waiting. Ask for a new one on your computer.' })
      }
      if (cloud && path === '/api/devices' && req.method === 'GET') return json(res, 200, await devices(cloud, user))
      if (cloud && path.startsWith('/api/devices/') && req.method === 'DELETE') return json(res, (await unlink(cloud, user, path.slice('/api/devices/'.length))) ? 200 : 404, { ok: true })
      // a leaving account opens nothing until it says it is staying
      if (deleteAt) return json(res, 401, { detail: 'This account is set to be deleted.', code: 'DELETING' })
      // the engine's routes for the gateway alone are never a browser's to call
      if (path.startsWith('/_gateway/') || path === FORGET) return json(res, 404, { detail: 'not found' })
      proxy(req, res, user)
    } catch (e) {
      console.error('gateway:', e instanceof Error ? e.message : e)
      if (!res.headersSent) json(res, 500, { detail: 'Something went wrong.' })
      else res.end()
    }
  }
}
