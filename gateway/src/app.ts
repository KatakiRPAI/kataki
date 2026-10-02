// The gateway's HTTP surface (docs/specs/2026-10-02-kataki-online.md §1):
//   /api/auth/*        Better Auth
//   /api/me            who is signed in, and their balance
//   /allow, /usage     the engine asks (its bearer key)
//   /app/*             the web build
//   everything else    a signed request to the engine, for whoever the session says
import { timingSafeEqual } from 'node:crypto'
import { createReadStream, existsSync, statSync } from 'node:fs'
import { request, type IncomingMessage, type RequestListener, type ServerResponse } from 'node:http'
import { extname, join, normalize, sep } from 'node:path'
import { fromNodeHeaders, toNodeHandler } from 'better-auth/node'
import type { Pool } from 'pg'
import { askToDelete, exportOf, FORGET, keep } from './account.ts'
import type { Auth, Send } from './auth.ts'
import { allow, balance, bill, grant } from './ledger.ts'
import type { Prices } from './money.ts'
import { signed, USER } from './sign.ts'

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
      if (path === '/api/providers') return json(res, 200, { social: c.social ?? [] })
      if (c.web && (path === '/app' || path.startsWith('/app/')) && (req.method === 'GET' || req.method === 'HEAD')) return serve(res, path === '/app' ? '/app/' : path)

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
      const who = { id: user, name: session.user.name, email: session.user.email }
      const deleteAt = session.user.deleteAt ?? null
      if (path === '/api/me') return json(res, 200, { user: who, balance: Number(await balance(c.pool, user)), deleteAt })
      if (path === '/api/account/export' && req.method === 'GET') {
        res.writeHead(200, { 'content-type': 'application/json', 'content-disposition': 'attachment; filename="kataki-account.json"', 'cache-control': 'no-store' })
        return void res.end(JSON.stringify(await exportOf(c, who), null, 2))
      }
      if (path === '/api/account/keep' && req.method === 'POST') { await keep(c, who); return json(res, 200, { ok: true }) }
      if (path === '/api/account/delete' && req.method === 'POST') {
        // only from a sign-in of the last ten minutes: a session left open on a shared computer cannot do this
        const fresh = Date.now() - new Date(session.session.createdAt).getTime() < 600_000
        if (!fresh) return json(res, 403, { detail: 'Sign in again to do this.', code: 'FRESH' })
        return json(res, 200, { deleteAt: await askToDelete(c, who) })
      }
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
