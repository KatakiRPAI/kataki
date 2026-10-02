// The gateway end to end, on PGlite and a stand-in engine that checks the signature it is sent.
import assert from 'node:assert/strict'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { createServer, type IncomingMessage, type RequestListener, type Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, test } from 'node:test'
import { PGlite } from '@electric-sql/pglite'
import { PGLiteSocketServer } from '@electric-sql/pglite-socket'
import pg from 'pg'
import { createGateway } from './app.ts'
import { makeAuth, migrateAuth } from './auth.ts'
import { migrate } from './db.ts'
import { balance } from './ledger.ts'
import { sign } from './sign.ts'

const SECRET = 'a signing secret of thirty-two b.'
const KEY = 'the engine key'
const PRICES = { 'rp-1': { input: 0.15, cached: 0.075, output: 0.6 } }
const PASSWORD = 'correct horse battery'

const mails: { to: string; text: string }[] = []
const seen: { method: string; url: string; headers: IncomingMessage['headers']; body: string }[] = []
let db: PGlite, socket: PGLiteSocketServer, pool: pg.Pool, engine: Server, gateway: Server, origin: string

const listen = (server: Server) => new Promise<number>((done) => server.listen(0, '127.0.0.1', () => done((server.address() as AddressInfo).port)))

before(async () => {
  db = await PGlite.create()
  socket = new PGLiteSocketServer({ db, port: 54330, host: '127.0.0.1' })
  await socket.start()
  pool = new pg.Pool({ connectionString: 'postgres://postgres@127.0.0.1:54330/postgres', max: 1 })

  // the engine: answers only a request signed for exactly its method and target, within a minute
  engine = createServer(async (req, res) => {
    let body = ''
    for await (const chunk of req) body += chunk
    const h = req.headers
    const url = req.url!
    const target = url.includes('?') ? url : `${url}?`
    const fresh = Math.abs(Date.now() / 1000 - Number(h['x-kataki-time'])) < 60
    if (!fresh || h['x-kataki-sig'] !== sign(SECRET, String(h['x-kataki-user']), String(h['x-kataki-channel']), Number(h['x-kataki-time']), req.method!, target)) {
      return void res.writeHead(401).end('{"detail":"missing or invalid gateway signature"}')
    }
    seen.push({ method: req.method!, url, headers: h, body })
    res.writeHead(200, { 'content-type': 'application/json' }).end(JSON.stringify({ user: h['x-kataki-user'] }))
  })
  const enginePort = await listen(engine)

  const web = mkdtempSync(join(tmpdir(), 'kataki-web-'))
  mkdirSync(join(web, 'assets'))
  writeFileSync(join(web, 'index.html'), '<title>Kataki</title>')
  writeFileSync(join(web, 'assets', 'app-a1b2c3d4.js'), 'console.log(1)')
  writeFileSync(join(web, '..', 'outside.txt'), 'not yours')

  let handler: RequestListener = () => {}
  gateway = createServer((req, res) => handler(req, res))
  origin = `http://127.0.0.1:${await listen(gateway)}`
  const auth = makeAuth({ pool, origin, secret: 'x7Kq'.repeat(10), pwned: false, send: (to, _subject, text) => void mails.push({ to, text }) })
  await migrateAuth(auth)
  await migrate(pool)
  await migrate(pool) // again: nothing to do, nothing breaks
  handler = createGateway({ auth, pool, origin, engine: `http://127.0.0.1:${enginePort}`, secret: SECRET, key: KEY, prices: PRICES, web, starter: 1_000_000n })
})

after(async () => {
  gateway.close()
  engine.close()
  await pool.end()
  await socket.stop()
  await db.close()
})

const call = (path: string, init: RequestInit & { cookie?: string } = {}) =>
  fetch(origin + path, { redirect: 'manual', ...init, headers: { ...(init.cookie ? { cookie: init.cookie } : {}), ...init.headers } })
const post = (path: string, body: unknown, init: RequestInit & { cookie?: string } = {}) =>
  call(path, { method: 'POST', body: JSON.stringify(body), ...init, headers: { 'content-type': 'application/json', origin, ...init.headers } })
const asEngine = { authorization: `Bearer ${KEY}` }

/** Sign up, open the mailed link, and come back with the session cookie and the user's id. */
async function account(email: string): Promise<{ cookie: string; id: string }> {
  const r = await post('/api/auth/sign-up/email', { name: 'Qais', email, password: PASSWORD, adult: true, callbackURL: '/app/' })
  assert.equal(r.status, 200)
  const link = mails.findLast((m) => m.to === email)!.text.match(/http\S+/)![0]
  const verified = await call(link.slice(origin.length))
  assert.equal(verified.status, 302)
  assert.equal(verified.headers.get('location'), '/app/')
  const cookie = verified.headers.get('set-cookie')!.split(';')[0]
  const me = (await (await call('/api/me', { cookie })).json()) as { user: { id: string } }
  return { cookie, id: me.user.id }
}

test('signed out, nothing reaches the engine', async () => {
  const r = await call('/stories')
  assert.equal(r.status, 401)
  assert.equal(((await r.json()) as { code: string }).code, 'SIGNED_OUT')
  assert.equal(seen.length, 0)
})

test('an account holds nothing until its email is confirmed', async () => {
  await post('/api/auth/sign-up/email', { name: 'Nobody', email: 'unconfirmed@example.com', password: PASSWORD, adult: true })
  const r = await post('/api/auth/sign-in/email', { email: 'unconfirmed@example.com', password: PASSWORD })
  assert.equal(r.status, 403)
  assert.equal(r.headers.get('set-cookie'), null)
})

test('signing up with a known address answers like a new one', async () => {
  await account('known@example.com')
  const again = await post('/api/auth/sign-up/email', { name: 'Someone else', email: 'known@example.com', password: PASSWORD, adult: true })
  assert.equal(again.status, 200)
  assert.equal(((await again.json()) as { token: unknown }).token, null)
  assert.equal(mails.at(-1)!.to, 'known@example.com') // and the owner of the address hears of it
  assert.match(mails.at(-1)!.text, /already have one/)
})

test('a short password is refused', async () => {
  const r = await post('/api/auth/sign-up/email', { name: 'Short', email: 'short@example.com', password: 'elevenchars', adult: true })
  assert.equal(r.status, 400)
})

test('an account is for someone who says they are 18 or older', async () => {
  for (const adult of [false, undefined]) {
    const r = await post('/api/auth/sign-up/email', { name: 'Young', email: 'young@example.com', password: PASSWORD, adult })
    assert.equal(r.status, 400)
  }
  assert.equal(mails.some((m) => m.to === 'young@example.com'), false)
})

test('signed in, a request reaches the engine signed as that user and nothing else', async () => {
  const { cookie, id } = await account('qais@example.com')
  assert.match(id, /^[0-9a-f-]{36}$/) // a lowercase uuid: the library's folder name
  const r = await call('/stories?x=1&y=%20z', { cookie, headers: { 'x-kataki-user': 'someone-else', authorization: 'Bearer stolen' } })
  assert.equal(r.status, 200)
  assert.deepEqual(await r.json(), { user: id })
  const got = seen.at(-1)!
  assert.equal(got.url, '/stories?x=1&y=%20z')
  assert.equal(got.headers['x-kataki-user'], id)
  assert.equal(got.headers.cookie, undefined)
  assert.equal(got.headers.authorization, undefined)
})

test('a request that changes something must come from our own pages', async () => {
  const { cookie } = await account('writer@example.com')
  const before = seen.length
  const foreign = await post('/stories', { title: 'x' }, { cookie, headers: { origin: 'https://evil.example' } })
  assert.equal(foreign.status, 403)
  const none = await call('/stories', { method: 'POST', cookie, body: '{}' })
  assert.equal(none.status, 403)
  assert.equal(seen.length, before)
  const ours = await post('/stories', { title: 'Low tide' }, { cookie })
  assert.equal(ours.status, 200)
  assert.equal(seen.at(-1)!.body, '{"title":"Low tide"}')
})

test('the ledger: starting credit once, a call billed once, and the gate', async () => {
  const { cookie, id } = await account('spender@example.com')
  await call('/api/me', { cookie })
  assert.equal(await balance(pool, id), 1_000_000n) // given once, however many requests

  assert.equal((await call(`/allow?user=${id}&estimate=0.5`)).status, 401) // not the engine
  const allowed = async (estimate: number) => ((await (await call(`/allow?user=${id}&estimate=${estimate}`, { headers: asEngine })).json()) as { ok: boolean }).ok
  assert.equal(await allowed(0.5), true)
  assert.equal(await allowed(2), false)

  const row = { user: id, usage_id: 'ab'.repeat(16), story_id: 1, role: 'rp', model: 'rp-1', prompt_tokens: 1000, cached_tokens: 400, completion_tokens: 200, cost: 0.00024, estimated: false, at: '2026-10-02 10:57:33' }
  assert.equal((await post('/usage', row)).status, 401)
  assert.equal((await post('/usage', row, { headers: asEngine })).status, 200)
  assert.equal((await post('/usage', row, { headers: asEngine })).status, 409) // sent again: not billed again
  assert.equal(await balance(pool, id), 1_000_000n - 240n) // from its tokens, never from `cost`
  assert.equal((await post('/usage', { ...row, usage_id: 'cd'.repeat(16), model: 'unpriced' }, { headers: asEngine })).status, 422)
  assert.equal((await post('/usage', { ...row, usage_id: 'cd'.repeat(16), prompt_tokens: -1 }, { headers: asEngine })).status, 422)
  assert.equal((await call('/usage', { method: 'POST', body: 'not json', headers: asEngine })).status, 400)

  const big = { ...row, usage_id: 'ef'.repeat(16), prompt_tokens: 8_000_000, cached_tokens: 0, completion_tokens: 0 }
  assert.equal((await post('/usage', big, { headers: asEngine })).status, 200) // one call may take it below zero
  assert.equal(await allowed(0), false) // and the next is refused
  const me = (await (await call('/api/me', { cookie })).json()) as { balance: number }
  assert.equal(me.balance, 1_000_000 - 240 - 1_200_000)
})

test('a forgotten password: a mailed link, a new password, every device signed out, and a notice', async () => {
  const email = 'forgetful@example.com'
  const { cookie } = await account(email)
  const before = mails.length
  assert.equal((await post('/api/auth/request-password-reset', { email: 'nobody@example.com', redirectTo: '/app/' })).status, 200)
  assert.equal(mails.length, before) // the same answer, and no mail to someone who is not here
  assert.equal((await post('/api/auth/request-password-reset', { email, redirectTo: '/app/' })).status, 200)
  const link = mails.at(-1)!.text.match(/http\S+/)![0]
  const opened = await call(link.slice(origin.length)) // opening it uses nothing up
  const token = new URL(opened.headers.get('location')!, origin).searchParams.get('token')!
  assert.ok(token)
  assert.equal((await post('/api/auth/reset-password', { newPassword: 'too short', token })).status, 400)
  assert.equal((await post('/api/auth/reset-password', { newPassword: 'a brand new pass phrase', token })).status, 200)
  assert.match(mails.at(-1)!.text, /was just changed/)
  assert.equal((await post('/api/auth/reset-password', { newPassword: 'and another pass phrase', token })).status, 400) // once
  assert.equal((await post('/api/auth/sign-in/email', { email, password: PASSWORD })).status, 401)
  assert.equal((await post('/api/auth/sign-in/email', { email, password: 'a brand new pass phrase' })).status, 200)
  assert.equal((await call('/stories', { cookie })).status, 401) // the old session is gone
})

test('a sign-in link: only for an account, used by a button and only once', async () => {
  const email = 'linker@example.com'
  await account(email)
  const before = mails.length
  assert.equal((await post('/api/auth/sign-in/magic-link', { email: 'nobody@example.com', callbackURL: '/app/' })).status, 200)
  assert.equal(mails.length, before)
  assert.equal((await post('/api/auth/sign-in/magic-link', { email, callbackURL: '/app/' })).status, 200)
  const page = new URL(mails.at(-1)!.text.match(/http\S+/)![0])
  assert.equal(page.pathname, '/app/') // our page, not the request that uses the token up
  const token = page.searchParams.get('magic')!
  assert.match(await (await call(page.pathname + page.search)).text(), /Kataki/) // a scanner opening it burns nothing
  const used = await call(`/api/auth/magic-link/verify?token=${token}&callbackURL=%2Fapp%2F`)
  assert.equal(used.status, 302)
  const cookie = used.headers.get('set-cookie')!.split(';')[0]
  assert.equal((await call('/stories', { cookie })).status, 200)
  const again = await call(`/api/auth/magic-link/verify?token=${token}&callbackURL=%2Fapp%2F`)
  assert.equal(again.headers.get('set-cookie'), null)
})

test('the web build is served, and nothing outside it', async () => {
  assert.equal((await call('/')).headers.get('location'), '/app/')
  assert.match(await (await call('/app/')).text(), /Kataki/)
  assert.match(await (await call('/app/settings/general')).text(), /Kataki/) // the app routes itself
  const asset = await call('/app/assets/app-a1b2c3d4.js')
  assert.match(asset.headers.get('cache-control')!, /immutable/)
  const out = await call('/app/..%2Foutside.txt')
  assert.doesNotMatch(await out.text(), /not yours/)
})
