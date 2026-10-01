// Run with: node app/src/pace.check.ts (Node 24 strips the types). Fails loudly if pacing breaks.
import assert from 'node:assert/strict'
import { paced, pacer } from './pace.ts'

let out = ''
const fast = pacer((t) => (out += t), 1000) // 40 characters a tick
fast.push('x'.repeat(100))
assert.equal(out, '', 'nothing shows before the first tick')
await fast.drain()
assert.equal(out, 'x'.repeat(100), 'all of it comes out, in order')

out = ''
const slow = pacer((t) => (out += t), 25) // one character a tick
slow.push('hello world')
await new Promise((r) => setTimeout(r, 130))
assert.ok(out.length > 0 && out.length < 11, `paced, not dumped (got ${out.length})`)
slow.flush()
assert.equal(out, 'hello world', 'Stop shows the rest at once')
await slow.drain() // already settled: resolves at once

out = ''
pacer((t) => (out += t), Infinity).push('now')
assert.equal(out, 'now', 'instant shows text as it arrives')

// a text reply's bubbles: the model's own time comes off the front; each still types a moment
const plan = [{ delay_ms: 2000, typing_ms: 3000 }, { delay_ms: 500, typing_ms: 1000 }]
assert.deepEqual(paced(plan, 0), [{ pause: 2000, typing: 3000 }, { pause: 500, typing: 1000 }])
assert.deepEqual(paced(plan, 2500), [{ pause: 0, typing: 2500 }, { pause: 500, typing: 1000 }])
assert.deepEqual(paced(plan, 120_000), [{ pause: 0, typing: 400 }, { pause: 0, typing: 400 }], 'a slow reply adds no pretend typing')
assert.deepEqual(paced([{ delay_ms: 0, typing_ms: 0 }], 900), [{ pause: 0, typing: 0 }], 'the dial off stays instant')
console.log('pace ok')
