// The gateway bills and signs exactly as the engine does: both are held to the engine's
// vectors (engine/tests/test_gateway_vectors.py is the other half).
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { micros, type Prices, type Tokens } from './money.ts'
import { sign, signed, USER } from './sign.ts'

const V = JSON.parse(readFileSync(new URL('../../engine/tests/gateway_vectors.json', import.meta.url), 'utf8')) as {
  prices: Prices
  money: { row: Tokens; micros: number | null }[]
  sign: { secret: string; user: string; channel: string; at: number; method: string; target: string; sig: string }[]
}

test('micros match the engine, case by case', () => {
  for (const { row, micros: want } of V.money) {
    const got = micros(V.prices, row)
    assert.equal(got === null ? null : Number(got), want, JSON.stringify(row))
  }
})

test('a count that is not a whole number prices nothing', () => {
  assert.equal(micros(V.prices, { model: 'rp-1', role: 'rp', prompt_tokens: 1.5 }), null)
  assert.equal(micros(V.prices, { model: 'rp-1', role: 'rp', prompt_tokens: -1 }), null)
})

test('signatures match the engine', () => {
  for (const v of V.sign) assert.equal(sign(v.secret, v.user, v.channel, v.at, v.method, v.target), v.sig)
})

test('the signed target always has its question mark', () => {
  const v = V.sign[0]
  const h = signed(v.secret, v.user, v.channel, v.method, '/stories', v.at * 1000)
  assert.equal(h['x-kataki-sig'], v.sig)
  const q = signed(V.sign[1].secret, V.sign[1].user, V.sign[1].channel, 'POST', '/stories/1/turn?x=1&y=%20z', 1000)
  assert.equal(q['x-kataki-sig'], V.sign[1].sig)
})

test('only ids that can name a library folder pass', () => {
  assert.ok(USER.test('2f1641eb-4813-484e-b5e3-60218e1af6fc'))
  for (const bad of ['', 'Alice', 'con', 'a/b', '..', 'x'.repeat(65)]) assert.ok(!USER.test(bad), bad)
})
