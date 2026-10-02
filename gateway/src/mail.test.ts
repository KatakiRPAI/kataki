import assert from 'node:assert/strict'
import { test } from 'node:test'
import { mailer, printed } from './mail.ts'

test('with no key, mail is printed', () => {
  assert.equal(mailer({}), printed)
})

test('a key without a sender is a setup mistake, said at start', () => {
  assert.throws(() => mailer({ RESEND_API_KEY: 're_x' }), /KATAKI_MAIL_FROM/)
})

test('with a key, one POST to Resend carries the mail', async () => {
  const sent: { url: string; init: RequestInit }[] = []
  const send = mailer({ RESEND_API_KEY: 're_x', KATAKI_MAIL_FROM: 'Kataki <hello@kataki.test>' }, (async (url: string, init: RequestInit) => {
    sent.push({ url, init })
    return new Response('{}', { status: 200 })
  }) as typeof fetch)
  await send('qais@example.com', 'Confirm your email', 'Open this link')
  assert.equal(sent.length, 1)
  assert.equal(sent[0].url, 'https://api.resend.com/emails')
  assert.equal((sent[0].init.headers as Record<string, string>).Authorization, 'Bearer re_x')
  assert.deepEqual(JSON.parse(String(sent[0].init.body)), { from: 'Kataki <hello@kataki.test>', to: ['qais@example.com'], subject: 'Confirm your email', text: 'Open this link' })
})

test('a mail that fails does not take the request down with it', async () => {
  const send = mailer({ RESEND_API_KEY: 're_x', KATAKI_MAIL_FROM: 'k@kataki.test' }, (async () => { throw new TypeError('network down') }) as typeof fetch)
  await send('qais@example.com', 'x', 'y') // resolves: logged, not thrown
  const refused = mailer({ RESEND_API_KEY: 're_x', KATAKI_MAIL_FROM: 'k@kataki.test' }, (async () => new Response('', { status: 422 })) as typeof fetch)
  await refused('qais@example.com', 'x', 'y')
})
