// The gateway end to end, on PGlite and a stand-in engine that checks the signature it is sent.
import assert from 'node:assert/strict'
import { existsSync, mkdirSync, mkdtempSync, readdirSync, writeFileSync } from 'node:fs'
import { createHmac } from 'node:crypto'
import { createServer, type IncomingMessage, type RequestListener, type Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, test } from 'node:test'
import { PGlite } from '@electric-sql/pglite'
import { PGLiteSocketServer } from '@electric-sql/pglite-socket'
import pg from 'pg'
import { GRACE_DAYS, sweep, type AccountConfig } from './account.ts'
import { chargeStorage } from './cloud.ts'
import { createGateway } from './app.ts'
import { makeAuth, migrateAuth, personChecked, socialFrom, usernameOk } from './auth.ts'
import { migrate } from './db.ts'
import { balance } from './ledger.ts'
import { sign } from './sign.ts'

const SECRET = 'a signing secret of thirty-two b.'
const KEY = 'the engine key'
const PRICES = { 'rp-1': { input: 0.15, cached: 0.075, output: 0.6 } }
const PASSWORD = 'correct horse battery'

const mails: { to: string; text: string }[] = []
const seen: { method: string; url: string; headers: IncomingMessage['headers']; body: string }[] = []
let db: PGlite, socket: PGLiteSocketServer, pool: pg.Pool, engine: Server, gateway: Server, provider: Server, origin: string, leaving: AccountConfig
let forgetStatus = 200 // what the stand-in engine answers when asked to forget a library
let cloudDir = ''

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
    if (url === '/_gateway/forget') return void res.writeHead(forgetStatus, { 'content-type': 'application/json' }).end('{}')
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
  // another service: answers any code with one person, as GitHub would after "Authorize"
  // the code it is given says who: `a-code` is Octo, any other code is its own person
  provider = createServer(async (req, res) => {
    let sent = ''
    for await (const chunk of req) sent += chunk
    const who = req.url!.startsWith('/token') ? new URLSearchParams(sent).get('code')! : String(req.headers.authorization).replace('Bearer ', '')
    const body = req.url!.startsWith('/token') ? { access_token: who, token_type: 'bearer' }
      : who === 'a-code' ? { id: 'gh-1', sub: 'gh-1', email: 'octo@example.com', email_verified: true, name: 'Octo' }
        : { id: who, sub: who, email: `${who}@example.com`, email_verified: true, name: who }
    res.writeHead(200, { 'content-type': 'application/json' }).end(JSON.stringify(body))
  })
  const there = `http://127.0.0.1:${await listen(provider)}`
  const others = [{ providerId: 'fake', clientId: 'an-id', clientSecret: 'a-secret', authorizationUrl: `${there}/authorize`, tokenUrl: `${there}/token`, userInfoUrl: `${there}/userinfo`, scopes: ['email'] }]
  const social = socialFrom({ GITHUB_CLIENT_ID: 'an-id', GITHUB_CLIENT_SECRET: 'a-secret', GOOGLE_CLIENT_ID: 'half-set' })
  const send = (to: string, _subject: string, text: string) => void mails.push({ to, text })
  cloudDir = mkdtempSync(join(tmpdir(), 'kataki-cloud-'))
  const cloud = { dir: cloudDir, maxBytes: 1000, limits: { free: { stories: 2, characters: 3 }, microsPerGbMonth: 100_000 } }
  const auth = makeAuth({ pool, origin, secret: 'x7Kq'.repeat(10), pwned: false, social, others, send })
  await migrateAuth(auth)
  await migrate(pool)
  await migrate(pool) // again: nothing to do, nothing breaks
  handler = createGateway({ auth, pool, origin, engine: `http://127.0.0.1:${enginePort}`, secret: SECRET, key: KEY, prices: PRICES, web, starter: 1_000_000n, social: Object.keys(social), send, cloud })
  leaving = { auth, pool, origin, engine: `http://127.0.0.1:${enginePort}`, secret: SECRET, send, cloud }
})

after(async () => {
  gateway.close()
  engine.close()
  provider.close()
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

test('another service is offered only when both its keys are set', async () => {
  assert.deepEqual(await (await call('/api/providers')).json(), { social: ['github'] })
  const go = await post('/api/auth/sign-in/social', { provider: 'github', callbackURL: '/app/' })
  assert.equal(go.status, 200)
  const { url } = (await go.json()) as { url: string }
  const there = new URL(url)
  assert.equal(there.origin, 'https://github.com')
  assert.equal(there.searchParams.get('client_id'), 'an-id')
  assert.equal(there.searchParams.get('redirect_uri'), `${origin}/api/auth/callback/github`)
  assert.match(there.searchParams.get('scope')!, /user:email/) // the verified address, never the profile's
  assert.notEqual((await post('/api/auth/sign-in/social', { provider: 'google', callbackURL: '/app/' })).status, 200)
})

/** What an authenticator app shows for this secret (RFC 6238: SHA-1, 30 seconds, 6 digits). */
function totp(secret: string, at = Date.now()): string {
  const bits = [...secret.replace(/=+$/, '')].map((ch) => 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'.indexOf(ch).toString(2).padStart(5, '0')).join('')
  const key = Buffer.from(bits.match(/.{8}/g)!.map((b) => Number.parseInt(b, 2)))
  const counter = Buffer.alloc(8)
  counter.writeBigUInt64BE(BigInt(Math.floor(at / 30_000)))
  const mac = createHmac('sha1', key).update(counter).digest()
  const from = mac[mac.length - 1] & 15
  return String((mac.readUInt32BE(from) & 0x7fffffff) % 1_000_000).padStart(6, '0')
}
const cookies = (r: Response) => r.headers.getSetCookie().map((c) => c.split(';')[0]).join('; ')

test('two-step sign-in: after a password, after a sign-in link, and a backup code once', async () => {
  const email = 'careful@example.com'
  const { cookie } = await account(email)
  assert.equal((await post('/api/auth/two-factor/enable', { password: 'not my password' }, { cookie })).status, 400)
  const on = await post('/api/auth/two-factor/enable', { password: PASSWORD }, { cookie })
  assert.equal(on.status, 200)
  const { totpURI, backupCodes } = (await on.json()) as { totpURI: string; backupCodes: string[] }
  assert.equal(backupCodes.length, 10)
  const secret = new URL(totpURI).searchParams.get('secret')!
  assert.match(totpURI, /issuer=Kataki/)
  // it is on only once a code from the app has been typed back
  assert.equal((await post('/api/auth/two-factor/verify-totp', { code: totp(secret) }, { cookie })).status, 200)

  const first = await post('/api/auth/sign-in/email', { email, password: PASSWORD })
  assert.equal(((await first.json()) as { twoFactorRedirect?: boolean }).twoFactorRedirect, true)
  assert.doesNotMatch(cookies(first), /session_token=[^;]/) // the password alone opens nothing
  assert.notEqual((await post('/api/auth/two-factor/verify-totp', { code: '000000' }, { cookie: cookies(first) })).status, 200)
  const second = await post('/api/auth/two-factor/verify-totp', { code: totp(secret) }, { cookie: cookies(first) })
  assert.equal(second.status, 200)
  assert.equal((await call('/stories', { cookie: cookies(second) })).status, 200)

  const again = await post('/api/auth/sign-in/email', { email, password: PASSWORD })
  assert.equal((await post('/api/auth/two-factor/verify-backup-code', { code: backupCodes[0] }, { cookie: cookies(again) })).status, 200)
  const reused = await post('/api/auth/sign-in/email', { email, password: PASSWORD })
  assert.notEqual((await post('/api/auth/two-factor/verify-backup-code', { code: backupCodes[0] }, { cookie: cookies(reused) })).status, 200)

  // a sign-in link does not walk past the second step
  await post('/api/auth/sign-in/magic-link', { email, callbackURL: '/app/' })
  const token = new URL(mails.at(-1)!.text.match(/http\S+/)![0]).searchParams.get('magic')!
  const linked = await call(`/api/auth/magic-link/verify?token=${token}&callbackURL=%2Fapp%2F`)
  assert.equal(linked.status, 302)
  assert.equal(linked.headers.get('location'), `${origin}/app/?step=2`)
  assert.doesNotMatch(cookies(linked), /session_token=[^;]/)
  assert.equal((await call('/stories', { cookie: cookies(linked) })).status, 401)
  const done = await post('/api/auth/two-factor/verify-totp', { code: totp(secret) }, { cookie: cookies(linked) })
  assert.equal(done.status, 200)
  assert.equal((await call('/stories', { cookie: cookies(done) })).status, 200)
})

/** Leave for the other service and come back, as the browser does after "Authorize". */
async function viaProvider(extra: Record<string, unknown>, code = 'a-code') {
  const left = await post('/api/auth/sign-in/social', { provider: 'fake', callbackURL: '/app/', errorCallbackURL: '/app/', ...extra })
  assert.equal(left.status, 200)
  const state = new URL(((await left.json()) as { url: string }).url).searchParams.get('state')!
  const cookie = left.headers.getSetCookie().map((c) => c.split(';')[0]).join('; ')
  const back = await call(`/api/auth/callback/fake?code=${code}&state=${encodeURIComponent(state)}`, { cookie })
  return { location: back.headers.get('location') ?? '', session: back.headers.getSetCookie().find((c) => c.includes('session_token'))?.split(';')[0] }
}

test('another service: signing in never makes an account; creating one does, and carries 18 or older', async () => {
  const none = await viaProvider({})
  assert.match(none.location, /^\/app\/\?error=signup_disabled/)
  assert.equal(none.session, undefined)

  const unsaid = await viaProvider({ requestSignUp: true })
  assert.match(unsaid.location, /error=/) // asked to create, never said 18 or older
  assert.equal(unsaid.session, undefined)

  const made = await viaProvider({ requestSignUp: true, additionalData: { adult: true } })
  assert.equal(made.location, '/app/')
  const me = (await (await call('/api/me', { cookie: made.session! })).json()) as { user: { email: string; id: string } }
  assert.equal(me.user.email, 'octo@example.com')
  assert.match(me.user.id, /^[0-9a-f-]{36}$/)

  const again = await viaProvider({}) // and now plain sign-in works
  assert.equal(again.location, '/app/')
  assert.ok(again.session)
})

test('two-step sign-in is asked after another service too', async () => {
  // the account made through the other service gets a password (the reset link), then turns it on
  const email = 'octo@example.com'
  await post('/api/auth/request-password-reset', { email, redirectTo: '/app/' })
  const opened = await call(mails.at(-1)!.text.match(/http\S+/)![0].slice(origin.length))
  const token = new URL(opened.headers.get('location')!, origin).searchParams.get('token')!
  assert.equal((await post('/api/auth/reset-password', { newPassword: PASSWORD, token })).status, 200)
  const signedIn = cookies(await post('/api/auth/sign-in/email', { email, password: PASSWORD }))
  const on = (await (await post('/api/auth/two-factor/enable', { password: PASSWORD }, { cookie: signedIn })).json()) as { totpURI: string }
  const secret = new URL(on.totpURI).searchParams.get('secret')!
  assert.equal((await post('/api/auth/two-factor/verify-totp', { code: totp(secret) }, { cookie: signedIn })).status, 200)

  const left = await post('/api/auth/sign-in/social', { provider: 'fake', callbackURL: '/app/', errorCallbackURL: '/app/' })
  const state = new URL(((await left.json()) as { url: string }).url).searchParams.get('state')!
  const back = await call(`/api/auth/callback/fake?code=a-code&state=${encodeURIComponent(state)}`, { cookie: cookies(left) })
  assert.equal(back.headers.get('location'), `${origin}/app/?step=2`)
  assert.equal((await call('/stories', { cookie: cookies(back) })).status, 401) // the other service alone opens nothing
  const done = await post('/api/auth/two-factor/verify-totp', { code: totp(secret) }, { cookie: cookies(back) })
  assert.equal((await call('/stories', { cookie: cookies(done) })).status, 200)
})

test('an account can see where it is signed in, and sign the other places out', async () => {
  const email = 'everywhere@example.com'
  const { cookie } = await account(email)
  const phone = cookies(await post('/api/auth/sign-in/email', { email, password: PASSWORD }))
  const listed = (await (await call('/api/auth/list-sessions', { cookie })).json()) as unknown[]
  assert.equal(listed.length, 2)
  assert.equal((await post('/api/auth/revoke-other-sessions', {}, { cookie })).status, 200)
  assert.equal((await call('/stories', { cookie: phone })).status, 401)
  assert.equal((await call('/stories', { cookie })).status, 200)
})

test('a changed password: the old one is needed, the other places are signed out, the owner is told', async () => {
  const email = 'changer@example.com'
  const { cookie } = await account(email)
  const phone = cookies(await post('/api/auth/sign-in/email', { email, password: PASSWORD }))
  const next = 'an entirely new pass phrase'
  assert.notEqual((await post('/api/auth/change-password', { currentPassword: 'not it at all here', newPassword: next, revokeOtherSessions: true }, { cookie })).status, 200)
  const before = mails.length
  const changed = await post('/api/auth/change-password', { currentPassword: PASSWORD, newPassword: next, revokeOtherSessions: true }, { cookie })
  assert.equal(changed.status, 200)
  assert.equal(mails.length, before + 1)
  assert.match(mails.at(-1)!.text, /was just changed/)
  assert.equal((await call('/stories', { cookie: phone })).status, 401)
  assert.equal((await post('/api/auth/sign-in/email', { email, password: next })).status, 200)
})

test('a changed email: approved from the old address, confirmed from the new one', async () => {
  const old = 'old@example.com'
  const fresh = 'fresh@example.com'
  const { cookie } = await account(old)
  assert.equal((await post('/api/auth/change-email', { newEmail: fresh, callbackURL: '/app/' }, { cookie })).status, 200)
  assert.equal(mails.at(-1)!.to, old) // nothing moves until the old address says so
  assert.equal((await post('/api/auth/sign-in/email', { email: fresh, password: PASSWORD })).status, 401)
  await call(mails.at(-1)!.text.match(/http\S+/)![0].slice(origin.length), { cookie })
  assert.equal(mails.at(-1)!.to, fresh)
  await call(mails.at(-1)!.text.match(/http\S+/)![0].slice(origin.length), { cookie })
  assert.equal((await post('/api/auth/sign-in/email', { email: fresh, password: PASSWORD })).status, 200)
  assert.equal((await post('/api/auth/sign-in/email', { email: old, password: PASSWORD })).status, 401)
})

test('leaving: signed out at once, fourteen days to stay, then the library and the account go', async () => {
  const email = 'leaver@example.com'
  const { cookie, id } = await account(email)
  assert.equal((await call('/_gateway/forget', { method: 'POST', cookie, headers: { origin } })).status, 404) // never a browser's to call
  const asked = await post('/api/account/delete', {}, { cookie })
  assert.equal(asked.status, 200)
  const { deleteAt } = (await asked.json()) as { deleteAt: string }
  assert.equal(Math.round((Date.parse(deleteAt) - Date.now()) / 86_400_000), GRACE_DAYS)
  assert.match(mails.at(-1)!.text, /will be deleted on/)
  assert.equal((await call('/stories', { cookie })).status, 401) // signed out everywhere

  // signing in again shows what is coming, opens nothing, and can undo it
  const back = cookies(await post('/api/auth/sign-in/email', { email, password: PASSWORD }))
  assert.ok(((await (await call('/api/me', { cookie: back })).json()) as { deleteAt: string | null }).deleteAt)
  assert.equal(((await (await call('/stories', { cookie: back })).json()) as { code: string }).code, 'DELETING')
  assert.equal(await sweep(leaving), 0) // not its day yet
  assert.equal((await post('/api/account/keep', {}, { cookie: back })).status, 200)
  assert.equal((await call('/stories', { cookie: back })).status, 200)

  // asked again, and this time the day comes
  assert.equal((await post('/api/account/delete', {}, { cookie: back })).status, 200)
  const theDay = new Date(Date.now() + (GRACE_DAYS + 1) * 86_400_000)
  forgetStatus = 409 // the engine still has usage to bill: nothing goes yet
  assert.equal(await sweep(leaving, theDay), 0)
  assert.equal((await post('/api/auth/sign-in/email', { email, password: PASSWORD })).status, 200)
  forgetStatus = 200
  assert.equal(await sweep(leaving, theDay), 1)
  assert.equal(seen.at(-1)!.url, '/_gateway/forget')
  assert.equal(seen.at(-1)!.headers['x-kataki-user'], id) // the engine is told whose library
  assert.equal((await post('/api/auth/sign-in/email', { email, password: PASSWORD })).status, 401) // gone
  assert.equal((await pool.query('SELECT count(*) AS n FROM credit WHERE user_id = $1', [id])).rows[0].n, '1') // the payment record stays
})

test('deleting needs a sign-in of the last ten minutes', async () => {
  const { cookie, id } = await account('stale@example.com')
  await pool.query(`UPDATE session SET "createdAt" = now() - interval '11 minutes' WHERE "userId" = $1`, [id])
  const r = await post('/api/account/delete', {}, { cookie })
  assert.equal(r.status, 403)
  assert.equal(((await r.json()) as { detail: { code: string } }).detail.code, 'FRESH')
})

test('an account can take what the gateway holds about it', async () => {
  const { cookie } = await account('exporter@example.com')
  const r = await call('/api/account/export', { cookie })
  assert.match(r.headers.get('content-disposition')!, /kataki-account\.json/)
  const got = (await r.json()) as { account: { email: string }; signInMethods: { providerId: string }[]; credit: unknown[]; balanceMicroDollars: number }
  assert.equal(got.account.email, 'exporter@example.com')
  assert.deepEqual(got.signInMethods.map((m) => m.providerId), ['credential'])
  assert.equal(got.credit.length, 1)
  assert.equal(got.balanceMicroDollars, 1_000_000)
  assert.equal(JSON.stringify(got).includes('password'), false) // never the hash
})

test('a backup email hears of changes once it has confirmed itself, and can do nothing else', async () => {
  const email = 'primary@example.com'
  const backup = 'backup@example.com'
  const { cookie } = await account(email)
  assert.equal((await post('/api/account/backup-email', { email }, { cookie })).status, 422) // not the same address
  assert.equal((await post('/api/account/backup-email', { email: 'not an address' }, { cookie })).status, 422)
  assert.equal((await post('/api/account/backup-email', { email: backup }, { cookie })).status, 200)
  const link = mails.at(-1)!
  assert.equal(link.to, backup)

  // silent until confirmed
  let before = mails.length
  await post('/api/auth/change-password', { currentPassword: PASSWORD, newPassword: 'the second pass phrase', revokeOtherSessions: false }, { cookie })
  assert.deepEqual(mails.slice(before).map((m) => m.to), [email])

  assert.equal((await call('/api/account/backup-email/verify?token=wrong')).headers.get('location'), '/app/?error=INVALID_TOKEN')
  const opened = await call(link.text.match(/http\S+/)![0].slice(origin.length)) // from any browser
  assert.equal(opened.headers.get('location'), '/app/settings/account')
  assert.equal((await call(link.text.match(/http\S+/)![0].slice(origin.length))).headers.get('location'), '/app/?error=INVALID_TOKEN') // once
  const me = (await (await call('/api/me', { cookie })).json()) as { backupEmail: string; backupEmailVerified: boolean }
  assert.deepEqual([me.backupEmail, me.backupEmailVerified], [backup, true])

  before = mails.length
  await post('/api/auth/change-password', { currentPassword: 'the second pass phrase', newPassword: 'the third pass phrase!', revokeOtherSessions: false }, { cookie })
  assert.deepEqual(mails.slice(before).map((m) => m.to).sort(), [backup, email])

  // it hears; it cannot get in
  before = mails.length
  await post('/api/auth/request-password-reset', { email: backup, redirectTo: '/app/' })
  await post('/api/auth/sign-in/magic-link', { email: backup, callbackURL: '/app/' })
  assert.equal(mails.length, before)

  assert.equal((await call('/api/account/backup-email', { method: 'DELETE', cookie, headers: { origin } })).status, 200)
  assert.equal(((await (await call('/api/me', { cookie })).json()) as { backupEmail: string | null }).backupEmail, null)
})

test('passkeys: offered to a signed-in account, for this site, with the person checked each time', async () => {
  const { cookie } = await account('keyholder@example.com')
  assert.equal((await call('/api/auth/passkey/generate-register-options')).status, 401) // an account adds its own
  const make = (await (await call('/api/auth/passkey/generate-register-options?name=Laptop', { cookie })).json()) as {
    rp: { id: string; name: string }; challenge: string; authenticatorSelection: { userVerification: string }
  }
  assert.deepEqual(make.rp, { id: '127.0.0.1', name: 'Kataki' })
  assert.ok(make.challenge.length > 20)
  assert.equal(make.authenticatorSelection.userVerification, 'required')
  const use = (await (await call('/api/auth/passkey/generate-authenticate-options')).json()) as { rpId: string; challenge: string }
  assert.equal(use.rpId, '127.0.0.1')
  // the library only "prefers" that the device checks who holds it; ours refuses a sign-in where it did not
  assert.throws(() => personChecked(false), /did not confirm/)
  assert.doesNotThrow(() => personChecked(true))
  assert.deepEqual(await (await call('/api/auth/passkey/list-user-passkeys', { cookie })).json(), [])
  // an answer that no device made is refused
  const forged = await post('/api/auth/passkey/verify-authentication', { response: { id: 'x', rawId: 'x', type: 'public-key', response: {}, clientExtensionResults: {} } })
  assert.notEqual(forged.status, 200)
  assert.equal(forged.headers.getSetCookie().some((c) => /session_token=[^;]/.test(c)), false)
})

test('an account with no password turns two-step sign-in on from a recent sign-in, not a stale one', async () => {
  const made = await viaProvider({ requestSignUp: true, additionalData: { adult: true } }, 'nopass')
  const cookie = made.session!
  const { user } = (await (await call('/api/me', { cookie })).json()) as { user: { id: string } }
  const on = await post('/api/auth/two-factor/enable', {}, { cookie }) // just signed in: no password to ask for
  assert.equal(on.status, 200)
  const secret = new URL(((await on.json()) as { totpURI: string }).totpURI).searchParams.get('secret')!
  const turnedOn = await post('/api/auth/two-factor/verify-totp', { code: totp(secret) }, { cookie })
  assert.equal(turnedOn.status, 200)
  const now = /session_token=[^;]/.test(cookies(turnedOn)) ? cookies(turnedOn) : cookie // turning it on may renew the session

  await pool.query(`UPDATE session SET "createdAt" = now() - interval '11 minutes' WHERE "userId" = $1`, [user.id])
  const stale = await post('/api/auth/two-factor/disable', {}, { cookie: now })
  assert.equal(stale.status, 403)
  assert.equal(((await stale.json()) as { code: string }).code, 'SESSION_NOT_FRESH')
  const keyTooLate = await call('/api/auth/passkey/generate-register-options', { cookie: now }) // the same rule, for a passkey
  assert.equal(((await keyTooLate.json()) as { code: string }).code, 'SESSION_NOT_FRESH')
})

test('a username: one per account whatever the capitals, never ours, and a way to sign in', async () => {
  for (const good of ['mira', 'tobin_77', 'abc']) assert.ok(usernameOk(good), good)
  for (const bad of ['ab', 'Mira', 'mi ra', 'm@ra', 'kataki', 'admin', 'x'.repeat(31), 'mïra']) assert.ok(!usernameOk(bad), bad)

  const { cookie } = await account('named@example.com')
  assert.notEqual((await post('/api/auth/update-user', { username: 'support' }, { cookie })).status, 200)
  assert.equal((await post('/api/auth/update-user', { username: 'Harbour_Fox' }, { cookie })).status, 200) // kept lowercase
  const other = await account('second@example.com')
  assert.notEqual((await post('/api/auth/update-user', { username: 'harbour_fox' }, { cookie: other.cookie })).status, 200) // taken

  const byName = await post('/api/auth/sign-in/username', { username: 'HARBOUR_FOX', password: PASSWORD })
  assert.equal(byName.status, 200)
  assert.equal((await call('/stories', { cookie: cookies(byName) })).status, 200)
  assert.equal((await post('/api/auth/sign-in/username', { username: 'harbour_fox', password: 'not the password' })).status, 401)
  assert.equal((await post('/api/auth/sign-in/username', { username: 'nobody_here', password: PASSWORD })).status, 401) // the same answer
  assert.equal((await call('/api/auth/is-username-available', { method: 'POST', body: JSON.stringify({ username: 'harbour_fox' }), headers: { 'content-type': 'application/json', origin } })).status, 404)
})

/** Link a computer to the signed-in account, as the desktop and the website do between them. */
async function linked(cookie: string, name = 'Study PC'): Promise<{ authorization: string }> {
  const started = (await (await post('/api/device/start', { name }, { headers: { origin: '' } })).json()) as { code: string; secret: string; url: string }
  assert.match(started.code, /^[A-Z2-9]{8}$/)
  assert.equal(started.url, `${origin}/app/?link=${started.code}`)
  assert.equal((await post('/api/device/poll', { secret: started.secret })).status, 202) // nobody has said yes
  assert.deepEqual(await (await call(`/api/device/link?code=${started.code.toLowerCase()}`, { cookie })).json(), { name })
  assert.equal((await post('/api/device/approve', { code: started.code }, { cookie })).status, 200)
  const got = (await (await post('/api/device/poll', { secret: started.secret })).json()) as { token: string }
  assert.match(got.token, /^kd_[0-9a-f]{64}$/)
  assert.equal((await post('/api/device/poll', { secret: started.secret })).status, 410) // handed over once
  return { authorization: `Bearer ${got.token}` }
}
const put = (auth: { authorization: string }, bytes: string, query: string) =>
  fetch(`${origin}/api/cloud?${query}`, { method: 'PUT', headers: auth, body: bytes })

test('cloud save: a computer is linked by its owner, and its token opens the cloud and nothing else', async () => {
  const { cookie } = await account('saver@example.com')
  assert.equal((await call('/api/cloud')).status, 401)
  assert.equal((await call('/api/device/approve', { method: 'POST', body: '{"code":"AAAAAAAA"}', headers: { 'content-type': 'application/json', origin } })).status, 401) // approving needs the account
  assert.equal((await post('/api/device/approve', { code: 'AAAAAAAA' }, { cookie })).status, 404) // and a code that is waiting
  const device = await linked(cookie)
  assert.equal((await call('/stories', { headers: device })).status, 401) // not the library, not the account
  assert.equal((await call('/api/me', { headers: device })).status, 401)
  const seenFromWeb = (await (await call('/api/devices', { cookie })).json()) as { id: string; name: string }[]
  assert.deepEqual(seenFromWeb.map((d) => d.name), ['Study PC'])
  const info = (await (await call('/api/cloud', { headers: device })).json()) as { account: string; snapshot: unknown; kept: number }
  assert.deepEqual([info.account, info.snapshot, info.kept], ['Qais', null, 5])
  assert.equal((await call('/api/cloud/download', { headers: device })).status, 404)
  // unlinked from the website: the token stops working at once
  assert.equal((await call(`/api/devices/${seenFromWeb[0].id}`, { method: 'DELETE', cookie, headers: { origin } })).status, 200)
  assert.equal((await call('/api/cloud', { headers: device })).status, 401)
})

test('cloud save: snapshots have revisions, one computer never silently overwrites another, and old ones go', async () => {
  const { cookie, id } = await account('twocomputers@example.com')
  const desk = await linked(cookie, 'Desk')
  const laptop = await linked(cookie, 'Laptop')
  const holds = encodeURIComponent(JSON.stringify({ stories: 2, characters: 3, 'not a count': 'x' }))

  const first = await put(desk, 'the library, v1', `base=0&holds=${holds}`)
  assert.equal(first.status, 200)
  const one = ((await first.json()) as { snapshot: { revision: number; bytes: number; device: string; holds: object } }).snapshot
  assert.deepEqual([one.revision, one.bytes, one.device, one.holds], [1, 15, 'Desk', { stories: 2, characters: 3 }])

  // the laptop last saw nothing: it is told what is there instead of overwriting it
  const clash = await put(laptop, 'the laptop library', 'base=0')
  assert.equal(clash.status, 409)
  assert.equal(((await clash.json()) as { snapshot: { device: string } }).snapshot.device, 'Desk')
  const got = await call('/api/cloud/download', { headers: laptop })
  assert.equal(got.headers.get('x-kataki-revision'), '1')
  assert.equal(await got.text(), 'the library, v1')
  assert.equal((await put(laptop, 'the laptop library', 'base=1')).status, 200) // built on what it downloaded
  assert.equal((await put(desk, 'the desk again', 'base=1')).status, 409) // now the desk is the one behind
  assert.equal((await put(desk, 'the desk again', 'base=1&force=1')).status, 200) // "upload and replace"

  assert.equal((await put(desk, 'x'.repeat(1001), 'base=3')).status, 413) // past the size limit: refused, nothing kept
  for (let base = 3; base < 8; base++) assert.equal((await put(desk, `v${base + 1}`, `base=${base}`)).status, 200)
  assert.deepEqual(readdirSync(join(cloudDir, id)).sort(), ['4.kataki', '5.kataki', '6.kataki', '7.kataki', '8.kataki']) // the newest five

  // the account goes: so do its snapshots and its computers
  await post('/api/account/delete', {}, { cookie })
  assert.equal(await sweep(leaving, new Date(Date.now() + (GRACE_DAYS + 1) * 86_400_000)), 1)
  assert.equal(existsSync(join(cloudDir, id)), false)
  assert.equal((await call('/api/cloud', { headers: desk })).status, 401)
})

test('cloud save past the free limit: kept while there is credit, charged once a day, never deleted', async () => {
  const { cookie, id } = await account('bigwriter@example.com')
  const device = await linked(cookie)
  const small = encodeURIComponent(JSON.stringify({ stories: 2, characters: 3 }))
  const big = encodeURIComponent(JSON.stringify({ stories: 9, characters: 3 }))
  assert.equal((await put(device, 'small', `base=0&holds=${small}`)).status, 200) // free
  const today = new Date('2026-10-03T12:00:00Z')
  assert.equal(await chargeStorage(leaving as never, today), 0) // nothing to charge inside the limit

  const bigger = await put(device, 'x'.repeat(900), `base=1&holds=${big}`)
  assert.equal(bigger.status, 200) // past the limit, but there is credit
  const info = (await (await call('/api/cloud', { headers: device })).json()) as { over: string[]; free: object; pricePerGbMonth: number }
  assert.deepEqual([info.over, info.pricePerGbMonth], [['stories'], 0.1])

  const before = await balance(pool, id)
  assert.equal(await chargeStorage({ ...leaving, ...leaving.cloud!, limits: { free: { stories: 2, characters: 3 }, microsPerGbMonth: 100_000 } } as never, today), 1)
  assert.equal(await chargeStorage({ ...leaving, ...leaving.cloud!, limits: { free: { stories: 2, characters: 3 }, microsPerGbMonth: 100_000 } } as never, today), 0) // once a day
  assert.equal(await balance(pool, id), before - 1n) // a few hundred bytes cost the smallest unit, rounded up

  // out of credit: a library past the limit is not taken; what is there stays and comes down
  await pool.query("INSERT INTO credit(user_id, micros, reason, ref) VALUES($1, $2, 'adjust', $3)", [id, (-(await balance(pool, id))).toString(), `test:${id}`])
  const refused = await put(device, 'y'.repeat(900), `base=2&holds=${big}`)
  assert.equal(refused.status, 402)
  assert.deepEqual(((await refused.json()) as { over: string[] }).over, ['stories'])
  assert.equal((await put(device, 'small again', `base=2&holds=${small}`)).status, 200) // inside the limit it is free
  assert.equal((await call('/api/cloud/download', { headers: device })).status, 200)
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
